from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
import sys

def get_gemini_llm():
    if not settings.GOOGLE_API_KEY:
        print("Erro: A chave GOOGLE_API_KEY não foi configurada.")
        print("Por favor, adicione-a ao seu arquivo .env")
        sys.exit(1) 

    try:
        # Atualizado para o modelo Gemini 3.1 Flash
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0
        )
        print(f"Modelo {llm.model} inicializado com sucesso.")
        return llm
    except Exception as e:
        print(f"Erro ao inicializar o modelo Gemini: {e}")
        sys.exit(1)