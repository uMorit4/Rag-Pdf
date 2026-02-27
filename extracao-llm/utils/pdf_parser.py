import time
from google import genai

def fazer_upload_pdf(client: genai.Client, caminho_arquivo: str, modelo_alvo: str = "gemini-2.5-flash"):
    """Faz o upload do PDF para a File API do Google e aguarda ficar pronto."""
    print(f"[File API] Iniciando upload de: {caminho_arquivo}")
    
    try:
        myfile = client.files.upload(file=caminho_arquivo)
        print(f"[File API] Upload concluído. Aguardando processamento multimodal (ID: {myfile.name})...")
        
        while myfile.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(2)
            myfile = client.files.get(name=myfile.name)
        
        print("\n[File API] Arquivo 100% pronto para leitura!")
        
        # --- NOVO: Chama a contagem de tokens aqui ---
        contar_tokens_pdf(client, myfile, modelo=modelo_alvo)
        # --------------------------------------------
        
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

def contar_tokens_pdf(client: genai.Client, myfile, modelo: str = "gemini-2.5-flash"):
    """
    Usa a API nativa do Google para contar os tokens de um arquivo já enviado.
    """
    try:
        # O método count_tokens precisa saber qual modelo você vai usar, 
        # pois a tokenização pode variar levemente de modelo para modelo.
        response = client.models.count_tokens(
            model=modelo,
            contents=myfile
        )
        print(f"[File API] O documento '{myfile.name}' possui {response.total_tokens} tokens.")
        return response.total_tokens
    except Exception as e:
        print(f"[File API] Erro ao contar tokens: {e}")
        return None