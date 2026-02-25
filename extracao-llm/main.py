import os
import sys 
import time
import json
import argparse

# --- Configuração de Caminhos ---
DIRETORIO_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_DO_SCRIPT) # Sobe um nível para a raiz geral
sys.path.insert(0, DIRETORIO_DO_SCRIPT)
# -------------------------------------------------

from typing import List
from langchain_core.documents import Document
from utils.pdf_parser import carregar_pdf
from core.extractor import extrair_dados_estruturados
from utils.csv_writer import salvar_para_csv
from core.llm_service import get_gemini_llm  

# Limites do modelo
GEMINI_MAX_INPUT_TOKENS = 1_000_000
FRACAO_MAX_CHUNK = 0.85
MAX_TOKENS_POR_CHUNK = int(GEMINI_MAX_INPUT_TOKENS * FRACAO_MAX_CHUNK)

def criar_chunks_de_documento(documentos: List[Document]) -> List[List[Document]]:
    # ... [O conteúdo desta função permanece EXATAMENTE igual ao seu original] ...
    if not documentos: return []
    llm = get_gemini_llm()
    chunks: List[List[Document]] = []
    chunk_atual: List[Document] = []
    texto_atual = ""  
    separador = "\n\n--- Pág ---\n\n"

    def conta_tokens(texto: str) -> int:
        try:
            return llm.get_num_tokens(texto)
        except Exception as e:
            return max(1, len(texto) // 4)

    for doc in documentos:
        pagina_texto = doc.page_content or ""
        texto_candidato = pagina_texto if not chunk_atual else texto_atual + separador + pagina_texto
        tokens_candidato = conta_tokens(texto_candidato)

        if tokens_candidato > MAX_TOKENS_POR_CHUNK and chunk_atual:
            chunks.append(chunk_atual)
            chunk_atual = [doc]
            texto_atual = pagina_texto  
        else:
            chunk_atual.append(doc)
            texto_atual = texto_candidato

    if chunk_atual:
        chunks.append(chunk_atual)
    return chunks

def executar_pipeline(nome_json_config: str):
    print(f"--- Iniciando Pipeline de Extração com JSON: {nome_json_config} ---")

    # Mapeando os diretórios da nova arquitetura
    caminho_configs = os.path.join(DIRETORIO_RAIZ, "inputs", "configs_jsons")
    caminho_pdfs = os.path.join(DIRETORIO_RAIZ, "inputs", "pdfs")
    caminho_arquivo_json = os.path.join(caminho_configs, nome_json_config)

    # 1. Carregando as Regras (JSON)
    if not os.path.exists(caminho_arquivo_json):
        print(f"Erro: Arquivo JSON não encontrado no caminho: {caminho_arquivo_json}")
        return

    with open(caminho_arquivo_json, 'r', encoding='utf-8') as f:
        config = json.load(f)

    arquivos_pdf = config.get("metadata", {}).get("files", [])
    
    if not arquivos_pdf:
        print("Aviso: Nenhum PDF especificado na chave 'files' do JSON. Encerrando.")
        return

    # 2. Processando cada PDF definido no JSON
    for nome_pdf in arquivos_pdf:
        print(f"\n==================================================")
        print(f"Processando arquivo alvo: {nome_pdf}")
        print(f"==================================================")
        
        caminho_pdf = os.path.join(caminho_pdfs, nome_pdf)
        
        caminho_outputs = os.path.join(DIRETORIO_RAIZ, "outputs")
        nome_csv_saida = os.path.join(caminho_outputs, f"dados_extraidos_{nome_pdf.replace('.pdf', '')}.csv")

        print(f"\n[Passo 1: Carregando PDF]")
        documentos_completos = carregar_pdf(caminho_pdf)
        
        if not documentos_completos:
            print(f"Falha ao carregar {nome_pdf}. Pulando para o próximo...")
            continue

        print(f"\n[Passo 2: Dividindo Documento em Chunks]")
        chunks = criar_chunks_de_documento(documentos_completos)

        print(f"\n[Passo 3: Processando Chunks com LLM]")
        todos_os_dados_extraidos = [] 

        for i, chunk in enumerate(chunks):
            print(f"\n--- Processando Chunk {i + 1} / {len(chunks)} ---")

            # Agora passamos o config_json inteiro em vez do antigo dicionário engessado
            dados_extraidos_do_chunk = extrair_dados_estruturados(chunk, config)
            
            if dados_extraidos_do_chunk:
                todos_os_dados_extraidos.extend(dados_extraidos_do_chunk)
                print(f"Chunk {i + 1} processado. {len(dados_extraidos_do_chunk)} itens encontrados.")
            else:
                print(f"Chunk {i + 1} processado. Nenhum item encontrado.")

            if i < len(chunks) - 1: 
                print("Aguardando 2 segundos para evitar limite de quota...")
                time.sleep(2) 

        print(f"\n[Passo 4: Salvando em CSV - {nome_pdf}]")
        if not todos_os_dados_extraidos:
            print(f"Nenhum dado extraído de {nome_pdf}. O CSV não será criado.")
        else:
            salvar_para_csv(todos_os_dados_extraidos, nome_csv_saida)
            print(f"CSV criado: '{nome_csv_saida}'")
    
    print("\n--- Pipeline Concluído ---")

if __name__ == "__main__":
    # Permite passar o nome do arquivo JSON pelo terminal
    parser = argparse.ArgumentParser(description="Pipeline Genérico de Extração de Dados via LLM")
    parser.add_argument(
        "config_json", 
        type=str, 
        help="Nome do arquivo JSON de configuração (ex: config_fs.json)"
    )
    args = parser.parse_args()
    
    executar_pipeline(args.config_json)