from typing import List
from collections import Counter
import re

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

def limpar_paginas_pdf(
    paginas: List[Document],
    frac_repeticao: float = 0.5,
) -> List[Document]:
    if not paginas:
        return paginas

    todas_linhas_por_pagina: List[List[str]] = []
    contador_linhas = Counter()

    for doc in paginas:
        texto = doc.page_content or ""
        linhas = [l.strip() for l in texto.splitlines() if l.strip()]
        todas_linhas_por_pagina.append(linhas)
        contador_linhas.update(set(linhas))

    n_paginas = len(paginas)
    limite_repeticao = max(2, int(n_paginas * frac_repeticao))
    linhas_ruido = {
        linha for linha, c in contador_linhas.items() if c >= limite_repeticao
    }

    print(
        f"[Limpeza PDF] Identificadas {len(linhas_ruido)} linhas repetidas "
        f"(provável cabeçalho/rodapé) em >= {limite_repeticao} páginas."
    )

    for doc, linhas in zip(paginas, todas_linhas_por_pagina):
        # Remove apenas as linhas identificadas como ruído estrutural
        linhas_filtradas = [l for l in linhas if l not in linhas_ruido]

        linhas_mescladas: List[str] = []
        buffer = ""
        for l in linhas_filtradas:
            if not buffer:
                buffer = l
                continue

            # Se a linha atual não termina com pontuação de final de frase, junta com a próxima
            if not re.search(r"[.!?:;]$", buffer):
                buffer += " " + l
            else:
                linhas_mescladas.append(buffer)
                buffer = l

        if buffer:
            linhas_mescladas.append(buffer)

        # Normaliza espaços extras
        linhas_norm = [re.sub(r"[ \t]+", " ", l).strip() for l in linhas_mescladas]
        doc.page_content = "\n".join(linhas_norm)

    return paginas

def carregar_pdf(caminho_arquivo: str) -> List[Document]:
    print(f"Carregando PDF de: {caminho_arquivo}")
    try:
        loader = PyPDFLoader(caminho_arquivo)
        paginas: List[Document] = loader.load()
        print(f"PDF carregado com sucesso. Número de páginas: {len(paginas)}")

        paginas = limpar_paginas_pdf(paginas, frac_repeticao=0.5)

        print("Limpeza básica aplicada às páginas (remoção de cabeçalho/rodapé genérico, "
              "merge de linhas e normalização de espaços).")
        return paginas
    except Exception as e:
        print(f"Erro ao carregar o PDF: {e}")
        return []