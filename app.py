import streamlit as st
import pandas as pd
import plotly.express as px
import logging
import json
from data.loader import load_data

# Logger JSON
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format='%(message)s'
)

def log_event(event):
    logging.info(json.dumps(event))

# Charger data
df = load_data()

st.title("🚢 Titanic Dashboard - DevOps Project")

# Sidebar
st.sidebar.header("Filtres")
sex = st.sidebar.selectbox("Sexe", ["all"] + list(df['sex'].unique()))
pclass = st.sidebar.selectbox("Classe", ["all"] + list(df['pclass'].unique()))

# Filtrage
filtered_df = df.copy()

if sex != "all":
    filtered_df = filtered_df[filtered_df['sex'] == sex]

if pclass != "all":
    filtered_df = filtered_df[filtered_df['pclass'] == pclass]

log_event({"event": "filter", "sex": sex, "class": pclass})

# KPI
st.subheader("📊 KPIs")
col1, col2, col3 = st.columns(3)

col1.metric("Passengers", len(filtered_df))
col2.metric("Survival Rate", f"{filtered_df['survived'].mean():.2f}")
col3.metric("Average Age", f"{filtered_df['age'].mean():.1f}")

# Graphs
st.subheader("📈 Analyse")

fig1 = px.bar(filtered_df, x="sex", y="survived", title="Survie par sexe")
st.plotly_chart(fig1)

fig2 = px.pie(filtered_df, names="pclass", title="Répartition par classe")
st.plotly_chart(fig2)

fig3 = px.histogram(filtered_df, x="age", nbins=30)
st.plotly_chart(fig3)

# Data
st.subheader("📄 Données")
st.dataframe(filtered_df)

csv = filtered_df.to_csv(index=False)
st.download_button("Download CSV", csv)

log_event({"event": "page_view"})