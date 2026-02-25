import re
from typing import List, Optional, Type, Dict, Any
from pydantic import BaseModel, Field, create_model
from langchain_core.messages import HumanMessage, SystemMessage

def _slugify(text: str) -> str:
    text = re.sub(r'[\s/()-]+', '_', text)
    text = re.sub(r'[^0-9a-zA-Z_]', '', text)
    return text.lower().strip('_')

def create_dynamic_output_schema(campos_extracao: List[Dict[str, str]]) -> Type[BaseModel]:
    fields_definition: Dict[str, Any] = {}
    
    for campo in campos_extracao:
        nome = campo.get("nome", "")
        descricao = campo.get("descricao", "")
        regras = campo.get("regras_formatacao", "")
        
        field_slug = _slugify(nome)
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
    arquivos_info: List[Dict[str, str]], # <--- Agora recebe uma lista com dicts {uri, nome}
    config_json: Dict[str, Any],
    llm
) -> List[Dict]:
    
    prompts_config = config_json.get("prompts", {})
    campos_extracao = config_json.get("campos_extracao", [])
    
    system_base = prompts_config.get("system_base", "Você é um analista especialista.")
    system_instrucoes = prompts_config.get("system_instrucoes_extras", "")
    contexto_busca = prompts_config.get("contexto_busca_padrao", "")

    lista_nomes_campos = [c.get("nome") for c in campos_extracao if c.get("nome")]
    
    # Prepara a lista de nomes para o prompt
    nomes_arquivos_str = "\n".join([f"- {arq['nome']}" for arq in arquivos_info])

    prompt_texto = f"""
{system_base}

{system_instrucoes}

Contexto principal de busca: **{contexto_busca}**.

INFORMAÇÃO ADICIONAL:
Os nomes originais dos arquivos anexados são:
{nomes_arquivos_str}
Você pode (e deve) usar os nomes dos arquivos como contexto para extrair informações, caso a regra do campo solicite.

Campos que você DEVE extrair para cada item/arquivo: {", ".join(lista_nomes_campos)}

Siga rigorosamente as regras de formatação de cada campo no output JSON.
"""

    try:
        OutputSchema = create_dynamic_output_schema(campos_extracao)
        llm_with_schema = llm.with_structured_output(OutputSchema)
        
        conteudo_human_message = [
            {"type": "text", "text": "Por favor, analise o(s) documento(s) anexo(s) e extraia os dados solicitados, cruzando com os nomes dos arquivos passados nas instruções."}
        ]
        
        # Adiciona os arquivos fisicamente na requisição
        for arq in arquivos_info:
            conteudo_human_message.append(
                {"type": "file", "file_id": arq["uri"], "mime_type": "application/pdf"}
            )

        messages = [
            SystemMessage(content=prompt_texto),
            HumanMessage(content=conteudo_human_message)
        ]

        resultado = llm_with_schema.invoke(messages)
        
        if resultado and hasattr(resultado, 'data'):
            return [item.model_dump() for item in resultado.data]
        return []
        
    except Exception as e:
        print(f"[Extrator] Erro: {e}")
        return []