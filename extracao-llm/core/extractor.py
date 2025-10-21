import re
from typing import List, Optional, Type, Dict, Any
from pydantic import BaseModel, Field, create_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from core.llm_service import get_gemini_llm

# Um template de prompt claro, focado na extração de dados
PROMPT_TEMPLATE = """
Sua tarefa é agir como um especialista em análise de documentos financeiros e extrair dados de forma precisa.

Analise o CONTEÚDO DO DOCUMENTO fornecido e extraia *todas* as ocorrências dos dados solicitados.
Você deve encontrar os valores para os seguintes campos: {campos_lista_str}

Retorne uma lista de objetos, onde cada objeto corresponde a um conjunto de dados encontrado (por exemplo, uma linha ou um período de tempo em uma tabela).

CONTEÚDO DO DOCUMENTO:
---------------------
{contexto_documento}
---------------------

Siga rigorosamente o formato de saída JSON solicitado.
"""

def _slugify(text: str) -> str:
    """Converte um nome de campo (ex: "Net revenue") em um identificador válido (ex: "net_revenue")."""
    text = re.sub(r'[\s/()-]+', '_', text) # Substitui espaços e caracteres especiais por _
    text = re.sub(r'[^0-9a-zA-Z_]', '', text) # Remove caracteres não-alfanuméricos
    text = text.lower().strip('_')
    return text

def create_dynamic_output_schema(campos: List[str]) -> Type[BaseModel]:
    """
    Cria um "schema" Pydantic dinamicamente com base nos campos solicitados 
    pelo usuário, aninhado dentro de um objeto de saída principal.
    """
    
    # 1. Cria a definição dos campos para uma única linha de dados
    fields_definition: Dict[str, Any] = {}
    for campo_original in campos:
        field_name = _slugify(campo_original)
        # Todos os campos são opcionais (Optional[str]) para não quebrar a extração se um não for encontrado
        fields_definition[field_name] = (
            Optional[str], 
            Field(description=f"O valor extraído para o campo '{campo_original}'")
        )
        
    # 2. Cria o modelo Pydantic para uma "linha"
    # Ex: class ExtractedRow(BaseModel):
    #         net_revenue: Optional[str] = Field(...)
    #         cost_of_sales: Optional[str] = Field(...)
    DynamicRowModel = create_model(
        "ExtractedRow", 
        **fields_definition
    )
    
    # 3. Cria o modelo de Saída principal que contém uma *lista* de linhas
    # Ex: class ExtractionOutput(BaseModel):
    #         data: List[ExtractedRow] = Field(...)
    OutputModel = create_model(
        "ExtractionOutput",
        data=(List[DynamicRowModel], Field(description="Uma lista de todas as linhas de dados extraídas do documento."))
    )
    
    return OutputModel


def extrair_dados_estruturados(documentos: List[Document], campos_desejados: List[str]) -> List[Dict]:
    """
    Orquestra o processo de extração de dados estruturados de um PDF.
    """
    print(f"\n[Extrator] Iniciando extração para os campos: {campos_desejados}")
    
    # 1. Obter o LLM
    llm = get_gemini_llm()
    
    # 2. Criar o "schema" de saída dinâmico
    try:
        OutputSchema = create_dynamic_output_schema(campos_desejados)
        print(f"[Extrator] Schema dinâmico criado com sucesso.")
    except Exception as e:
        print(f"[Extrator] Erro ao criar schema Pydantic: {e}")
        return []

    # 3. Configurar o LLM para usar o "schema" de saída (Structured Output)
    llm_with_schema = llm.with_structured_output(OutputSchema)
    
    # 4. Preparar o contexto (juntar todas as páginas em um único texto)
    contexto = "\n\n--- Próxima Página ---\n\n".join([doc.page_content for doc in documentos])
    # O Gemini 1.5 Pro tem uma janela de contexto gigante, então podemos "stuffed" tudo.
    
    # 5. Criar o prompt
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    
    # 6. Criar a cadeia (chain)
    chain = prompt | llm_with_schema
    
    print("[Extrator] Invocando o LLM... (Isso pode levar alguns segundos)")
    
    # 7. Invocar a cadeia
    try:
        resultado_schema = chain.invoke({
            "contexto_documento": contexto,
            "campos_lista_str": ", ".join(campos_desejados)
        })
        
        # 8. Converter os modelos Pydantic de volta para dicionários
        dados_lista = [item.model_dump() for item in resultado_schema.data]
        
        print(f"[Extrator] Extração concluída. {len(dados_lista)} itens encontrados.")
        return dados_lista
        
    except Exception as e:
        print(f"[Extrator] Erro durante a invocação da cadeia: {e}")
        return []