import re
from typing import List, Optional, Type, Dict, Any, Union
from pydantic import BaseModel, Field, create_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from core.llm_service import get_gemini_llm

# --- PROMPTS ---
# Atualizei levemente o prompt para reforçar que ele deve ler as descrições dos campos
PROMPT_TEMPLATE_CONTEXTO = """
Sua tarefa é agir como um analista de dados especialista.
Seu objetivo é extrair informações *apenas* da seção ou contexto específico: **"{contexto_busca}"**.

1. Localize esta seção no CONTEÚDO DO DOCUMENTO. Se não encontrar, retorne lista vazia. Seja bem criterioso na busca e não retorne nada a não ser que tenha encontrado EXATAMENTE o que foi solicitado.
2. Se encontrar, extraia os dados solicitados.
3. **IMPORTANTE:** Para cada campo, siga estritamente a instrução de formatação fornecida na definição do schema (descrição do campo).

Campos a extrair:
{campos_lista_str}

CONTEÚDO DO DOCUMENTO:
---------------------
{contexto_documento}
---------------------

Siga rigorosamente o formato de saída JSON.
"""

SYSTEM_PROMPT = """
Sua tarefa é agir como um analista de dados especialista.
Extraia os dados solicitados do documento abaixo.

**IMPORTANTE:** Para cada campo, siga estritamente a instrução de formatação fornecida na definição do schema (descrição do campo).

Campos a extrair:
{campos_lista_str}

CONTEÚDO DO DOCUMENTO:
---------------------
{contexto_documento}
---------------------

Siga rigorosamente o formato de saída JSON.
"""

def _slugify(text: str) -> str:
    """Converte texto em identificador válido."""
    text = re.sub(r'[\s/()-]+', '_', text)
    text = re.sub(r'[^0-9a-zA-Z_]', '', text)
    text = text.lower().strip('_')
    return text

def create_dynamic_output_schema(campos_dict: Dict[str, str]) -> Type[BaseModel]:
    """
    Cria um schema Pydantic onde a descrição de cada campo vem do 
    dicionário de instruções do usuário.
    """
    fields_definition: Dict[str, Any] = {}
    
    for campo_nome, instrucao_formatacao in campos_dict.items():
        field_slug = _slugify(campo_nome)
        
        # AQUI ESTÁ O SEGREDO:
        # Passamos a sua instrução ("Retornar apenas números...") para o LLM via 'description'
        fields_definition[field_slug] = (
            Optional[str], 
            Field(description=f"Campo: '{campo_nome}'. Instrução: {instrucao_formatacao}")
        )
        
    DynamicRowModel = create_model("ExtractedRow", **fields_definition)
    
    OutputModel = create_model(
        "ExtractionOutput",
        data=(List[DynamicRowModel], Field(description="Lista de dados extraídos."))
    )
    
    return OutputModel

def extrair_dados_estruturados(
    documentos: List[Document], 
    campos_config: Union[List[str], Dict[str, str]], # Aceita Lista (legado) ou Dict (novo)
    contexto_busca: Optional[str] = None
) -> List[Dict]:
    
    # 1. Normalização: Se o usuário passar Lista (modo antigo), converte para Dict com instrução padrão
    if isinstance(campos_config, list):
        campos_dict = {campo: "Extraia o valor correspondente a este campo." for campo in campos_config}
    else:
        campos_dict = campos_config

    # Lista de nomes para o prompt (apenas as chaves)
    lista_nomes_campos = list(campos_dict.keys())

    # 2. Selecionar Prompt
    if contexto_busca:
        print(f"\n[Extrator] Extração com CONTEXTO: '{contexto_busca}'")
        prompt_template = PROMPT_TEMPLATE_CONTEXTO
        inputs = {
            "contexto_busca": contexto_busca,
            "campos_lista_str": ", ".join(lista_nomes_campos),
        }
    else:
        print(f"\n[Extrator] Extração GENÉRICA.")
        prompt_template = SYSTEM_PROMPT
        inputs = {
            "campos_lista_str": ", ".join(lista_nomes_campos),
        }

    llm = get_gemini_llm()
    
    try:
        # 3. Criar Schema com as instruções do Dicionário
        OutputSchema = create_dynamic_output_schema(campos_dict)
        llm_with_schema = llm.with_structured_output(OutputSchema)
        
        # 4. Preparar Documento
        contexto_documento = "\n\n--- Pág ---\n\n".join([doc.page_content for doc in documentos])
        inputs["contexto_documento"] = contexto_documento
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | llm_with_schema
        
        # 5. Invocar
        resultado = chain.invoke(inputs)
        dados = [item.model_dump() for item in resultado.data]
        return dados
        
    except Exception as e:
        print(f"[Extrator] Erro: {e}")
        return []