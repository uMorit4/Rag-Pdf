# Extrator de Dados Financeiros (PDF para CSV)

Este projeto processa documentos PDF não estruturados e extrai dados estruturados utilizando a inteligência artificial do Google Gemini, salvando o resultado final em formato CSV. O pipeline é otimizado para lidar com documentos grandes, dividindo-os em blocos (*chunks*) para respeitar os limites de tokens da API.

## 📋 Pré-requisitos

Antes de executar o pipeline, certifique-se de ter o seguinte configurado no seu ambiente:

* **Python 3.8+** instalado.
* **Chave de API do Google Gemini** configurada e acessível pelo código em um .env como `GEMINI_API_KEY`.
* Executar `pip install -r requirements.txt`

## 🚀 Como Executar

1.  **Prepare o arquivo de entrada:**
    Coloque o documento PDF que você deseja processar no mesmo diretório do arquivo `main.py`. Por padrão, o script procurará por um arquivo com o nome exato de **`FS.pdf`**.
    *(Caso precise usar outro arquivo, altere o valor da variável `NOME_PDF_ENTRADA` no código)*.

2.  **Configure as variáveis de ambiente:**
    Certifique-se de que a sua chave de API esteja configurada no ambiente da sua máquina (por exemplo, `export GOOGLE_API_KEY="sua-chave-aqui"` no terminal ou configurada via um arquivo `.env`).

3.  **Inicie o processamento:**
    Abra o seu terminal, navegue até a pasta do projeto e execute o script:
    ```bash
    python main.py
    ```

4.  **Acompanhe o log e verifique o resultado:**
    O script exibirá o progresso no terminal (carregamento do PDF, divisão de *chunks* e comunicação com o LLM com pausas de 2 segundos para evitar limite de requisições). Ao final do processo, os dados extraídos (Data, Current Assets, USD, NTD e %) estarão salvos no arquivo **`dados_extraidos.csv`** no mesmo diretório.