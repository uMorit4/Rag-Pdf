import os
import sys 
import json
import argparse

# --- Configuração de Caminhos ---
DIRETORIO_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_DO_SCRIPT) # Sobe um nível para a raiz geral
sys.path.insert(0, DIRETORIO_DO_SCRIPT)
# -------------------------------------------------

from utils.pdf_parser import fazer_upload_pdf, deletar_pdf_nuvem
from core.extractor import extrair_dados_estruturados
from utils.csv_writer import salvar_para_csv
from core.llm_service import get_gemini_clients

def executar_pipeline(nome_json_config: str):
    print(f"--- Iniciando Pipeline File API (Multimodal): {nome_json_config} ---")

    # Mapeando os diretórios da nova arquitetura
    caminho_configs = os.path.join(DIRETORIO_RAIZ, "inputs", "configs_jsons") 
    caminho_pdfs = os.path.join(DIRETORIO_RAIZ, "inputs", "pdfs")
    caminho_outputs = os.path.join(DIRETORIO_RAIZ, "outputs")
    caminho_arquivo_json = os.path.join(caminho_configs, nome_json_config)

    # 1. Carregando as Regras (JSON)
    if not os.path.exists(caminho_arquivo_json):
        print(f"Erro: Arquivo JSON não encontrado no caminho: {caminho_arquivo_json}")
        return

    with open(caminho_arquivo_json, 'r', encoding='utf-8') as f:
        config = json.load(f)

    arquivos_pdf = config.get("metadata", {}).get("files", [])
    modo_processamento = config.get("metadata", {}).get("modo_processamento", "individual")
    
    if not arquivos_pdf:
        print("Aviso: Nenhum PDF especificado na chave 'files' do JSON. Encerrando.")
        return

    # Inicia as instâncias do LangChain e GenAI nativo
    client_genai, llm_langchain = get_gemini_clients()

    # ==========================================
    # FLUXO 1: PROCESSAMENTO EM CONJUNTO
    # ==========================================
    if modo_processamento == "conjunto":
        print(f"\n[Modo Conjunto] Subindo {len(arquivos_pdf)} arquivos simultaneamente...")
        arquivos_nuvem = []
        arquivos_info = [] # Lista para guardar as infos pareadas (URI e Nome)
        
        # 1. Sobe todos os arquivos
        for nome_pdf in arquivos_pdf:
            caminho_pdf = os.path.join(caminho_pdfs, nome_pdf)
            arq = fazer_upload_pdf(client_genai, caminho_pdf)
            if arq: 
                arquivos_nuvem.append(arq)
                arquivos_info.append({"uri": arq.uri, "nome": nome_pdf})
            
        if not arquivos_nuvem: 
            return

        # 2. Extrai tudo de uma vez
        print("\n[Passo 2: Analisando todos os documentos simultaneamente...]")
        dados_extraidos = extrair_dados_estruturados(arquivos_info, config, llm_langchain)

        # 3. Salva em CSV único
        nome_csv_saida = os.path.join(caminho_outputs, "dados_extraidos_conjunto.csv")
        if dados_extraidos:
            salvar_para_csv(dados_extraidos, nome_csv_saida)
            print(f"Total de {len(dados_extraidos)} linhas consolidadas em '{nome_csv_saida}'")
        else:
            print("Atenção: Nenhum dado foi encontrado nos arquivos.")

        # 4. Deleta todos os arquivos
        print("\n[Passo 4: Faxina de Arquivos]")
        for arq in arquivos_nuvem:
            deletar_pdf_nuvem(client_genai, arq.name)

    # ==========================================
    # FLUXO 2: PROCESSAMENTO INDIVIDUAL (PADRÃO)
    # ==========================================
    else:
        for nome_pdf in arquivos_pdf:
            print(f"\n==================================================")
            print(f"[Modo Individual] Processando: {nome_pdf}")
            print(f"==================================================")
            
            caminho_pdf = os.path.join(caminho_pdfs, nome_pdf)
            nome_csv_saida = os.path.join(caminho_outputs, f"dados_extraidos_{nome_pdf.replace('.pdf', '')}.csv")

            # PASSO 1: File API
            arquivo_nuvem = fazer_upload_pdf(client_genai, caminho_pdf)
            if not arquivo_nuvem: 
                continue

            # PASSO 2: Extração
            print("\n[Passo 2: Analisando documento...]")
            arquivos_info = [{"uri": arquivo_nuvem.uri, "nome": nome_pdf}]
            dados_extraidos = extrair_dados_estruturados(arquivos_info, config, llm_langchain)

            # PASSO 3: CSV
            print(f"\n[Passo 3: Salvando resultados em CSV]")
            if dados_extraidos:
                salvar_para_csv(dados_extraidos, nome_csv_saida)
                print(f"Total de {len(dados_extraidos)} linhas estruturadas em '{nome_csv_saida}'")
            else:
                print(f"Atenção: Nenhum dado foi encontrado dentro de {nome_pdf}.")
            
            # PASSO 4: Limpeza (Fundamental para segurança)
            print("\n[Passo 4: Faxina de Arquivos]")
            deletar_pdf_nuvem(client_genai, arquivo_nuvem.name)
            
    print("\n--- Pipeline Concluído com Sucesso ---")

if __name__ == "__main__":
    # Permite passar o nome do arquivo JSON pelo terminal
    parser = argparse.ArgumentParser(description="Pipeline Multimodal de Extração de Dados via LLM")
    parser.add_argument(
        "config_json", 
        type=str, 
        help="Nome do arquivo JSON de configuração (ex: config_fs.json)"
    )
    args = parser.parse_args()
    
    executar_pipeline(args.config_json)