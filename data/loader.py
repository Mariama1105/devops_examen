import seaborn as sns
import pandas as pd

def load_data():
    df = sns.load_dataset('titanic')

    # Nettoyage
    df['age'] = df['age'].fillna(df['age'].median())

    df['embarked'] = df['embarked'].fillna('Unknown')

    # 🔥 Correction ici
    if df['deck'].dtype.name == 'category':
        df['deck'] = df['deck'].cat.add_categories(['Unknown'])

    df['deck'] = df['deck'].fillna('Unknown')

    return df