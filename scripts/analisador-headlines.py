#!/usr/bin/env python3
"""Pontue headlines por impacto emocional, palavras poderosas e efetividade estrutural."""

import argparse
import json
import math
import re
import sys
from pathlib import Path

POWER_WORDS = {
    "absolutely", "amazing", "astonishing", "breakthrough", "captivating",
    "compelling", "controversial", "crushing", "dangerous", "deadly",
    "devastating", "discover", "dominate", "epic", "essential", "exclusive",
    "explosive", "extraordinary", "forbidden", "free", "guaranteed",
    "hack", "hidden", "horrifying", "huge", "immediately", "incredible",
    "insane", "instant", "jaw-dropping", "killer", "legendary", "life-changing",
    "limited", "massive", "mind-blowing", "miracle", "must-have", "never",
    "nightmare", "now", "outrageous", "powerful", "proven", "rare",
    "revolutionary", "secret", "sensational", "shocking", "stunning",
    "supercharge", "surprising", "ultimate", "unbelievable", "unconventional",
    "unexpected", "unleash", "unprecedented", "unstoppable", "urgent",
    "vital", "warning", "weird",
}

EMOTIONAL_WORDS = {
    "positive": {
        "love", "joy", "happy", "amazing", "beautiful", "brilliant", "celebrate",
        "delight", "dream", "exciting", "fantastic", "grateful", "inspire",
        "laugh", "magic", "passion", "perfect", "smile", "success", "triumph",
        "wonderful", "worthy", "thriving", "bliss", "hope", "win",
    },
    "negative": {
        "afraid", "angry", "anxiety", "awful", "broken", "crisis", "danger",
        "dark", "dead", "destroy", "devastating", "disaster", "fail", "fear",
        "hate", "horrible", "hurt", "kill", "lonely", "loss", "mistake",
        "nightmare", "pain", "panic", "regret", "risk", "sad", "scam",
        "scary", "struggle", "suffer", "terrible", "threat", "toxic", "trap",
        "ugly", "victim", "warning", "worry", "worst",
    },
}

COMMON_WORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her",
    "she", "or", "an", "will", "my", "one", "all", "would", "there",
    "their", "what", "so", "up", "out", "if", "about", "who", "get",
    "which", "go", "me", "when", "make", "can", "like", "time", "no",
    "just", "him", "know", "take", "people", "into", "year", "your",
    "good", "some", "could", "them", "see", "other", "than", "then",
    "now", "look", "only", "come", "its", "over", "think", "also",
}

HEADLINE_PATTERNS = {
    "how-to": r"^how\s+to\b",
    "listicle": r"^\d+\s",
    "question": r"\?$",
    "why": r"^why\b",
    "what": r"^what\b",
    "guide": r"\bguide\b|\bcomplete\b|\bultimate\b",
    "negative": r"\bnever\b|\bstop\b|\bavoid\b|\bdon'?t\b|\bwithout\b|\bworst\b",
    "command": r"^(start|stop|get|try|use|make|do|build|create|learn|find|read)\b",
}


def estimate_reading_grade(text):
    """Estimativa simplificada de nível de série Flesch-Kincaid."""
    words = text.split()
    word_count = len(words)
    if word_count == 0:
        return 0.0
    # Estima frases (headlines são geralmente 1 frase)
    sentence_count = max(1, text.count(".") + text.count("!") + text.count("?"))
    if sentence_count == 0:
        sentence_count = 1
    # Conta sílabas (estimativa aproximada)
    syllable_count = 0
    for word in words:
        word = re.sub(r"[^a-zA-Z]", "", word.lower())
        if not word:
            continue
        count = 0
        vowels = "aeiouy"
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith("e") and count > 1:
            count -= 1
        count = max(1, count)
        syllable_count += count

    grade = 0.39 * (word_count / sentence_count) + 11.8 * (syllable_count / word_count) - 15.59
    return round(max(0, grade), 1)


