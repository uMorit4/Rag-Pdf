import csv
from typing import List, Dict

def salvar_para_csv(dados: List[Dict], nome_arquivo: str):
    """
    Salva uma lista de dicionários em um arquivo CSV.
    Os cabeçalhos do CSV são derivados das chaves do primeiro dicionário.
    """
    if not dados:
        print("[CSV] Nenhum dado recebido para salvar.")
        return

    headers = list(dados[0].keys())
    
    print(f"[CSV] Salvando dados em '{nome_arquivo}' com cabeçalhos: {headers}")
    
    try:
        with open(nome_arquivo, 'w', newline='', encoding='utf-8') as output_file:
            writer = csv.DictWriter(output_file, fieldnames=headers)

            writer.writeheader()

            writer.writerows(dados)
            
        print(f"[CSV] Arquivo '{nome_arquivo}' salvo com sucesso.")
        
    except Exception as e:
        print(f"[CSV] Erro ao salvar o arquivo CSV: {e}")