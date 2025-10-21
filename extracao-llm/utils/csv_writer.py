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

    # Pega os cabeçalhos (slugified) do primeiro item
    # Ex: 'net_revenue', 'cost_of_sales', 'date'
    headers = list(dados[0].keys())
    
    print(f"[CSV] Salvando dados em '{nome_arquivo}' com cabeçalhos: {headers}")
    
    try:
        with open(nome_arquivo, 'w', newline='', encoding='utf-8') as output_file:
            # Usa DictWriter para mapear os dicionários para as colunas do CSV
            writer = csv.DictWriter(output_file, fieldnames=headers)
            
            # Escreve o cabeçalho
            writer.writeheader()
            
            # Escreve todas as linhas de dados
            writer.writerows(dados)
            
        print(f"[CSV] Arquivo '{nome_arquivo}' salvo com sucesso.")
        
    except Exception as e:
        print(f"[CSV] Erro ao salvar o arquivo CSV: {e}")