import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging
import json
import os
import numpy as np
from data.loader import load_data
from streamlit_option_menu import option_menu
import plotly.figure_factory as ff
import requests
from datetime import datetime

# Configuration de la page (doit être la première commande Streamlit)
st.set_page_config(
    page_title="Titanic Dashboard",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS pour un design moderne
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    .main-header h1 { color: white; margin: 0; font-size: 2.5rem; font-weight: 700; }
    .main-header p { color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem; }
    
    .kpi-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border-top: 4px solid;
    }
    .kpi-card:hover { transform: translateY(-5px); box-shadow: 0 8px 30px rgba(0,0,0,0.15); }
    .kpi-value { font-size: 2.5rem; font-weight: 800; margin: 0.5rem 0; }
    .kpi-label { font-size: 0.9rem; color: #666; text-transform: uppercase; letter-spacing: 1px; }
    
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%); padding: 1rem; }
    .chart-card { background: white; padding: 1rem; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 1rem; }
    
    .footer {
        text-align: center;
        padding: 2rem;
        color: #888;
        font-size: 0.8rem;
        border-top: 1px solid #eee;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Custom JSON encoder for numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)

# Créer le dossier logs s'il n'existe pas
os.makedirs("logs", exist_ok=True)

# Configuration du logger
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format='%(message)s'
)

# URL d'Elasticsearch
ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_HOST', 'http://elasticsearch:9200')