def analyze_headline(headline):
    """Analise um único headline e retorne métricas de pontuação."""
    if not headline or not headline.strip():
        return {"error": "Headline vazio"}

    headline = headline.strip()
    words = re.findall(r"[a-zA-Z']+", headline)
    word_count = len(words)
    char_count = len(headline)
    words_lower = [w.lower() for w in words]

    # Análise de palavras de impacto
    power_found = [w for w in words_lower if w in POWER_WORDS]
    power_count = len(power_found)

    # Análise emocional
    pos_found = [w for w in words_lower if w in EMOTIONAL_WORDS["positive"]]
    neg_found = [w for w in words_lower if w in EMOTIONAL_WORDS["negative"]]
    emotional_count = len(pos_found) + len(neg_found)

    # Sentimento
    if len(pos_found) > len(neg_found):
        sentiment = "positive"
    elif len(neg_found) > len(pos_found):
        sentiment = "negative"
    else:
        sentiment = "neutral"

    # Proporção de palavras comuns e incomuns
    common_count = sum(1 for w in words_lower if w in COMMON_WORDS)
    uncommon_count = word_count - common_count
    common_pct = round((common_count / max(word_count, 1)) * 100, 1)
    uncommon_pct = round((uncommon_count / max(word_count, 1)) * 100, 1)

    # Detecção de tipo de headline
    headline_lower = headline.lower()
    detected_types = []
    for htype, pattern in HEADLINE_PATTERNS.items():
        if re.search(pattern, headline_lower, re.IGNORECASE):
            detected_types.append(htype)
    if not detected_types:
        detected_types = ["statement"]

    # Nível de leitura
    reading_grade = estimate_reading_grade(headline)

    # Pontuação emocional (0-100)
    emotional_score = min(100, int(
        (power_count * 15) +
        (emotional_count * 12) +
        (10 if word_count >= 6 and word_count <= 12 else 0) +
        (10 if char_count >= 40 and char_count <= 70 else 0) +
        (8 if any(c in headline for c in "!?") else 0) +
        (8 if re.match(r"^\d", headline) else 0) +
        (5 if uncommon_pct >= 30 else 0)
    ))

    # Avisos
    warnings = []
    if word_count < 4:
        warnings.append("Headline pode ser muito curto (< 4 palavras)")
    if word_count > 15:
        warnings.append("Headline pode ser muito longo (> 15 palavras)")
    if char_count > 70:
        warnings.append("Pode ser truncado em Google SERPs (> 70 chars)")
    if power_count == 0:
        warnings.append("Nenhuma palavra poderosa detectada; considere adicionar uma")
    if headline[0].islower():
        warnings.append("Headline não começa com letra maiúscula")

    return {
        "headline": headline,
        "word_count": word_count,
        "character_count": char_count,
        "emotional_score": emotional_score,
        "power_word_count": power_count,
        "power_words_found": power_found,
        "emotional_words_found": {"positive": pos_found, "negative": neg_found},
        "common_word_pct": common_pct,
        "uncommon_word_pct": uncommon_pct,
        "reading_grade_level": reading_grade,
        "sentiment": sentiment,
        "headline_types": detected_types,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="Pontue headlines por impacto emocional e efetividade")
    parser.add_argument("--headline", help="Único headline para analisar")
    parser.add_argument("--file", help="Arquivo com um headline por linha")
    args = parser.parse_args()

    if not args.headline and not args.file:
        parser.error("Forneça --headline ou --file")

    headlines = []
    if args.headline:
        headlines = [args.headline]
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            print(json.dumps({"error": f"Arquivo não encontrado: {args.file}"}))
            sys.exit(1)
        headlines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    if not headlines:
        print(json.dumps({"error": "Nenhum headline fornecido"}))
        sys.exit(1)

    results = [analyze_headline(h) for h in headlines]

    if len(results) == 1:
        output = results[0]
    else:
        scores = [r.get("emotional_score", 0) for r in results if "error" not in r]
        output = {
            "total_headlines": len(results),
            "average_emotional_score": round(sum(scores) / max(len(scores), 1), 1),
            "best_headline": max(results, key=lambda r: r.get("emotional_score", 0)).get("headline", ""),
            "results": results,
        }

    json.dump(output, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
