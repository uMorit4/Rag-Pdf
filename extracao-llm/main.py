import os
import sys 
import time

# --- Adicionar o caminho do projeto ao path ---
DIRETORIO_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIRETORIO_DO_SCRIPT)
# -------------------------------------------------

from typing import List
from langchain_core.documents import Document
from utils.pdf_parser import carregar_pdf
from core.extractor import extrair_dados_estruturados
from utils.csv_writer import salvar_para_csv
from core.llm_service import get_gemini_llm  

# --- Configuração ---
NOME_PDF_ENTRADA = "FS.pdf"
NOME_CSV_SAIDA = "dados_extraidos.csv"

GEMINI_MAX_INPUT_TOKENS = 1_000_000

FRACAO_MAX_CHUNK = 0.85
MAX_TOKENS_POR_CHUNK = int(GEMINI_MAX_INPUT_TOKENS * FRACAO_MAX_CHUNK)

CAMPOS_PARA_EXTRAIR = {
        "Data": "Extraia a data da coluna ou cabeçalho correspondente. Todas as datas disponíveis, incluindo períodos de tempo como YoY e similares",
        "Current Assets": "Extraia o nome de cada um dos Current Assets, em texto.",
        "USD": "Valor em dólar desses Assets, com separador como vírgula.",
        "NTD": "Valor em NTD desses Assets, com separador como vírgula.",
        "%": "Percentual de representatividade desses current assets em relação ao todo, utilizando ponto como separador."
}

def criar_chunks_de_documento(documentos: List[Document]) -> List[List[Document]]:
    """
    Divide a lista de páginas em chunks, garantindo que o TEXTO que será enviado
    para o LLM em cada chamada fique abaixo de MAX_TOKENS_POR_CHUNK.

    A contagem de tokens usa o tokenizer oficial do Gemini via get_num_tokens.
    """
    if not documentos:
        return []

    llm = get_gemini_llm()

    chunks: List[List[Document]] = []
    chunk_atual: List[Document] = []
    texto_atual = ""  
    separador = "\n\n--- Pág ---\n\n"

    def conta_tokens(texto: str) -> int:
        try:
            return llm.get_num_tokens(texto)
        except Exception as e:
            print(f"[Chunker] Falha em get_num_tokens, usando aproximação. Erro: {e}")
            return max(1, len(texto) // 4)

    for idx, doc in enumerate(documentos):
        pagina_texto = doc.page_content or ""

        if not chunk_atual:
            texto_candidato = pagina_texto
        else:
            texto_candidato = texto_atual + separador + pagina_texto

        tokens_candidato = conta_tokens(texto_candidato)

        if tokens_candidato > MAX_TOKENS_POR_CHUNK and chunk_atual:
            print(
                f"[Chunker] Fechando chunk {len(chunks) + 1} "
                f"com ~{conta_tokens(texto_atual)} tokens e {len(chunk_atual)} páginas."
            )
            chunks.append(chunk_atual)
            chunk_atual = [doc]
            texto_atual = pagina_texto  
        else:
            chunk_atual.append(doc)
            texto_atual = texto_candidato

    if chunk_atual:
        print(
            f"[Chunker] Fechando chunk {len(chunks) + 1} "
            f"com ~{conta_tokens(texto_atual)} tokens e {len(chunk_atual)} páginas."
        )
        chunks.append(chunk_atual)

    print(
        f"[Chunker] Documento dividido em {len(chunks)} chunks "
        f"com limite de ~{MAX_TOKENS_POR_CHUNK} tokens de contexto por chunk."
    )
    return chunks


def executar_pipeline():
    print("--- Iniciando Pipeline de Extração ---")

    caminho_pdf = os.path.join(DIRETORIO_DO_SCRIPT, NOME_PDF_ENTRADA)
    caminho_csv = os.path.join(DIRETORIO_DO_SCRIPT, NOME_CSV_SAIDA)

    print(f"\n[Passo 1: Carregando PDF]")
    print(f"Procurando PDF em: {caminho_pdf}")
    documentos_completos = carregar_pdf(caminho_pdf)
    
    if not documentos_completos:
        print("Falha ao carregar PDF. Abortando.")
        return

    print(f"PDF carregado. Total de páginas: {len(documentos_completos)}")

    print(f"\n[Passo 2: Dividindo Documento em Chunks]")
    chunks = criar_chunks_de_documento(documentos_completos)

    print(f"\n[Passo 3: Processando Chunks com LLM]")
    
    todos_os_dados_extraidos = [] 

    for i, chunk in enumerate(chunks):
        print(f"\n--- Processando Chunk {i + 1} / {len(chunks)} ---")

        dados_extraidos_do_chunk = extrair_dados_estruturados(
            chunk, 
            CAMPOS_PARA_EXTRAIR, 
        )
        # ---------------------------
        
        if dados_extraidos_do_chunk:
            todos_os_dados_extraidos.extend(dados_extraidos_do_chunk)
            print(f"Chunk {i + 1} processado. {len(dados_extraidos_do_chunk)} novos itens encontrados.")
        else:
            print(f"Chunk {i + 1} processado. Nenhum item encontrado.")

        if i < len(chunks) - 1: 
            print("Aguardando 2 segundos para evitar limite de quota...")
            time.sleep(2) 

    print("\n[Passo 4: Salvando em CSV]")
    if not todos_os_dados_extraidos:
        print("Nenhum dado foi extraído de nenhum chunk. O arquivo CSV não será criado.")
    else:
        salvar_para_csv(todos_os_dados_extraidos, caminho_csv)
        print(f"Total de {len(todos_os_dados_extraidos)} itens salvos em '{NOME_CSV_SAIDA}'")
    
    print("\n--- Pipeline Concluído ---")

if __name__ == "__main__":
    executar_pipeline()