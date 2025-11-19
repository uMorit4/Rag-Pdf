from typing import List
from collections import Counter
import re

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


def limpar_paginas_pdf(
    paginas: List[Document],
    frac_repeticao: float = 0.5,
) -> List[Document]:
    """
    Aplica limpezas para reduzir tokens e ruído:
    - Remove linhas de cabeçalho/rodapé repetidas em muitas páginas
    - Junta linhas quebradas no meio de frases
    - Normaliza espaços em branco

    frac_repeticao:
        Fração mínima de páginas em que uma linha precisa aparecer
        para ser considerada "ruído global" (cabeçalho/rodapé).
        Ex: 0.5 => linha que aparece em pelo menos 50% das páginas.
    """
    if not paginas:
        return paginas

    todas_linhas_por_pagina: List[List[str]] = []
    contador_linhas = Counter()

    # 1) Coletar linhas de cada página e contar repetições
    for doc in paginas:
        texto = doc.page_content or ""
        # Remove linhas vazias e espaços nas extremidades
        linhas = [l.strip() for l in texto.splitlines() if l.strip()]
        todas_linhas_por_pagina.append(linhas)

        # para identificar cabeçalho/rodapé global,
        # contamos cada linha no máximo 1x por página
        contador_linhas.update(set(linhas))

    n_paginas = len(paginas)
    # Pelo menos 2 páginas, e pelo menos frac_repeticao das páginas
    limite_repeticao = max(2, int(n_paginas * frac_repeticao))
    linhas_ruido = {
        linha for linha, c in contador_linhas.items() if c >= limite_repeticao
    }

    print(
        f"[Limpeza PDF] Identificadas {len(linhas_ruido)} linhas repetidas "
        f"(provável cabeçalho/rodapé) em >= {limite_repeticao} páginas."
    )

    # 2) Limpar página a página
    for doc, linhas in zip(paginas, todas_linhas_por_pagina):
        # 2.1) Remover linhas de ruído global
        linhas_filtradas = [l for l in linhas if l not in linhas_ruido]

        # (Opcional) Remover disclaimers específicos via regex
        # Exemplo:
        padroes_descartar = [
            r"this document.*not (an offer|constitute)",
            r"tsmc.*all rights reserved",
        ]
        linhas_filtradas2: List[str] = []
        for l in linhas_filtradas:
            if any(re.search(p, l, flags=re.I) for p in padroes_descartar):
                continue
            linhas_filtradas2.append(l)

        # 2.2) Juntar linhas quebradas "no meio da frase"
        linhas_mescladas: List[str] = []
        buffer = ""
        for l in linhas_filtradas2:
            if not buffer:
                buffer = l
                continue

            # se a linha anterior NÃO termina com pontuação "forte",
            # assumimos que a próxima linha é continuação
            if not re.search(r"[.!?:;]$", buffer):
                buffer += " " + l
            else:
                linhas_mescladas.append(buffer)
                buffer = l

        if buffer:
            linhas_mescladas.append(buffer)

        # 2.3) Normalizar espaços dentro de cada linha
        linhas_norm = [re.sub(r"[ \t]+", " ", l).strip() for l in linhas_mescladas]

        # 2.4) Reconstituir conteúdo da página
        doc.page_content = "\n".join(linhas_norm)

    return paginas


def carregar_pdf(caminho_arquivo: str) -> List[Document]:
    """
    Carrega um arquivo PDF, limpa o texto e retorna uma lista de Documentos (páginas).
    
    Args:
        caminho_arquivo: O caminho para o arquivo PDF.

    Returns:
        Uma lista de objetos Document do LangChain, onde cada objeto representa uma página.
    """
    print(f"Carregando PDF de: {caminho_arquivo}")
    try:
        # PyPDFLoader carrega o PDF e já o divide por páginas
        loader = PyPDFLoader(caminho_arquivo)
        paginas: List[Document] = loader.load()
        print(f"PDF carregado com sucesso. Número de páginas: {len(paginas)}")

        # >>> AQUI entra a mágica da otimização <<<
        paginas = limpar_paginas_pdf(paginas, frac_repeticao=0.5)

        print("Limpeza básica aplicada às páginas (remoção de cabeçalho/rodapé, "
              "merge de linhas e normalização de espaços).")
        return paginas
    except Exception as e:
        print(f"Erro ao carregar o PDF: {e}")
        return []
