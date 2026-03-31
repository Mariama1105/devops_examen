FROM python:3.11-slim

# Dossier de travail
WORKDIR /app

# Copier dépendances
COPY requirements.txt .

# Installer dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le projet
COPY . .

# Port Streamlit
EXPOSE 8501

# Commande de lancement
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]