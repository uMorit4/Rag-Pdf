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
    print(f"--- Iniciando Pipeline File API (Iterativo): {nome_json_config} ---")

    caminho_configs = os.path.join(DIRETORIO_RAIZ, "inputs", "configs_jsons") 
    caminho_pdfs = os.path.join(DIRETORIO_RAIZ, "inputs", "pdfs")
    caminho_outputs = os.path.join(DIRETORIO_RAIZ, "outputs")
    caminho_arquivo_json = os.path.join(caminho_configs, nome_json_config)

    if not os.path.exists(caminho_arquivo_json):
        print(f"Erro: Arquivo JSON não encontrado no caminho: {caminho_arquivo_json}")
        return

    with open(caminho_arquivo_json, 'r', encoding='utf-8') as f:
        config = json.load(f)

    arquivos_pdf = config.get("metadata", {}).get("files", [])
    
    if not arquivos_pdf:
        print("Aviso: Nenhum PDF especificado na chave 'files' do JSON. Encerrando.")
        return

    print(f"-> Fila de processamento: {len(arquivos_pdf)} arquivo(s).")
    
    client_genai, llm_langchain = get_gemini_clients()

    # Lista mestra que vai guardar os dados de TODOS os arquivos processados
    todos_dados_extraidos = []

    # ==========================================
    # PROCESSAMENTO ITERATIVO (UM A UM)
    # ==========================================
    for index, nome_pdf in enumerate(arquivos_pdf, start=1):
        print(f"\n==================================================")
        print(f"[{index}/{len(arquivos_pdf)}] Processando: {nome_pdf}")
        print(f"==================================================")
        
        caminho_pdf = os.path.join(caminho_pdfs, nome_pdf)

        if not os.path.exists(caminho_pdf):
            print(f"  [Aviso] Arquivo não encontrado na pasta, pulando: {nome_pdf}")
            continue

        try:
            # PASSO 1: Upload individual
            arquivo_nuvem = fazer_upload_pdf(client_genai, caminho_pdf)
            if not arquivo_nuvem: 
                continue

            # PASSO 2: Extração isolada
            print("  [Extração] Analisando documento...")
            arquivos_info = [{"uri": arquivo_nuvem.uri, "nome": nome_pdf}]
            dados_extraidos = extrair_dados_estruturados(arquivos_info, config, llm_langchain)

            # PASSO 3: Acumulando resultados
            if dados_extraidos:
                # Adiciona o nome do arquivo aos dados para fácil identificação no Excel/CSV
                for linha in dados_extraidos:
                    linha_com_origem = {"Arquivo_Origem": nome_pdf}
                    linha_com_origem.update(linha)
                    todos_dados_extraidos.append(linha_com_origem)
                    
                print(f"  [Sucesso] Dados extraídos e armazenados na memória.")
            else:
                print(f"  [Atenção] Nenhum dado retornado para este arquivo.")
            
            # PASSO 4: Limpeza da nuvem (Garante que o contexto fique zerado para o próximo arquivo)
            deletar_pdf_nuvem(client_genai, arquivo_nuvem.name)
            
        except Exception as e:
            print(f"  [Erro] Falha catastrófica ao processar {nome_pdf}: {e}")
            # Em caso de erro, tenta limpar o arquivo da nuvem de qualquer forma
            try:
                deletar_pdf_nuvem(client_genai, arquivo_nuvem.name)
            except:
                pass

    # ==========================================
    # SALVAMENTO FINAL CONSOLIDADO
    # ==========================================
    print("\n==================================================")
    print("CONSOLIDAÇÃO FINAL DOS DADOS")
    print("==================================================")
    
    if todos_dados_extraidos:
        # Pega o nome do json, tira a extensão e cria o nome do CSV final
        nome_base = nome_json_config.replace('.json', '')
        nome_csv_saida = os.path.join(caminho_outputs, f"dados_consolidados_{nome_base}.csv")
        
        salvar_para_csv(todos_dados_extraidos, nome_csv_saida)
        print(f"\n--- Pipeline Concluído! Total de {len(todos_dados_extraidos)} registros em: {nome_csv_saida} ---")
    else:
        print("\n--- Pipeline Concluído, mas nenhum dado útil foi extraído de toda a fila. ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline Multimodal de Extração de Dados via LLM")
    parser.add_argument(
        "config_json", 
        type=str, 
        help="Nome do arquivo JSON de configuração (ex: config_fs.json)"
    )
    args = parser.parse_args()
    
    executar_pipeline(args.config_json)
