#!/usr/bin/env python3
"""
avaliador-conteudo.py
=================
Pontuação de qualidade de conteúdo multidimensional usando uma rubrica padronizada.

Avalia conteúdo de marketing em legibilidade, sinais SEO, estrutura,
qualidade de CTA e detecção de spam/preenchimento. Retorna uma pontuação
de qualidade geral (0-100) com decomposição de dimensão ponderada e recomendações acionáveis.

Dependências: textstat, nltk, json, re, sys, argparse, pathlib

Uso:
    python avaliador-conteudo.py --text "Seu conteúdo..." --type blog --keyword "ferramentas IA"
    python avaliador-conteudo.py --file artigo.md --type landing_page --keyword "gerenciamento de projetos"
    python avaliador-conteudo.py --file email.txt --type email

Tipos de Conteúdo:  blog | email | ad | landing_page | social
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Verificação de dependências
# ---------------------------------------------------------------------------
try:
    import textstat
except ImportError:
    print(json.dumps({
        "fallback": True,
        "error": "textstat_not_installed",
        "message": "textstat não instalado. Pontuação de conteúdo requer: pip install textstat",
        "overall_score": None,
        "recommendation": "Instale textstat para pontuação automatizada de conteúdo, ou avalie manualmente usando skills/context-engine/scoring-rubrics.md"
    }, indent=2))
    sys.exit(0)

try:
    import nltk
except ImportError:
    print(json.dumps({
        "fallback": True,
        "error": "nltk_not_installed",
        "message": "NLTK não instalado. Pontuação de conteúdo requer: pip install nltk",
        "overall_score": None,
        "recommendation": "Instale NLTK para pontuação automatizada de conteúdo, ou avalie manualmente usando skills/context-engine/scoring-rubrics.md"
    }, indent=2))
    sys.exit(0)

for _res in ("punkt", "punkt_tab"):
    try:
        nltk.data.find(f"tokenizers/{_res}")
    except LookupError:
        nltk.download(_res, quiet=True)

from nltk.tokenize import sent_tokenize

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

CONTENT_TYPE_WEIGHTS = {
    "blog": {
        "readability": 0.20,
        "seo": 0.25,
        "structure": 0.20,
        "cta": 0.10,
        "spam_filler": 0.10,
        "length": 0.15,
    },
    "email": {
        "readability": 0.25,
        "seo": 0.05,
        "structure": 0.15,
        "cta": 0.30,
        "spam_filler": 0.15,
        "length": 0.10,
    },
    "ad": {
        "readability": 0.20,
        "seo": 0.10,
        "structure": 0.10,
        "cta": 0.35,
        "spam_filler": 0.15,
        "length": 0.10,
    },
    "landing_page": {
        "readability": 0.15,
        "seo": 0.25,
        "structure": 0.20,
        "cta": 0.25,
        "spam_filler": 0.05,
        "length": 0.10,
    },
    "social": {
        "readability": 0.25,
        "seo": 0.05,
        "structure": 0.10,
        "cta": 0.25,
        "spam_filler": 0.20,
        "length": 0.15,
    },
}

IDEAL_WORD_COUNTS = {
    "blog": (800, 2500),
    "email": (50, 500),
    "ad": (15, 150),
    "landing_page": (300, 1500),
    "social": (10, 280),
}

# Palavras e frases de spam / preenchimento
SPAM_WORDS = {
    "act now", "buy now", "limited time", "once in a lifetime", "risk-free",
    "no obligation", "free", "100% free", "click here", "click below",
    "congratulations", "winner", "you've been selected", "double your",
    "earn extra cash", "make money", "$$", "!!!",
    "no questions asked", "guaranteed", "no catch", "instant",
    "apply now", "order now",
}

FILLER_WORDS = {
    "very", "really", "just", "actually", "basically", "honestly",
    "literally", "simply", "quite", "rather", "somewhat", "pretty",
    "stuff", "things", "thing", "kind of", "sort of", "a lot",
    "in order to", "due to the fact", "at the end of the day",
    "it goes without saying", "needless to say", "as a matter of fact",
    "for all intents and purposes", "in terms of",
}

# Padrões de CTA
CTA_PATTERNS = [
    r"\b(sign up|signup)\b",
    r"\b(get started|start now|start today)\b",
    r"\b(learn more|read more|find out more)\b",
    r"\b(download|download now|get your copy)\b",
    r"\b(subscribe|join now|join us|join today)\b",
    r"\b(buy now|shop now|order now|purchase)\b",
    r"\b(try (it )?free|free trial|start free)\b",
    r"\b(book (a )?demo|schedule (a )?call|request (a )?demo)\b",
    r"\b(contact us|reach out|get in touch)\b",
    r"\b(claim (your )?offer|grab (your )?spot)\b",
    r"\b(register|enroll|apply)\b",
    r"\b(explore|discover)\b",
]

CTA_STRONG_VERBS = {
    "sign up", "signup", "get started", "start now", "start today",
    "download", "subscribe", "join", "buy", "shop", "order", "purchase",
    "try", "book", "schedule", "request", "claim", "grab", "register",
    "enroll", "apply",
}

CTA_WEAK_VERBS = {
    "learn more", "read more", "find out", "explore", "discover",
    "contact", "reach out", "click here",
}

# ---------------------------------------------------------------------------
# Funções de pontuação
# ---------------------------------------------------------------------------

def _split_words(text: str) -> list[str]:
    """Extraia tokens alfabéticos do texto."""
    return [w for w in re.findall(r"[a-zA-Z']+", text) if len(w) > 0]


def score_readability(text: str, content_type: str) -> dict:
    """Pontua legibilidade de 0-100 usando Flesch Reading Ease como métrica principal."""
    ease = textstat.flesch_reading_ease(text)
    grade = textstat.flesch_kincaid_grade(text)

    # Faixas-alvo de legibilidade por tipo de conteúdo
    targets = {
        "blog": (50, 70),
        "email": (55, 75),
        "ad": (60, 80),
        "landing_page": (50, 70),
        "social": (65, 85),
    }
    lo, hi = targets.get(content_type, (50, 70))
    mid = (lo + hi) / 2

    # Pontuação: 100 se dentro da faixa, decai linearmente fora
    if lo <= ease <= hi:
        score = 100.0
    elif ease < lo:
        score = max(0, 100 - (lo - ease) * 2.5)
    else:
        score = max(0, 100 - (ease - hi) * 2.0)

    recommendations = []
    if ease < lo:
        recommendations.append(
            f"Conteúdo mais difícil de ler do que o ideal para {content_type} "
            f"(Reading Ease: {ease:.1f}, alvo: {lo}-{hi}). "
            "Simplifique as frases e use palavras mais curtas."
        )
    elif ease > hi:
        recommendations.append(
            f"Conteúdo pode ser simples demais para {content_type} "
            f"(Reading Ease: {ease:.1f}, alvo: {lo}-{hi}). "
            "Considere adicionar mais profundidade."
        )

    return {
        "score": round(min(max(score, 0), 100), 2),
        "flesch_reading_ease": round(ease, 2),
        "flesch_kincaid_grade": round(grade, 2),
        "target_ease_range": [lo, hi],
        "recommendations": recommendations,
    }


def score_seo(text: str, keyword: str | None, content_type: str) -> dict:
    """Pontua sinais SEO de 0-100."""
    score = 0.0
    max_possible = 0.0
    details = {}
    recommendations = []

    text_lower = text.lower()
    words = _split_words(text)
    word_count = len(words)

    # --- Verificações de palavra-chave (50 pontos possíveis) ---
    if keyword:
        kw_lower = keyword.lower()
        max_possible += 50

        # Palavra-chave nas primeiras 100 palavras
        first_100 = " ".join(words[:100]).lower()
        kw_in_first_100 = kw_lower in first_100
        if kw_in_first_100:
            score += 15
        else:
            recommendations.append(
                f"Palavra-chave '{keyword}' não encontrada nas primeiras 100 palavras. "
                "Mova-a para mais cedo no conteúdo para melhorar o SEO."
            )
        details["keyword_in_first_100_words"] = kw_in_first_100

        # Densidade de palavra-chave (ideal: 1-3%)
        kw_count = len(re.findall(r'\b' + re.escape(kw_lower) + r'\b', text_lower))
        density = (kw_count / max(word_count, 1)) * 100 if word_count else 0
        details["keyword_density_pct"] = round(density, 2)
        details["keyword_count"] = kw_count

        if 0.8 <= density <= 3.0:
            score += 20
        elif 0.3 <= density < 0.8:
            score += 10
            recommendations.append(
                f"Densidade da palavra-chave ({density:.1f}%) está levemente baixa. "
                "Mire em 1-3% para SEO ideal."
            )
        elif density > 3.0:
            score += 5
            recommendations.append(
                f"Densidade da palavra-chave ({density:.1f}%) está alta demais. "
                "Pode ser sinalizado como keyword stuffing. Mire em 1-3%."
            )
        else:
            recommendations.append(
                f"Palavra-chave '{keyword}' quase não aparece (densidade: {density:.1f}%). "
                "Use-a de forma mais natural ao longo do conteúdo."
            )

        # Palavra-chave em títulos
        headings = re.findall(r"^#+\s+(.+)$", text, re.MULTILINE)
        headings += re.findall(r"<h[1-6][^>]*>(.+?)</h[1-6]>", text, re.IGNORECASE)
        kw_in_heading = any(kw_lower in h.lower() for h in headings)
        details["keyword_in_heading"] = kw_in_heading
        if kw_in_heading:
            score += 15
        elif headings:
            recommendations.append(
                f"Palavra-chave '{keyword}' não encontrada em nenhum título. "
                "Inclua-a em pelo menos um H2 ou H3."
            )
    else:
        details["keyword"] = "Nenhuma palavra-chave fornecida — verificações SEO de keyword ignoradas."

    # --- Estrutura de títulos (25 pontos) ---
    max_possible += 25
    heading_md = re.findall(r"^(#{1,6})\s+", text, re.MULTILINE)
    heading_html = re.findall(r"<h([1-6])", text, re.IGNORECASE)
    heading_count = len(heading_md) + len(heading_html)
    details["heading_count"] = heading_count

    if content_type in ("blog", "landing_page"):
        if heading_count >= 3:
            score += 25
        elif heading_count >= 1:
            score += 15
            recommendations.append(
                f"Apenas {heading_count} título(s) encontrado(s). Use mais subtítulos "
                "(H2, H3) para melhorar a escaneabilidade e o SEO."
            )
        else:
            recommendations.append(
                "Nenhum título encontrado. Adicione subtítulos H2/H3 para estrutura e SEO."
            )
    else:
        # Para emails, anúncios, social: títulos menos relevantes
        score += 20 if heading_count >= 1 else 15

    # --- Proxy de comprimento de meta description (25 pontos) ---
    # Verifica meta description no front-matter ou primeiro parágrafo
    max_possible += 25
    meta_match = re.search(r"meta[_-]?description[:\s]+[\"']?(.+?)[\"']?\s*$",
                           text, re.MULTILINE | re.IGNORECASE)
    first_para = text.strip().split("\n\n")[0] if text.strip() else ""
    first_para_len = len(first_para)

    if meta_match:
        meta_len = len(meta_match.group(1).strip())
        details["meta_description_length"] = meta_len
        if 120 <= meta_len <= 160:
            score += 25
        elif 80 <= meta_len <= 200:
            score += 15
            recommendations.append(
                f"Meta description tem {meta_len} caracteres. "
                "O ideal é 120-160 caracteres."
            )
        else:
            score += 5
            recommendations.append(
                f"Meta description tem {meta_len} caracteres — "
                "fora da faixa recomendada de 120-160."
            )
    else:
        details["meta_description"] = "Não encontrada"
        if content_type in ("blog", "landing_page"):
            # Usa o primeiro parágrafo como proxy
            if 120 <= first_para_len <= 200:
                score += 15
                details["first_paragraph_length"] = first_para_len
            else:
                score += 5
                recommendations.append(
                    "Meta description não encontrada. Adicione uma (120-160 chars) para "
                    "os snippets de resultados de busca."
                )
        else:
            score += 20  # Menos relevante para conteúdo não-web

    # Normaliza para 0-100
    final_score = (score / max(max_possible, 1)) * 100 if max_possible else 50

    return {
        "score": round(min(max(final_score, 0), 100), 2),
        "details": details,
        "recommendations": recommendations,
    }


def score_structure(text: str, content_type: str) -> dict:
    """Pontua estrutura do conteúdo de 0-100 (parágrafos, títulos, listas)."""
    score = 0.0
    recommendations = []

    # Parágrafos
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    para_count = len(paragraphs)

    # Títulos
    headings = re.findall(r"^#{1,6}\s+", text, re.MULTILINE)
    html_headings = re.findall(r"<h[1-6]", text, re.IGNORECASE)
    heading_count = len(headings) + len(html_headings)

    # Listas (markdown ou HTML)
    md_list_items = re.findall(r"^[\s]*[-*+]\s+", text, re.MULTILINE)
    md_numbered_items = re.findall(r"^[\s]*\d+[.)]\s+", text, re.MULTILINE)
    html_list_items = re.findall(r"<li", text, re.IGNORECASE)
    list_item_count = len(md_list_items) + len(md_numbered_items) + len(html_list_items)

    # Uso de negrito/ênfase
    bold_count = len(re.findall(r"\*\*[^*]+\*\*", text))
    bold_count += len(re.findall(r"__[^_]+__", text))
    bold_count += len(re.findall(r"<strong>", text, re.IGNORECASE))
    bold_count += len(re.findall(r"<b>", text, re.IGNORECASE))

    details = {
        "paragraph_count": para_count,
        "heading_count": heading_count,
        "list_item_count": list_item_count,
        "bold_emphasis_count": bold_count,
    }

    # --- Lógica de pontuação por tipo de conteúdo ---
    if content_type == "blog":
        # Parágrafos: esperamos múltiplos parágrafos, não muito longos
        if para_count >= 5:
            score += 25
        elif para_count >= 3:
            score += 15
        else:
            score += 5
            recommendations.append(
                "Blog tem poucos parágrafos. Divida o conteúdo em mais "
                "parágrafos para facilitar a leitura."
            )

        # Verifica parágrafos tipo "parede de texto"
        long_paras = [p for p in paragraphs if len(_split_words(p)) > 100]
        if long_paras:
            score -= 5
            recommendations.append(
                f"{len(long_paras)} parágrafo(s) excedem 100 palavras. "
                "Quebre-os para melhorar a legibilidade."
            )

        # Títulos
        if heading_count >= 3:
            score += 25
        elif heading_count >= 1:
            score += 15
            recommendations.append("Adicione mais subtítulos para melhorar a escaneabilidade.")
        else:
            recommendations.append("Nenhum título encontrado. Adicione subtítulos H2/H3.")

        # Listas
        if list_item_count >= 3:
            score += 25
        elif list_item_count >= 1:
            score += 15
        else:
            score += 5
            recommendations.append(
                "Considere adicionar marcadores ou listas numeradas para "
                "destacar informações-chave."
            )

        # Ênfase
        if bold_count >= 2:
            score += 25
        elif bold_count >= 1:
            score += 15
        else:
            score += 5
            recommendations.append(
                "Use negrito para destacar frases-chave e melhorar a escaneabilidade."
            )

    elif content_type == "email":
        if para_count >= 2:
            score += 30
        else:
            score += 15
        if list_item_count >= 1:
            score += 25
        else:
            score += 15
        # Emails não precisam de muitos títulos
        score += 25
        if bold_count >= 1:
            score += 20
        else:
            score += 10
            recommendations.append("Use negrito em frases-chave para atrair o olhar do leitor.")

    elif content_type == "ad":
        # Anúncios são curtos — menos estrutura necessária
        if para_count >= 1:
            score += 30
        score += 30  # Títulos/listas menos relevantes
        if bold_count >= 1:
            score += 20
        score += 20

    elif content_type == "landing_page":
        if para_count >= 3:
            score += 20
        else:
            score += 10
            recommendations.append("Adicione mais seções de conteúdo à landing page.")
        if heading_count >= 3:
            score += 25
        elif heading_count >= 1:
            score += 15
            recommendations.append(
                "Landing pages se beneficiam de múltiplos títulos. Adicione mais H2s."
            )
        else:
            recommendations.append("Adicione títulos para estruturar a landing page.")
        if list_item_count >= 2:
            score += 25
        else:
            score += 10
            recommendations.append(
                "Adicione listas de funcionalidades ou benefícios à landing page."
            )
        if bold_count >= 2:
            score += 30
        elif bold_count >= 1:
            score += 20
        else:
            score += 5
            recommendations.append("Use negrito para destacar propostas de valor-chave.")

    elif content_type == "social":
        if para_count >= 1:
            score += 40
        score += 30  # Structure is minimal for social
        if list_item_count >= 1 or bold_count >= 1:
            score += 30
        else:
            score += 20

    return {
        "score": round(min(max(score, 0), 100), 2),
        "details": details,
        "recommendations": recommendations,
    }


def score_cta(text: str, content_type: str) -> dict:
    """Pontua qualidade do CTA (Call to Action) de 0-100."""
    text_lower = text.lower()
    recommendations = []

    # Encontra todos os CTAs
    ctas_found = []
    for pattern in CTA_PATTERNS:
        matches = re.finditer(pattern, text_lower)
        for m in matches:
            ctas_found.append(m.group(0))
    ctas_found = list(set(ctas_found))  # deduplicate

    cta_count = len(ctas_found)

    # Classifica CTAs como fortes ou fracos
    strong = [c for c in ctas_found
              if any(sv in c for sv in CTA_STRONG_VERBS)]
    weak = [c for c in ctas_found if c not in strong]

    details = {
        "ctas_found": ctas_found,
        "cta_count": cta_count,
        "strong_ctas": strong,
        "weak_ctas": weak,
    }

    # --- Pontuação ---
    score = 0.0

    # Quantidade ideal de CTAs por tipo de conteúdo
    ideal_cta = {
        "blog": (1, 3),
        "email": (1, 2),
        "ad": (1, 2),
        "landing_page": (2, 5),
        "social": (1, 1),
    }
    lo, hi = ideal_cta.get(content_type, (1, 3))

    if cta_count == 0:
        score = 0
        recommendations.append(
            "Nenhum call to action encontrado. Todo conteúdo de marketing "
            "deve incluir pelo menos um CTA claro."
        )
    elif lo <= cta_count <= hi:
        score += 50
    elif cta_count < lo:
        score += 25
        recommendations.append(
            f"Apenas {cta_count} CTA encontrado. Considere adicionar "
            f"{'outro' if cta_count == 1 else 'mais'} para um {content_type}."
        )
    else:
        score += 30
        recommendations.append(
            f"{cta_count} CTAs detectados — pode ser demais para {content_type}. "
            f"O ideal é {lo}-{hi}. Muitos CTAs podem diluir o impacto."
        )

    # Fortes vs fracos
    if strong:
        score += 30
    elif weak:
        score += 15
        recommendations.append(
            "CTAs usam verbos fracos (ex: 'learn more'). "
            "Considere verbos de ação mais fortes como 'Começar agora', 'Baixar', 'Cadastrar'."
        )

    # Posicionamento do CTA: verifica se aparece próximo ao final
    if ctas_found:
        # Verifica os últimos 20% do texto em busca de um CTA
        cutoff = int(len(text_lower) * 0.8)
        last_portion = text_lower[cutoff:]
        cta_near_end = any(c in last_portion for c in ctas_found)
        details["cta_near_end"] = cta_near_end
        if cta_near_end:
            score += 20
        else:
            score += 5
            recommendations.append(
                "Nenhum CTA encontrado próximo ao final do conteúdo. "
                "Coloque seu CTA principal onde os leitores terminam de ler."
            )
    else:
        details["cta_near_end"] = False

    return {
        "score": round(min(max(score, 0), 100), 2),
        "details": details,
        "recommendations": recommendations,
    }


def score_spam_filler(text: str) -> dict:
    """Pontua conteúdo quanto ao uso de spam/preenchimento. Maior = mais limpo."""
    text_lower = text.lower()
    words = _split_words(text)
    word_count = len(words)
    recommendations = []

    # Detecção de palavras de spam
    spam_found = []
    for phrase in SPAM_WORDS:
        if phrase in text_lower:
            spam_found.append(phrase)
    # Verifica uso excessivo de exclamações
    excl_count = text.count("!")
    excl_sequences = len(re.findall(r"!{2,}", text))

    # Detecção de palavras de preenchimento
    filler_found = []
    for phrase in FILLER_WORDS:
        if " " in phrase:
            count = text_lower.count(phrase)
            if count > 0:
                filler_found.append({"phrase": phrase, "count": count})
        else:
            tokens_lower = [w.lower() for w in words]
            count = tokens_lower.count(phrase)
            if count > 0:
                filler_found.append({"phrase": phrase, "count": count})

    total_filler_count = sum(f["count"] for f in filler_found)
    filler_pct = round((total_filler_count / max(word_count, 1)) * 100, 2)

    # Palavras em MAIÚSCULAS (gritar)
    caps_words = [w for w in text.split() if w.isupper() and len(w) > 2
                  and w.isalpha()]

    details = {
        "spam_phrases_found": spam_found,
        "spam_count": len(spam_found),
        "filler_words_found": sorted(filler_found, key=lambda x: x["count"],
                                     reverse=True)[:10],
        "filler_word_pct": filler_pct,
        "exclamation_marks": excl_count,
        "consecutive_exclamation_sequences": excl_sequences,
        "all_caps_words": caps_words[:10],
        "all_caps_count": len(caps_words),
    }

    # --- Pontuação (começa em 100, subtrai) ---
    score = 100.0

    # Penalidades de spam
    score -= len(spam_found) * 8
    if spam_found:
        recommendations.append(
            f"Palavras de spam detectadas: {', '.join(spam_found[:5])}. "
            "Podem prejudicar a entregabilidade de emails e aprovação de anúncios."
        )

    # Penalidades de preenchimento
    if filler_pct > 8:
        score -= 20
        recommendations.append(
            f"Alto uso de palavras de preenchimento ({filler_pct}%). "
            "Remova qualificadores desnecessários como 'very', 'really', 'just'."
        )
    elif filler_pct > 4:
        score -= 10
        recommendations.append(
            f"Uso moderado de palavras de preenchimento ({filler_pct}%). "
            "Considere condensar o texto."
        )

    # Penalidades de exclamação
    if excl_sequences > 0:
        score -= excl_sequences * 5
        recommendations.append(
            "Múltiplas exclamações consecutivas detectadas. "
            "Use no máximo uma exclamação por vez."
        )
    if excl_count > 3:
        score -= (excl_count - 3) * 2
        recommendations.append(
            f"{excl_count} pontos de exclamação encontrados. "
            "Excesso de exclamações reduz a credibilidade."
        )

    # Penalidades de MAIÚSCULAS
    if len(caps_words) > 2:
        score -= len(caps_words) * 3
        recommendations.append(
            f"{len(caps_words)} palavras em MAIÚSCULAS encontradas. "
            "Evite 'gritar' — parece spam."
        )

    if not recommendations:
        recommendations.append("Conteúdo limpo — nenhum spam ou preenchimento significativo detectado.")

    return {
        "score": round(min(max(score, 0), 100), 2),
        "details": details,
        "recommendations": recommendations,
    }


def score_length(text: str, content_type: str) -> dict:
    """Pontua adequação do comprimento do conteúdo de 0-100."""
    words = _split_words(text)
    word_count = len(words)
    recommendations = []

    lo, hi = IDEAL_WORD_COUNTS.get(content_type, (100, 1500))

    details = {
        "word_count": word_count,
        "ideal_range": [lo, hi],
    }

    if lo <= word_count <= hi:
        score = 100.0
    elif word_count < lo:
        ratio = word_count / max(lo, 1)
        score = max(ratio * 100, 0)
        recommendations.append(
            f"Conteúdo muito curto ({word_count} palavras) para {content_type}. "
            f"A faixa ideal é {lo}-{hi} palavras."
        )
    else:
        # Acima do máximo — penalidade suave
        overage_ratio = (word_count - hi) / max(hi, 1)
        score = max(100 - overage_ratio * 80, 20)
        recommendations.append(
            f"Conteúdo longo ({word_count} palavras) para {content_type}. "
            f"A faixa ideal é {lo}-{hi} palavras. Considere cortar."
        )

    return {
        "score": round(min(max(score, 0), 100), 2),
        "details": details,
        "recommendations": recommendations,
    }


# ---------------------------------------------------------------------------
# Main scoring pipeline
# ---------------------------------------------------------------------------

def score_content(text: str, content_type: str, keyword: str | None) -> dict:
    """Executa o pipeline completo de pontuação multidimensional."""
    if not text or not text.strip():
        return {
            "error": "Texto vazio fornecido. Forneça conteúdo para analisar.",
            "overall_score": 0,
        }

    if content_type not in CONTENT_TYPE_WEIGHTS:
        return {
            "error": f"Tipo de conteúdo desconhecido: '{content_type}'",
            "valid_types": list(CONTENT_TYPE_WEIGHTS.keys()),
        }

    weights = CONTENT_TYPE_WEIGHTS[content_type]

    # Executa o pontuador de cada dimensão
    readability = score_readability(text, content_type)
    seo = score_seo(text, keyword, content_type)
    structure = score_structure(text, content_type)
    cta = score_cta(text, content_type)
    spam_filler = score_spam_filler(text)
    length = score_length(text, content_type)

    dimensions = {
        "readability": readability,
        "seo": seo,
        "structure": structure,
        "cta": cta,
        "spam_filler": spam_filler,
        "length": length,
    }

    # Calcula pontuação geral ponderada
    overall = 0.0
    for dim_name, dim_result in dimensions.items():
        w = weights.get(dim_name, 0)
        overall += dim_result["score"] * w

    overall = round(min(max(overall, 0), 100), 2)

    # Coleta todas as recomendações ordenadas por peso de dimensão (mais impactantes primeiro)
    all_recommendations = []
    for dim_name in sorted(weights, key=weights.get, reverse=True):
        dim = dimensions[dim_name]
        for rec in dim.get("recommendations", []):
            all_recommendations.append({
                "dimension": dim_name,
                "weight": weights[dim_name],
                "recommendation": rec,
            })

    # Estatísticas resumidas
    sentences = sent_tokenize(text)
    words = _split_words(text)
    stats = {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_sentence_length": (
            round(len(words) / len(sentences), 1) if sentences else 0
        ),
        "content_type": content_type,
        "keyword": keyword or "N/A",
    }

    return {
        "overall_score": overall,
        "interpretation": _interpret_score(overall),
        "weights_used": weights,
        "dimension_scores": {
            name: {
                "score": dim["score"],
                "weight": weights.get(name, 0),
                "weighted_contribution": round(
                    dim["score"] * weights.get(name, 0), 2
                ),
            }
            for name, dim in dimensions.items()
        },
        "dimension_details": dimensions,
        "top_recommendations": all_recommendations[:10],
        "stats": stats,
    }


def _interpret_score(score: float) -> str:
    """Retorne uma interpretação legível do escore geral."""
    if score >= 90:
        return "Excelente — conteúdo pronto para publicação"
    elif score >= 75:
        return "Bom — melhorias menores recomendadas"
    elif score >= 60:
        return "Aceitável — vários áreas precisam atenção"
    elif score >= 40:
        return "Pobre — revisão significativa necessária"
    else:
        return "Crítico — reescrita maior recomendada"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pontuação de qualidade de conteúdo multidimensional.",
        epilog=(
            "Tipos de conteúdo: blog, email, ad, landing_page, social\n\n"
            "Exemplo:\n"
            '  python avaliador-conteudo.py --file post.md --type blog --keyword "ferramentas IA"'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--text", type=str,
        help="Texto de conteúdo para analisar (inline).",
    )
    input_group.add_argument(
        "--file", type=str,
        help="Caminho para um arquivo contendo conteúdo para analisar.",
    )
    parser.add_argument(
        "--type", dest="content_type", required=True,
        choices=list(CONTENT_TYPE_WEIGHTS.keys()),
        help="Tipo de conteúdo de marketing.",
    )
    parser.add_argument(
        "--keyword", type=str, default=None,
        help="Palavra-chave SEO primária para verificar (opcional).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Resolve texto de entrada
    if args.text:
        text = args.text
    else:
        file_path = Path(args.file)
        if not file_path.exists():
            print(json.dumps({
                "error": f"Arquivo não encontrado: {file_path}",
            }, indent=2))
            sys.exit(1)
        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception as exc:
            print(json.dumps({
                "error": f"Não foi possível ler arquivo: {exc}",
            }, indent=2))
            sys.exit(1)

    # Pontua
    result = score_content(text, args.content_type, args.keyword)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
