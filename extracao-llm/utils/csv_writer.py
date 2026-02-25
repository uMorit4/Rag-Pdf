import csv
import os
from typing import List, Dict

def salvar_para_csv(dados: List[Dict], nome_arquivo: str):
    if not dados:
        print("[CSV] Nenhum dado recebido para salvar.")
        return

    headers = list(dados[0].keys())

    diretorio = os.path.dirname(nome_arquivo)
    if diretorio:
        os.makedirs(diretorio, exist_ok=True)
        
    print(f"[CSV] Salvando dados em '{nome_arquivo}' com cabeçalhos: {headers}")
    
    try:
        with open(nome_arquivo, 'w', newline='', encoding='utf-8') as output_file:
            writer = csv.DictWriter(output_file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(dados)
            
        print(f"[CSV] Arquivo '{nome_arquivo}' salvo com sucesso.")
        
    except Exception as e:
        print(f"[CSV] Erro ao salvar o arquivo CSV: {e}")