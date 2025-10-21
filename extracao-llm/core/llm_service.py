from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings # Importa nossas configurações
import sys

def get_gemini_llm():
    """
    Inicializa e retorna o modelo LLM do Gemini.
    """
    if not settings.GOOGLE_API_KEY:
        print("Erro: A chave GOOGLE_API_KEY não foi configurada.")
        print("Por favor, adicione-a ao seu arquivo .env")
        sys.exit(1) # Para a execução se a chave não estiver presente

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0 # Queremos respostas factuais e consistentes
        )
        print("Modelo Gemini inicializado com sucesso.")
        return llm
    except Exception as e:
        print(f"Erro ao inicializar o modelo Gemini: {e}")
        sys.exit(1)