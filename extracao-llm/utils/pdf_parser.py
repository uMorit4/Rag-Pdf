from langchain_community.document_loaders import PyPDFLoader
from typing import List

def carregar_pdf(caminho_arquivo: str) -> List:
    """
    Carrega um arquivo PDF e retorna uma lista de Documentos (páginas).
    
    Args:
        caminho_arquivo: O caminho para o arquivo PDF.

    Returns:
        Uma lista de objetos Document do LangChain, onde cada objeto representa uma página.
    """
    print(f"Carregando PDF de: {caminho_arquivo}")
    try:
        # PyPDFLoader carrega o PDF e já o divide por páginas
        loader = PyPDFLoader(caminho_arquivo)
        paginas = loader.load()
        print(f"PDF carregado com sucesso. Número de páginas: {len(paginas)}")
        return paginas
    except Exception as e:
        print(f"Erro ao carregar o PDF: {e}")
        return []