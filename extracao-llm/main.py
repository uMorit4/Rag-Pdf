import os
from utils.pdf_parser import carregar_pdf
from core.extractor import extrair_dados_estruturados
from utils.csv_writer import salvar_para_csv

# --- Configuração ---

# Pega o caminho absoluto para o diretório onde este script (main.py) está
DIRETORIO_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))

# O PDF que você quer processar (o de Finanças que você enviou)
NOME_PDF_ENTRADA = "documento_mock.pdf"

# O nome do arquivo CSV que será gerado
NOME_CSV_SAIDA = "dados_extraidos.csv"

# --- Campos Desejados ---
# Defina aqui os campos que você quer extrair do PDF.
# Use os nomes exatos ou descrições do que você procura.
# O exemplo do seu pedido: ["net revenue", "cost of sales", "date"]
#
# Vou usar um exemplo mais alinhado com as tabelas do PDF:
CAMPOS_PARA_EXTRAIR = [
    "Time Period", # O LLM deve entender que isso é "Three Months Ended..."
    "Net revenue",
    "Cost of sales",
    "Gross profit"
]

# ----------------------

def executar_pipeline():
    print("--- Iniciando Pipeline de Extração ---")

    # 1. Definir caminhos completos
    caminho_pdf = os.path.join(DIRETORIO_DO_SCRIPT, NOME_PDF_ENTRADA)
    caminho_csv = os.path.join(DIRETORIO_DO_SCRIPT, NOME_CSV_SAIDA)

    # 2. Carregar o PDF
    print(f"\n[Passo 1: Carregando PDF]")
    print(f"Procurando PDF em: {caminho_pdf}")
    documentos = carregar_pdf(caminho_pdf)
    
    if not documentos:
        print("Falha ao carregar PDF. Abortando.")
        return

    print(f"PDF carregado. Total de páginas: {len(documentos)}")

    # 3. Extrair os dados usando o LLM
    print("\n[Passo 2: Extraindo Dados com LLM]")
    dados_extraidos = extrair_dados_estruturados(documentos, CAMPOS_PARA_EXTRAIR)
    
    if not dados_extraidos:
        print("Nenhum dado foi extraído. Abortando.")
        return

    # 4. Salvar os dados em CSV
    print("\n[Passo 3: Salvando em CSV]")
    salvar_para_csv(dados_extraidos, caminho_csv)
    
    print("\n--- Pipeline Concluído ---")

if __name__ == "__main__":
    executar_pipeline()