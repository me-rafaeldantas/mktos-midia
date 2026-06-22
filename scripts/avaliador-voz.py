#!/usr/bin/env python3
"""
avaliador-voz.py
=====================
Avalia conteúdo contra um perfil de voz de marca.

Lê um perfil de voz de marca de ./data/clientes/{slug}/perfil.json,
analisa conteúdo de texto em múltiplas dimensões de voz e retorna uma pontuação
de consistência de voz (0-100) com detalhamento por dimensão e desvios específicos.

Dependências: nltk, json, sys, pathlib, argparse

Uso:
    python avaliador-voz.py --brand acme --text "Check out our amazing product!"
    python avaliador-voz.py --brand acme --file content.txt

Schema JSON do Perfil do Cliente (perfil.json — de gerenciar-contas.py / /mktos:configurar):
    {
        "brand_name": "Acme Corp",
        "brand_voice": {
            "formality": 7,         // 1 (muito casual) a 10 (muito formal)
            "energy": 5,            // 1 (calmo/reservado) a 10 (alta-energia/empolgado)
            "humor": 2,             // 1 (sério) a 10 (humorístico)
            "authority": 8,         // 1 (nível de pares) a 10 (autoritário/especialista)
            "personality_traits": ["confident", "precise"],
            "tone_keywords": ["innovative", "reliable"],
            "avoid_words": ["cheap", "basically", "honestly"],
            "prefer_words": ["innovative", "reliable", "precision"],
            "this_not_that": [["cheap", "affordable"], ["buy", "invest in"]],
            "sample_content": []
        }
    }

    Também suporta schema direto legado:
    {
        "voice_dimensions": {"formality": 0.7, "energy": 0.5, ...},
        "preferred_words": [...], "avoided_words": [...]
    }
"""

import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# NLTK bootstrap — download the required data silently on first run
# ---------------------------------------------------------------------------
try:
    import nltk
except ImportError:
    print(json.dumps({
        "fallback": True,
        "error": "nltk_not_installed",
        "message": "NLTK não instalado. Avaliação de voz requer: pip install nltk",
        "overall_score": None,
        "recommendation": "Instale NLTK para avaliação automatizada, ou revise manualmente contra diretrizes de voz de marca."
    }, indent=2))
    sys.exit(0)

# Ensure tokenizer models are available
for _res in ("punkt", "punkt_tab", "averaged_perceptron_tagger",
             "averaged_perceptron_tagger_eng"):
    try:
        nltk.data.find(f"tokenizers/{_res}" if "punkt" in _res
                       else f"taggers/{_res}")
    except LookupError:
        nltk.download(_res, quiet=True)

from nltk.tokenize import sent_tokenize, word_tokenize

# ---------------------------------------------------------------------------
# Constants & indicator word-lists
# ---------------------------------------------------------------------------

# Words / patterns that signal HIGH formality
FORMAL_INDICATORS = {
    "furthermore", "consequently", "nevertheless", "therefore", "moreover",
    "accordingly", "henceforth", "hereby", "herein", "notwithstanding",
    "pursuant", "regarding", "respectively", "subsequently", "thus",
    "whereas", "whereby", "wherein", "utilise", "utilize", "facilitate",
    "implement", "demonstrate", "constitute", "acknowledge", "endeavor",
    "commence", "terminate", "prior", "subsequent", "sufficient",
    "considerable", "significant", "appropriate", "approximately",
    "establish", "determine", "indicate", "obtain", "provide", "require",
    "shall", "must", "ensure",
}

# Words / patterns that signal LOW formality (casual)
CASUAL_INDICATORS = {
    "hey", "hi", "yo", "gonna", "gotta", "wanna", "kinda", "sorta",
    "yeah", "yep", "nope", "cool", "awesome", "amazing", "literally",
    "basically", "honestly", "totally", "super", "stuff", "thing",
    "things", "lots", "tons", "bunch", "guys", "dude", "lol", "omg",
    "btw", "fyi", "tbh", "imo", "imho", "ok", "okay", "chill",
    "vibe", "vibes", "fam", "bro",
}

# High-energy words
HIGH_ENERGY_WORDS = {
    "exciting", "incredible", "amazing", "fantastic", "extraordinary",
    "revolutionary", "breakthrough", "transformative", "game-changing",
    "explosive", "unstoppable", "phenomenal", "spectacular", "stunning",
    "thrilling", "electrifying", "dynamic", "powerful", "turbocharge",
    "skyrocket", "supercharge", "unleash", "ignite", "amplify", "crush",
    "dominate", "epic", "insane", "wild", "massive", "huge", "unbelievable",
}

