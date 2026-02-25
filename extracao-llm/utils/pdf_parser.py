import time
from google import genai

def fazer_upload_pdf(client: genai.Client, caminho_arquivo: str):
    """Faz o upload do PDF para a File API do Google e aguarda ficar pronto."""
    print(f"[File API] Iniciando upload de: {caminho_arquivo}")
    
    try:
        myfile = client.files.upload(file=caminho_arquivo)
        print(f"[File API] Upload concluído. Aguardando processamento multimodal (ID: {myfile.name})...")
        
        # Como PDFs são documentos complexos, a API precisa de alguns segundos para extrair o layout
        while myfile.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(2)
            myfile = client.files.get(name=myfile.name)
        
        print("\n[File API] Arquivo 100% pronto para leitura!")
        return myfile
    except Exception as e:
        print(f"\n[File API] Erro crítico no upload: {e}")
        return None

def deletar_pdf_nuvem(client: genai.Client, file_name: str):
    """Limpa o arquivo dos servidores do Google após a extração."""
    try:
        client.files.delete(name=file_name)
        print(f"[File API] O arquivo temporário {file_name} foi apagado da nuvem com sucesso.")
    except Exception as e:
        print(f"[File API] Erro ao deletar arquivo: {e}")