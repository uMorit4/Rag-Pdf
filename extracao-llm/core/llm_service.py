from langchain_google_genai import ChatGoogleGenerativeAI
from google import genai
from config import settings
import sys

def get_gemini_clients():
    """Retorna o cliente de arquivos do Google e o LLM do LangChain."""
    if not settings.GOOGLE_API_KEY:
        print("Erro: A chave GOOGLE_API_KEY não foi configurada.")
        sys.exit(1) 

    try:

        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0
        )
        print(f"Modelo utilizado: {llm.model}")
        return client, llm
    except Exception as e:
        print(f"Erro ao inicializar clientes Gemini: {e}")
        sys.exit(1)