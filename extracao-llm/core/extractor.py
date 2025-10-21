import re
from typing import List, Optional, Type, Dict, Any
from pydantic import BaseModel, Field, create_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from core.llm_service import get_gemini_llm

# --- TEMPLATE DE PROMPT 1: COM CONTEXTO (O NOVO) ---
PROMPT_TEMPLATE_CONTEXTO = """
Sua tarefa é agir como um analista de dados especialista.
Seu objetivo é extrair informações *apenas* da seção ou contexto específico: **"{contexto_busca}"**.

Primeiro, localize esta seção no CONTEÚDO DO DOCUMENTO.
Se esta seção não for encontrada, retorne uma lista vazia.

Se a seção **"{contexto_busca}"** for encontrada, extraia *todas* as ocorrências dos seguintes campos *dentro* dela:
{campos_lista_str}

Retorne uma lista de objetos, onde cada objeto corresponde a um item encontrado (por exemplo, um diretor na lista de propostas).

CONTEÚDO DO DOCUMENTO:
---------------------
{contexto_documento}
---------------------

Siga rigorosamente o formato de saída JSON solicitado. Se nada for encontrado que corresponda ao contexto e aos campos, retorne uma lista vazia.
"""

# --- TEMPLATE DE PROMPT 2: GENÉRICO (O ANTIGO) ---
PROMPT_TEMPLATE_GENERICO = """
Sua tarefa é agir como um analista de dados especialista.
Analise o CONTEÚDO DO DOCUMENTO fornecido e extraia *todas* as ocorrências dos dados solicitados.

Você deve encontrar os valores para os seguintes campos:
{campos_lista_str}

Retorne uma lista de objetos, onde cada objeto corresponde a um conjunto de dados encontrado.

CONTEÚDO DO DOCUMENTO:
---------------------
{contexto_documento}
---------------------

Siga rigorosamente o formato de saída JSON solicitado. Se nada for encontrado, retorne uma lista vazia.
"""


def _slugify(text: str) -> str:
    """Converte um nome de campo (ex: "Net revenue") em um identificador válido (ex: "net_revenue")."""
    text = re.sub(r'[\s/()-]+', '_', text)
    text = re.sub(r'[^0-9a-zA-Z_]', '', text)
    text = text.lower().strip('_')
    return text

def create_dynamic_output_schema(campos: List[str]) -> Type[BaseModel]:
    """Cria um "schema" Pydantic dinamicamente com base nos campos solicitados."""
    
    fields_definition: Dict[str, Any] = {}
    for campo_original in campos:
        field_name = _slugify(campo_original)
        fields_definition[field_name] = (
            Optional[str], 
            Field(description=f"O valor extraído para o campo '{campo_original}'")
        )
        
    DynamicRowModel = create_model("ExtractedRow", **fields_definition)
    
    OutputModel = create_model(
        "ExtractionOutput",
        data=(List[DynamicRowModel], Field(description="Uma lista de todas as linhas de dados extraídas do documento."))
    )
    
    return OutputModel


def extrair_dados_estruturados(
    documentos: List[Document], 
    campos_desejados: List[str], 
    contexto_busca: Optional[str] = None  # <-- NOVO PARÂMETRO OPCIONAL
) -> List[Dict]:
    """
    Orquestra o processo de extração de dados estruturados de um PDF.
    Se 'contexto_busca' for fornecido, busca apenas dentro desse contexto.
    """
    
    # 1. Selecionar o prompt e os inputs corretos
    if contexto_busca:
        print(f"\n[Extrator] Iniciando extração com CONTEXTO: '{contexto_busca}'")
        print(f"[Extrator] Campos alvo: {campos_desejados}")
        prompt_template_texto = PROMPT_TEMPLATE_CONTEXTO
        prompt_input = {
            "contexto_busca": contexto_busca,
            "campos_lista_str": ", ".join(campos_desejados),
        }
    else:
        print(f"\n[Extrator] Iniciando extração GENÉRICA.")
        print(f"[Extrator] Campos alvo: {campos_desejados}")
        prompt_template_texto = PROMPT_TEMPLATE_GENERICO
        prompt_input = {
            "campos_lista_str": ", ".join(campos_desejados),
        }

    # 2. Obter o LLM
    llm = get_gemini_llm()
    
    # 3. Criar o "schema" de saída dinâmico
    try:
        OutputSchema = create_dynamic_output_schema(campos_desejados)
        # print(f"[Extrator] Schema dinâmico criado com sucesso.") # (Opcional, pode poluir o log)
    except Exception as e:
        print(f"[Extrator] Erro ao criar schema Pydantic: {e}")
        return []

    # 4. Configurar o LLM para usar o "schema" de saída
    llm_with_schema = llm.with_structured_output(OutputSchema)
    
    # 5. Preparar o contexto (juntar todas as páginas do chunk)
    contexto_documento = "\n\n--- Próxima Página ---\n\n".join([doc.page_content for doc in documentos])
    
    # Adicionar o contexto do documento ao input do prompt
    prompt_input["contexto_documento"] = contexto_documento
    
    # 6. Criar o prompt
    prompt = ChatPromptTemplate.from_template(prompt_template_texto)
    
    # 7. Criar a cadeia (chain)
    chain = prompt | llm_with_schema
    
    print("[Extrator] Invocando o LLM... (Isso pode levar alguns segundos)")
    
    # 8. Invocar a cadeia
    try:
        resultado_schema = chain.invoke(prompt_input)
        
        dados_lista = [item.model_dump() for item in resultado_schema.data]
        
        print(f"[Extrator] Extração concluída. {len(dados_lista)} itens encontrados.")
        return dados_lista
        
    except Exception as e:
        print(f"[Extrator] Erro durante a invocação da cadeia: {e}")
        return []