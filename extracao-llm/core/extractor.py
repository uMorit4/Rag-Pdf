import re
from typing import List, Optional, Type, Dict, Any
from pydantic import BaseModel, Field, create_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from core.llm_service import get_gemini_llm

def _slugify(text: str) -> str:
    """Converte texto em identificador válido."""
    text = re.sub(r'[\s/()-]+', '_', text)
    text = re.sub(r'[^0-9a-zA-Z_]', '', text)
    return text.lower().strip('_')

def create_dynamic_output_schema(campos_extracao: List[Dict[str, str]]) -> Type[BaseModel]:
    """Cria um schema Pydantic lendo os campos do JSON."""
    fields_definition: Dict[str, Any] = {}
    
    for campo in campos_extracao:
        nome = campo.get("nome", "")
        descricao = campo.get("descricao", "")
        regras = campo.get("regras_formatacao", "")
        
        field_slug = _slugify(nome)
        
        # Junta a descrição e as regras para guiar o LLM perfeitamente
        instrucao_completa = f"{descricao} Regras: {regras}".strip()
        
        fields_definition[field_slug] = (
            Optional[str], 
            Field(description=f"Campo: '{nome}'. Instrução: {instrucao_completa}")
        )
        
    DynamicRowModel = create_model("ExtractedRow", **fields_definition)
    OutputModel = create_model(
        "ExtractionOutput",
        data=(List[DynamicRowModel], Field(description="Lista de dados extraídos."))
    )
    return OutputModel

def extrair_dados_estruturados(
    documentos: List[Document], 
    config_json: Dict[str, Any]
) -> List[Dict]:
    
    # Extrai as configurações do JSON
    prompts_config = config_json.get("prompts", {})
    campos_extracao = config_json.get("campos_extracao", [])
    
    system_base = prompts_config.get("system_base", "Você é um analista de dados especialista.")
    system_instrucoes = prompts_config.get("system_instrucoes_extras", "")
    contexto_busca = prompts_config.get("contexto_busca_padrao", "")

    lista_nomes_campos = [c.get("nome") for c in campos_extracao if c.get("nome")]

    # Montagem do Prompt Dinâmico
    prompt_texto = f"""
{system_base}

{system_instrucoes}

Você deve extrair as informações {'focando no contexto: **' + contexto_busca + '**' if contexto_busca else 'do documento'}.

Campos a extrair:
{", ".join(lista_nomes_campos)}

**IMPORTANTE:** Para cada campo, siga estritamente a instrução e formatação definida na descrição do schema.

CONTEÚDO DO DOCUMENTO:
---------------------
{{contexto_documento}}
---------------------

Siga rigorosamente o formato de saída JSON.
"""

    llm = get_gemini_llm()
    
    try:
        OutputSchema = create_dynamic_output_schema(campos_extracao)
        llm_with_schema = llm.with_structured_output(OutputSchema)

        contexto_documento = "\n\n--- Pág ---\n\n".join([doc.page_content for doc in documentos])
        
        prompt = ChatPromptTemplate.from_template(prompt_texto)
        chain = prompt | llm_with_schema

        resultado = chain.invoke({"contexto_documento": contexto_documento})
        dados = [item.model_dump() for item in resultado.data]
        return dados
        
    except Exception as e:
        print(f"[Extrator] Erro: {e}")
        return []