def log_event(event):
    """Log event to both file and Elasticsearch directly"""
    try:
        # Ajouter un timestamp si absent
        if 'timestamp' not in event:
            event['timestamp'] = datetime.now().isoformat()
        
        # 1. Écrire dans le fichier local
        event_json = json.dumps(event, cls=NumpyEncoder, ensure_ascii=False)
        logging.info(event_json)
        
        # 2. Envoyer directement à Elasticsearch via HTTP
        try:
            response = requests.post(
                f"{ELASTICSEARCH_URL}/titanic-logs/_doc",
                json=event,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            if response.status_code not in [200, 201]:
                print(f"⚠️ Elasticsearch error: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Could not reach Elasticsearch: {e}")
            
    except Exception as e:
        print(f"❌ Error logging: {e}")

# Charger data
df = load_data()

# ============================================
# SIDEBAR FILTRES (commun à toutes les pages)
# ============================================
with st.sidebar:
    st.markdown("### 🎛️ **Filtres**")
    st.markdown("---")
    
    sex_options = ["all"] + list(df['sex'].unique())
    sex_icons = {"all": "👥", "male": "👨", "female": "👩"}
    sex = st.selectbox(
        "🚻 **Sexe**", 
        sex_options,
        format_func=lambda x: f"{sex_icons.get(x, '')} {x.capitalize() if x != 'all' else 'Tous'}"
    )
    
    class_options = ["all"] + sorted(list(df['pclass'].unique()))
    pclass = st.selectbox(
        "🏠 **Classe**",
        class_options,
        format_func=lambda x: "🌟 Toutes" if x == "all" else f"Classe {x}"
    )
    
    st.markdown("---")
    st.markdown("### ℹ️ **Informations**")
    st.caption("📊 Données du Titanic (891 passagers)")
    st.caption("🎨 Dashboard interactif")

# Filtrage des données
filtered_df = df.copy()
if sex != "all":
    filtered_df = filtered_df[filtered_df['sex'] == sex]
if pclass != "all":
    filtered_df = filtered_df[filtered_df['pclass'] == pclass]

# Log filter event
log_event({
    "event": "filter_applied",
    "sex": str(sex),
    "class": str(pclass),
    "passengers_count": int(len(filtered_df))
})

# ============================================
# NAVIGATION - MENU DES 4 PAGES
# ============================================
st.markdown('<div class="main-header"><h1>🚢 Titanic Dashboard</h1><p>Analyse interactive des données du Titanic | Projet DevOps</p></div>', unsafe_allow_html=True)

selected = option_menu(
    menu_title=None,
    options=["🏠 Accueil", "📊 Analyse de survie", "👥 Profil des passagers", "📄 Données brutes"],
    icons=["house", "graph-up", "people", "table"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#fafafa", "border-radius": "15px", "margin-bottom": "2rem"},
        "icon": {"color": "#667eea", "font-size": "1.2rem"},
        "nav-link": {
            "font-size": "1rem",
            "text-align": "center",
            "margin": "0px",
            "padding": "0.8rem 1.5rem",
            "color": "#555",
            "font-weight": "500",
            "border-radius": "10px",
        },
        "nav-link-selected": {
            "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "color": "white",
        },
    },
)

# Calcul des KPIs communs
survival_rate = float(filtered_df['survived'].mean()) if len(filtered_df) > 0 else 0.0
avg_age = float(filtered_df['age'].mean()) if len(filtered_df) > 0 else 0.0
avg_fare = float(filtered_df['fare'].mean()) if len(filtered_df) > 0 else 0.0

# ============================================
# PAGE 1 : ACCUEIL - VUE GÉNÉRALE
# ============================================
if selected == "🏠 Accueil":
    log_event({"event": "page_view", "page": "home"})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card" style="border-top-color: #667eea;">
            <div class="kpi-label">👥 Passagers</div>
            <div class="kpi-value" style="color: #667eea;">{len(filtered_df)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-card" style="border-top-color: #28a745;">
            <div class="kpi-label">❤️ Taux de survie</div>
            <div class="kpi-value" style="color: #28a745;">{survival_rate:.1%}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="kpi-card" style="border-top-color: #17a2b8;">
            <div class="kpi-label">📅 Âge moyen</div>
            <div class="kpi-value" style="color: #17a2b8;">{avg_age:.1f} ans</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="kpi-card" style="border-top-color: #ffc107;">
            <div class="kpi-label">💰 Tarif moyen</div>
            <div class="kpi-value" style="color: #ffc107;">${avg_fare:.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.subheader("📊 Survie par sexe")
        survival_by_sex = filtered_df.groupby('sex')['survived'].mean().reset_index()
        fig = px.bar(survival_by_sex, x='sex', y='survived', 
                     color='sex', color_discrete_map={'male': '#667eea', 'female': '#f093fb'},
                     text_auto='.0%', height=400)
        fig.update_layout(showlegend=False, plot_bgcolor='white', title_font_size=16)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.subheader("🍰 Répartition par classe")
        class_dist = filtered_df['pclass'].value_counts().reset_index()
        class_dist.columns = ['pclass', 'count']
        fig = px.pie(class_dist, values='count', names='pclass', 
                     color_discrete_sequence=px.colors.sequential.Purples_r,
                     hole=0.4, height=400)
        fig.update_layout(title_font_size=16)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.subheader("📈 Distribution des âges")
    fig = px.histogram(filtered_df, x='age', nbins=30, 
                       color_discrete_sequence=['#764ba2'],
                       marginal='box', opacity=0.8, height=450)
    fig.update_layout(plot_bgcolor='white', title_font_size=16)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# PAGE 2 : ANALYSE DE SURVIE
# ============================================
elif selected == "📊 Analyse de survie":
    log_event({"event": "page_view", "page": "survival_analysis"})
    
    st.markdown("## 🔬 **Analyse approfondie de la survie**")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    n_survived = filtered_df[filtered_df['survived'] == 1].shape[0] if len(filtered_df) > 0 else 0
    n_deceased = filtered_df[filtered_df['survived'] == 0].shape[0] if len(filtered_df) > 0 else 0
    
    with col1:
        st.metric("✅ Survivants", n_survived)
    with col2:
        st.metric("❌ Décédés", n_deceased)
    with col3:
        st.metric("📊 Ratio survie", f"{survival_rate:.1%}")
    
    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("🎯 Survie par sexe")
        survival_by_sex = filtered_df.groupby('sex')['survived'].agg(['mean', 'count']).reset_index()
        survival_by_sex.columns = ['sex', 'survival_rate', 'count']
        male_rate = survival_by_sex[survival_by_sex['sex']=='male']['survival_rate'].values[0] if len(survival_by_sex[survival_by_sex['sex']=='male']) > 0 else 0
        female_rate = survival_by_sex[survival_by_sex['sex']=='female']['survival_rate'].values[0] if len(survival_by_sex[survival_by_sex['sex']=='female']) > 0 else 0
        fig = go.Figure(data=[
            go.Bar(name='Hommes', x=['Hommes'], y=[male_rate], marker_color='#667eea'),
            go.Bar(name='Femmes', x=['Femmes'], y=[female_rate], marker_color='#f093fb')
        ])
        fig.update_layout(title='Taux de survie par sexe', yaxis_title='Taux de survie', yaxis_tickformat='.0%', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.subheader("🎯 Survie par classe")
        survival_by_class = filtered_df.groupby('pclass')['survived'].mean().reset_index()
        fig = px.bar(survival_by_class, x='pclass', y='survived', 
                     color='survived', color_continuous_scale='RdYlGn',
                     labels={'pclass': 'Classe', 'survived': 'Taux de survie'},
                     text_auto='.0%', height=400)
        fig.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("📈 Impact de l'âge sur la survie")
    fig = px.histogram(filtered_df, x='age', color='survived', 
                       nbins=40, barmode='overlay',
                       color_discrete_map={0: '#dc3545', 1: '#28a745'},
                       labels={'survived': 'Survécu', 'age': 'Âge'},
                       opacity=0.7, height=450)
    fig.update_layout(legend_title_text='Statut')
    st.plotly_chart(fig, use_container_width=True)

# ============================================
# PAGE 3 : PROFIL DES PASSAGERS
# ============================================
elif selected == "👥 Profil des passagers":
    log_event({"event": "page_view", "page": "passenger_profile"})
    
    st.markdown("## 👤 **Analyse démographique des passagers**")
    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Distribution des âges")
        fig = go.Figure()
        survived_ages = filtered_df[filtered_df['survived']==1]['age'].dropna()
        deceased_ages = filtered_df[filtered_df['survived']==0]['age'].dropna()
        fig.add_trace(go.Histogram(x=survived_ages, name='Survivants', marker_color='#28a745', opacity=0.7))
        fig.add_trace(go.Histogram(x=deceased_ages, name='Décédés', marker_color='#dc3545', opacity=0.7))
        fig.update_layout(barmode='overlay', title='Distribution des âges par statut', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.subheader("💰 Distribution des tarifs")
        fig = px.box(filtered_df, x='pclass', y='fare', color='pclass',
                     color_discrete_sequence=px.colors.sequential.Purples_r,
                     labels={'pclass': 'Classe', 'fare': 'Tarif ($)'},
                     title='Tarifs par classe', height=400)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("📊 Statistiques démographiques")
    stats = filtered_df.agg({
        'age': ['mean', 'median', 'min', 'max'],
        'fare': ['mean', 'median', 'min', 'max'],
        'sibsp': ['mean', 'sum'],
        'parch': ['mean', 'sum']
    }).round(2)
    stats.columns = ['Âge', 'Tarif', 'Famille (sibsp)', 'Parents (parch)']
    st.dataframe(stats, use_container_width=True)

# ============================================
# PAGE 4 : DONNÉES BRUTES
# ============================================
elif selected == "📄 Données brutes":
    log_event({"event": "page_view", "page": "raw_data"})
    
    st.markdown("## 📋 **Données complètes du Titanic**")
    st.markdown("---")
    
    rows_per_page = st.selectbox("📄 Lignes par page", [10, 25, 50, 100], index=0)
    total_rows = len(filtered_df)
    total_pages = (total_rows - 1) // rows_per_page + 1 if total_rows > 0 else 1
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
    
    start_idx = (page_number - 1) * rows_per_page
    end_idx = min(start_idx + rows_per_page, total_rows)
    
    st.markdown(f"**Affichage des lignes {start_idx + 1} à {end_idx} sur {total_rows}**")
    st.dataframe(filtered_df.iloc[start_idx:end_idx], use_container_width=True, height=400)
    
    st.markdown("---")
    
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger les données (CSV)",
        data=csv,
        file_name="titanic_data.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    with st.expander("📊 Aperçu des colonnes disponibles"):
        col_info = pd.DataFrame({
            'Colonne': filtered_df.columns,
            'Type': filtered_df.dtypes.values,
            'Valeurs non-nulles': filtered_df.count().values,
            'Valeurs uniques': [filtered_df[col].nunique() for col in filtered_df.columns]
        })
        st.dataframe(col_info, use_container_width=True)

# ============================================
# FOOTER
# ============================================
st.markdown("""
<div class="footer">
    <p>🚢 Titanic Dashboard - Projet DevOps | Données historiques du Titanic | 
    <a href="#" style="color: #667eea;">GitHub</a> | 
    <a href="#" style="color: #667eea;">Documentation</a></p>
</div>
""", unsafe_allow_html=True)