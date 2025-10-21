import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Recupera a API Key. Retorna None se não for encontrada.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Atenção: GOOGLE_API_KEY não encontrada no .env")