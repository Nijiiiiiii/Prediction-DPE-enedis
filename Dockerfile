
FROM python:3.13-slim

# Répertoire de travail
WORKDIR /app

# Éviter les fichiers .pyc et activer les logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'ensemble du projet
COPY . .

# Port Streamlit
EXPOSE 8501

# Lancement de l'application
CMD ["sh", "-c", "streamlit run app/1_📖_Contexte.py --server.address=0.0.0.0 --server.port=${PORT:-8501}"]
