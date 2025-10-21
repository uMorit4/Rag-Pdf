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

# --- Configuração ---
NOME_PDF_ENTRADA = "NVIDIA 2025 Annual Report.pdf" 
NOME_CSV_SAIDA = "dados_extraidos.csv"
TAMANHO_DO_CHUNK_PAGINAS = 40 

# --- NOVA CONFIGURAÇÃO DE BUSCA ---

# Defina o CONTEXTO onde o LLM deve procurar.
# Ex: "Proposal for Election of Directors"
# Se não quiser um contexto (comportamento antigo), defina como None
CONTEXTO_DA_BUSCA = "Election of Directors"

# Defina os campos que você quer extrair DE DENTRO desse contexto.
CAMPOS_PARA_EXTRAIR = [
    "board_recomendation_name",
    "age",
    "director_since"

]

# ------------------------------------


# --- FUNÇÃO AUXILIAR ---
def criar_chunks_de_documento(documentos: List[Document], tamanho_chunk: int) -> List[List[Document]]:
    """Divide a lista de documentos (páginas) em chunks de tamanho fixo."""
    chunks = []
    for i in range(0, len(documentos), tamanho_chunk):
        chunk = documentos[i:i + tamanho_chunk]
        chunks.append(chunk)
    print(f"[Chunker] Documento dividido em {len(chunks)} chunks de até {tamanho_chunk} páginas cada.")
    return chunks

def executar_pipeline():
    print("--- Iniciando Pipeline de Extração ---")

    # 1. Definir caminhos completos
    caminho_pdf = os.path.join(DIRETORIO_DO_SCRIPT, NOME_PDF_ENTRADA)
    caminho_csv = os.path.join(DIRETORIO_DO_SCRIPT, NOME_CSV_SAIDA)

    # 2. Carregar o PDF
    print(f"\n[Passo 1: Carregando PDF]")
    print(f"Procurando PDF em: {caminho_pdf}")
    documentos_completos = carregar_pdf(caminho_pdf)
    
    if not documentos_completos:
        print("Falha ao carregar PDF. Abortando.")
        return

    print(f"PDF carregado. Total de páginas: {len(documentos_completos)}")

    # 3. Dividir o documento em Chunks
    print(f"\n[Passo 2: Dividindo Documento em Chunks]")
    chunks = criar_chunks_de_documento(documentos_completos, TAMANHO_DO_CHUNK_PAGINAS)

    # 4. Extrair dados de cada chunk
    print(f"\n[Passo 3: Processando Chunks com LLM]")
    
    todos_os_dados_extraidos = [] 

    for i, chunk in enumerate(chunks):
        print(f"\n--- Processando Chunk {i + 1} / {len(chunks)} ---")
        
        # --- CHAMADA ATUALIZADA ---
        # Agora passamos o CONTEXTO_DA_BUSCA para a função
        dados_extraidos_do_chunk = extrair_dados_estruturados(
            chunk, 
            CAMPOS_PARA_EXTRAIR, 
            CONTEXTO_DA_BUSCA  # <-- Passando o novo parâmetro
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

    # 5. Salvar TODOS os dados em CSV
    print("\n[Passo 4: Salvando em CSV]")
    if not todos_os_dados_extraidos:
        print("Nenhum dado foi extraído de nenhum chunk. O arquivo CSV não será criado.")
    else:
        salvar_para_csv(todos_os_dados_extraidos, caminho_csv)
        print(f"Total de {len(todos_os_dados_extraidos)} itens salvos em '{NOME_CSV_SAIDA}'")
    
    print("\n--- Pipeline Concluído ---")

if __name__ == "__main__":
    executar_pipeline()