# Calm / reserved words
CALM_WORDS = {
    "steady", "measured", "considered", "thoughtful", "deliberate",
    "careful", "gradual", "consistent", "reliable", "sustainable",
    "balanced", "moderate", "stable", "calm", "quiet", "gentle",
    "subtle", "understated", "nuanced", "refined",
}

# Humor indicators
HUMOR_INDICATORS = {
    "lol", "haha", "hehe", "rofl", "lmao", "😂", "🤣", "😄", "😆",
    "joke", "jokes", "joking", "kidding", "pun", "puns", "funny",
    "hilarious", "witty", "tongue-in-cheek",
}

# Exclamation marks and emoji also raise energy / humor signals
EXCLAMATION_WEIGHT = 0.02  # per exclamation mark
QUESTION_WEIGHT = 0.005

# Authority indicators
AUTHORITY_INDICATORS = {
    "proven", "research", "data", "evidence", "study", "studies",
    "expert", "expertise", "authority", "definitive", "comprehensive",
    "analysis", "framework", "methodology", "strategy", "strategic",
    "insight", "insights", "benchmark", "best-practice", "best practice",
    "proprietary", "patent", "certified", "decade", "decades", "years",
    "experience", "track record", "industry-leading", "peer-reviewed",
    "published", "demonstrated", "validated", "verified",
}

# Peer-level / humble indicators
PEER_INDICATORS = {
    "we think", "in our opinion", "we believe", "maybe", "perhaps",
    "might", "could", "possibly", "it seems", "from our perspective",
    "we feel", "just", "simply", "honestly", "in our experience",
    "we've found", "we've noticed",
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def normalize_profile(profile: dict) -> dict:
    """Normaliza o perfil de marca para o formato interno do avaliador.

    Suporta dois schemas:
    - Schema completo (de gerenciar-contas.py / /mktos:configurar) com objeto brand_voice aninhado
      e escalas inteiras de 1-10
    - Schema legado direto com voice_dimensions (floats 0.0-1.0) no nível raiz
    """
    normalized = dict(profile)

    brand_voice = profile.get("brand_voice", {})
    if brand_voice and "voice_dimensions" not in profile:
        # Converte escala 1-10 do setup.py para escala 0.0-1.0
        normalized["voice_dimensions"] = {
            "formality": brand_voice.get("formality", 5) / 10.0,
            "energy": brand_voice.get("energy", 5) / 10.0,
            "humor": brand_voice.get("humor", 3) / 10.0,
            "authority": brand_voice.get("authority", 5) / 10.0,
        }
        # Mapeia nomes de campos: prefer_words → preferred_words, avoid_words → avoided_words
        if "preferred_words" not in normalized:
            normalized["preferred_words"] = brand_voice.get("prefer_words", [])
        if "avoided_words" not in normalized:
            normalized["avoided_words"] = brand_voice.get("avoid_words", [])
        # Preserva tone keywords como contexto de notas
        tone = brand_voice.get("tone_keywords", [])
        if tone and "notes" not in normalized:
            normalized["notes"] = f"Palavras-chave de tom: {', '.join(tone)}"

    return normalized


def load_brand_profile(slug: str) -> dict:
    """Carrega um perfil JSON de voz de marca da localização padrão."""
    profile_path = Path(__file__).parent.parent / "data" / "clientes" / slug / "perfil.json"
    if not profile_path.exists():
        return {
            "error": f"Perfil do cliente não encontrado em {profile_path}",
            "hint": (
                "Crie um perfil.json no caminho acima. "
                "Execute /mktos:configurar para criar um interativamente."
            ),
        }
    try:
        with open(profile_path, "r", encoding="utf-8") as fh:
            profile = json.load(fh)
    except json.JSONDecodeError as exc:
        return {"error": f"JSON inválido em {profile_path}: {exc}"}
    return normalize_profile(profile)


def _count_matches(tokens_lower: list[str], word_set: set[str]) -> int:
    """Conta quantos tokens aparecem no conjunto dado."""
    return sum(1 for t in tokens_lower if t in word_set)


def _bigram_matches(text_lower: str, phrase_set: set[str]) -> int:
    """Conta correspondências de nível de frase que podem conter espaços."""
    return sum(1 for phrase in phrase_set if " " in phrase and phrase in text_lower)


def analyze_formality(tokens_lower: list[str], text_lower: str) -> float:
    """Retorna uma pontuação de formalidade entre 0.0 (casual) e 1.0 (formal)."""
    if not tokens_lower:
        return 0.5
    formal_hits = _count_matches(tokens_lower, FORMAL_INDICATORS)
    casual_hits = _count_matches(tokens_lower, CASUAL_INDICATORS)
    total = formal_hits + casual_hits
    if total == 0:
        return 0.5  # neutral
    return round(formal_hits / total, 4)


def analyze_energy(tokens_lower: list[str], text: str) -> float:
    """Retorna uma pontuação de energia entre 0.0 (calmo) e 1.0 (alta-energia)."""
    if not tokens_lower:
        return 0.5
    high_hits = _count_matches(tokens_lower, HIGH_ENERGY_WORDS)
    calm_hits = _count_matches(tokens_lower, CALM_WORDS)
    exclamation_boost = text.count("!") * EXCLAMATION_WEIGHT
    caps_words = sum(1 for t in text.split() if t.isupper() and len(t) > 1)
    caps_boost = min(caps_words * 0.01, 0.15)
    total = high_hits + calm_hits
    if total == 0:
        base = 0.5
    else:
        base = high_hits / total
    score = base + exclamation_boost + caps_boost
    return round(min(max(score, 0.0), 1.0), 4)


def analyze_humor(tokens_lower: list[str], text_lower: str) -> float:
    """Retorna uma pontuação de humor entre 0.0 (sério) e 1.0 (humorístico)."""
    if not tokens_lower:
        return 0.0
    humor_hits = _count_matches(tokens_lower, HUMOR_INDICATORS)
    # Also check for multi-word humor indicators
    humor_hits += _bigram_matches(text_lower, HUMOR_INDICATORS)
    # Normalize: even a few humor markers in short text is notable
    ratio = humor_hits / max(len(tokens_lower), 1)
    # Scale so that ~5% humor words => score of ~1.0
    score = min(ratio * 20, 1.0)
    return round(score, 4)


def analyze_authority(tokens_lower: list[str], text_lower: str) -> float:
    """Retorna uma pontuação de autoridade entre 0.0 (par) e 1.0 (autoritário)."""
    if not tokens_lower:
        return 0.5
    auth_hits = _count_matches(tokens_lower, AUTHORITY_INDICATORS)
    auth_hits += _bigram_matches(text_lower, AUTHORITY_INDICATORS)
    peer_hits = _bigram_matches(text_lower, PEER_INDICATORS)
    peer_hits += _count_matches(tokens_lower, PEER_INDICATORS)
    total = auth_hits + peer_hits
    if total == 0:
        return 0.5
    return round(auth_hits / total, 4)


def check_word_lists(tokens_lower: list[str], preferred: list[str],
                     avoided: list[str]) -> dict:
    """Verifica uso de palavras preferidas e evitadas."""
    preferred_lower = {w.lower() for w in preferred}
    avoided_lower = {w.lower() for w in avoided}

    preferred_found = sorted(preferred_lower & set(tokens_lower))
    preferred_missing = sorted(preferred_lower - set(tokens_lower))
    avoided_found = sorted(avoided_lower & set(tokens_lower))

    return {
        "preferred_found": preferred_found,
        "preferred_missing": preferred_missing,
        "avoided_found": avoided_found,
        "preferred_usage_ratio": (
            round(len(preferred_found) / len(preferred_lower), 4)
            if preferred_lower else 1.0
        ),
        "avoided_violation_count": len(avoided_found),
    }


def dimension_distance(actual: float, target: float) -> float:
    """Distância absoluta entre atual e alvo (ambos 0-1)."""
    return abs(actual - target)


def score_from_distance(distance: float) -> float:
    """Converte uma distância 0-1 para uma pontuação 0-100 (mais próximo = maior)."""
    return round((1.0 - distance) * 100, 2)


def generate_deviations(dimension_scores: dict, profile: dict) -> list[dict]:
    """Gera descrições de desvios legíveis."""
    deviations = []
    targets = profile.get("voice_dimensions", {})

    labels = {
        "formality": ("casual", "formal"),
        "energy": ("calmo/reservado", "alta-energia/empolgado"),
        "humor": ("sério", "humorístico"),
        "authority": ("nível de pares", "autoritário/especialista"),
    }

    for dim, info in dimension_scores.items():
        dist = info["distance"]
        if dist > 0.15:  # threshold for flagging
            target = targets.get(dim, 0.5)
            actual = info["actual"]
            low_label, high_label = labels.get(dim, ("low", "high"))
            direction = high_label if actual > target else low_label
            target_dir = high_label if target > 0.5 else low_label
            deviations.append({
                "dimension": dim,
                "severity": "high" if dist > 0.35 else "medium",
                "message": (
                    f"Conteúdo lê como muito {direction} "
                    f"(atual={actual:.2f}, alvo={target:.2f}). "
                    f"Voz de marca pede por tom mais {target_dir}."
                ),
            })
    return deviations


# ---------------------------------------------------------------------------
# Main scoring pipeline
# ---------------------------------------------------------------------------

def score_content(text: str, profile: dict) -> dict:
    """Executa o pipeline de avaliação de voz de marca completo e retorna dict de resultados."""
    if not text or not text.strip():
        return {
            "error": "Texto vazio fornecido. Forneça conteúdo para analisar.",
            "score": 0,
        }

    targets = profile.get("voice_dimensions", {
        "formality": 0.5,
        "energy": 0.5,
        "humor": 0.0,
        "authority": 0.5,
    })

    # Tokenize
    sentences = sent_tokenize(text)
    tokens = word_tokenize(text)
    tokens_lower = [t.lower() for t in tokens if t.isalpha()]
    text_lower = text.lower()

    # Dimension analysis
    actual = {
        "formality": analyze_formality(tokens_lower, text_lower),
        "energy": analyze_energy(tokens_lower, text),
        "humor": analyze_humor(tokens_lower, text_lower),
        "authority": analyze_authority(tokens_lower, text_lower),
    }

    dimension_results = {}
    weighted_score_sum = 0.0
    weight_total = 0.0

    # Weights for overall score (configurable in profile, with defaults)
    weights = profile.get("dimension_weights", {
        "formality": 1.0,
        "energy": 1.0,
        "humor": 0.8,
        "authority": 1.0,
    })

    for dim in ("formality", "energy", "humor", "authority"):
        target_val = targets.get(dim, 0.5)
        dist = dimension_distance(actual[dim], target_val)
        dim_score = score_from_distance(dist)
        w = weights.get(dim, 1.0)
        weighted_score_sum += dim_score * w
        weight_total += w
        dimension_results[dim] = {
            "actual": round(actual[dim], 4),
            "target": target_val,
            "distance": round(dist, 4),
            "score": dim_score,
        }

    # Word-list checks
    preferred = profile.get("preferred_words", [])
    avoided = profile.get("avoided_words", [])
    word_check = check_word_lists(tokens_lower, preferred, avoided)

    # Word-list contribution to overall score
    word_list_score = 100.0
    if preferred:
        word_list_score -= (1.0 - word_check["preferred_usage_ratio"]) * 30
    if avoided:
        penalty = min(word_check["avoided_violation_count"] * 10, 40)
        word_list_score -= penalty
    word_list_score = max(word_list_score, 0.0)

    # Combina pontuação de dimensão com pontuação de lista de palavras
    dimension_avg = (weighted_score_sum / weight_total) if weight_total else 50.0
    overall_score = round(dimension_avg * 0.7 + word_list_score * 0.3, 2)
    overall_score = max(0.0, min(100.0, overall_score))

    # Deviations
    deviations = generate_deviations(dimension_results, profile)

    # Sentence length check
    avg_sentence_len = (
        round(len(tokens) / len(sentences), 1) if sentences else 0
    )
    target_sentence_len = profile.get("target_sentence_length", None)
    if target_sentence_len and abs(avg_sentence_len - target_sentence_len) > 8:
        deviations.append({
            "dimension": "sentence_length",
            "severity": "medium",
            "message": (
                f"Comprimento médio de frase é {avg_sentence_len} palavras "
                f"(alvo: ~{target_sentence_len}). Considere ajustar."
            ),
        })

    return {
        "brand": profile.get("brand_name", "Unknown"),
        "overall_score": overall_score,
        "interpretation": _interpret_score(overall_score),
        "dimension_scores": dimension_results,
        "word_list_analysis": word_check,
        "word_list_score": round(word_list_score, 2),
        "deviations": deviations,
        "stats": {
            "word_count": len(tokens_lower),
            "sentence_count": len(sentences),
            "avg_sentence_length": avg_sentence_len,
        },
    }


def _interpret_score(score: float) -> str:
    """Retorna uma interpretação legível da pontuação geral."""
    if score >= 90:
        return "Excelente — muito alinhado com voz de marca"
    elif score >= 75:
        return "Bom — principalmente on-brand com desvios menores"
    elif score >= 60:
        return "Aceitável — desvios notáveis da voz de marca"
    elif score >= 40:
        return "Pobre — desalinhamento significativo com voz de marca"
    else:
        return "Crítico — conteúdo não corresponde à voz de marca"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Avalia conteúdo contra um perfil de voz de marca.",
        epilog=(
            "Exemplo:\n"
            '  python avaliador-voz.py --brand acme --text "Our product is great!"'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--brand", required=True,
        help="Slug do cliente (corresponde ao nome da pasta sob ./data/clientes/)",
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--text", type=str,
        help="Texto de conteúdo a analisar (inline).",
    )
    input_group.add_argument(
        "--file", type=str,
        help="Caminho para arquivo de texto contendo conteúdo a analisar.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Carrega perfil da marca
    profile = load_brand_profile(args.brand)
    if "error" in profile:
        print(json.dumps(profile, indent=2))
        sys.exit(1)

    # Resolve input text
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
    result = score_content(text, profile)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
