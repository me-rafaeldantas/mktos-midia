#!/usr/bin/env python3
"""
calculadora-roi.py
=================
Calculadora de ROI de campanha com modelos de atribuição multi-touch. Calcula ROI,
ROAS, CPA e métricas de contribuição por canal, aplica modelos de atribuição
entre dados multi-canal e gera recomendações de otimização.

Dependências: nenhuma (stdlib apenas)

Uso:
    python calculadora-roi.py --channels '[{"name":"Google Ads","spend":5000,"conversions":150,"revenue":22500}]'
    python calculadora-roi.py --file channels.json --attribution linear --period "Q1 2026"
    python calculadora-roi.py --channels '[...]' --attribution time_decay --ltv 1200
"""

import argparse
import json
import math
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Auxiliares de atribuição
# ---------------------------------------------------------------------------

VALID_MODELS = {"last_touch", "first_touch", "linear", "time_decay", "position_based"}


def apply_attribution(channels, model):
    """Retorna uma lista de pesos de atribuição (mesma ordem dos canais).

    Cada peso é um float entre 0 e 1; todos os pesos somam 1.
    """
    n = len(channels)
    if n == 0:
        return []
    if n == 1:
        return [1.0]

    if model == "last_touch":
        weights = [0.0] * n
        weights[-1] = 1.0

    elif model == "first_touch":
        weights = [0.0] * n
        weights[0] = 1.0

    elif model == "linear":
        weights = [1.0 / n] * n

    elif model == "time_decay":
        decay = 0.7
        raw = [decay ** (n - 1 - i) for i in range(n)]
        total = sum(raw)
        weights = [r / total for r in raw]

    elif model == "position_based":
        if n == 2:
            weights = [0.5, 0.5]
        else:
            weights = [0.0] * n
            weights[0] = 0.4
            weights[-1] = 0.4
            middle_share = 0.2 / (n - 2)
            for i in range(1, n - 1):
                weights[i] = middle_share
    else:
        weights = [1.0 / n] * n

    return weights


# ---------------------------------------------------------------------------
# Cálculos de métricas
# ---------------------------------------------------------------------------

def calculate_channel_metrics(channel, total_revenue, ltv=None):
    """Calcula métricas por canal. Retorna um dict."""
    spend = channel["spend"]
    conversions = channel["conversions"]
    revenue = channel["revenue"]

    roi_percent = ((revenue - spend) / spend * 100) if spend > 0 else None
    roas = (revenue / spend) if spend > 0 else None
    cpa = (spend / conversions) if conversions > 0 else None
    rev_per_conv = (revenue / conversions) if conversions > 0 else None
    contribution = (revenue / total_revenue * 100) if total_revenue > 0 else 0.0

    result = {
        "name": channel["name"],
        "spend": spend,
        "conversions": conversions,
        "revenue": revenue,
        "roi_percent": round(roi_percent, 2) if roi_percent is not None else None,
        "roas": round(roas, 2) if roas is not None else None,
        "cpa": round(cpa, 2) if cpa is not None else None,
        "revenue_per_conversion": round(rev_per_conv, 2) if rev_per_conv is not None else None,
        "contribution_percent": round(contribution, 2),
        "ltv_cac_ratio": None,
    }

    if ltv is not None and cpa is not None and cpa > 0:
        result["ltv_cac_ratio"] = round(ltv / cpa, 2)

    return result


def calculate_summary(channel_metrics):
    """Calcula resumo agregado entre todos os canais."""
    total_spend = sum(c["spend"] for c in channel_metrics)
    total_revenue = sum(c["revenue"] for c in channel_metrics)
    total_conversions = sum(c["conversions"] for c in channel_metrics)

    blended_roi = ((total_revenue - total_spend) / total_spend * 100) if total_spend > 0 else None
    blended_roas = (total_revenue / total_spend) if total_spend > 0 else None
    blended_cpa = (total_spend / total_conversions) if total_conversions > 0 else None

    # Ordena por ROI (decrescente), trata valores None
    valid_roi = [c for c in channel_metrics if c["roi_percent"] is not None]
    sorted_by_roi = sorted(valid_roi, key=lambda c: c["roi_percent"], reverse=True)

    best_channel = sorted_by_roi[0]["name"] if sorted_by_roi else None
    worst_channel = sorted_by_roi[-1]["name"] if sorted_by_roi else None

    # Ordena por ROAS para eficiência de orçamento
    valid_roas = [c for c in channel_metrics if c["roas"] is not None]
    sorted_by_roas = sorted(valid_roas, key=lambda c: c["roas"], reverse=True)
    efficiency_ranking = [c["name"] for c in sorted_by_roas]

    return {
        "total_spend": round(total_spend, 2),
        "total_revenue": round(total_revenue, 2),
        "total_conversions": total_conversions,
        "blended_roi_percent": round(blended_roi, 2) if blended_roi is not None else None,
        "blended_roas": round(blended_roas, 2) if blended_roas is not None else None,
        "blended_cpa": round(blended_cpa, 2) if blended_cpa is not None else None,
        "best_channel": best_channel,
        "worst_channel": worst_channel,
        "budget_efficiency_ranking": efficiency_ranking,
    }


def generate_recommendations(channel_metrics, summary):
    """Gera recomendações de orçamento e desempenho acionáveis."""
    recs = []

    # Ordena por ROAS decrescente para lógica de recomendações
    valid = [c for c in channel_metrics if c["roas"] is not None]
    sorted_by_roas = sorted(valid, key=lambda c: c["roas"], reverse=True)

    if sorted_by_roas:
        top = sorted_by_roas[0]
        recs.append(
            f"Aumente orçamento de {top['name']} \u2014 maior ROAS em {top['roas']}x"
        )

    # Marca canais com ROI negativo
    negative = [c for c in channel_metrics if c["roi_percent"] is not None and c["roi_percent"] < 0]
    for ch in negative:
        recs.append(
            f"Reduza gasto em {ch['name']} \u2014 ROI negativo ({ch['roi_percent']}%)"
        )

    # Sugere realocação do pior para o segundo melhor
    if len(sorted_by_roas) >= 2 and negative:
        worst = negative[0]
        runner_up = sorted_by_roas[1]
        recs.append(
            f"Teste realocar 20% do orçamento de {worst['name']} para "
            f"{runner_up['name']} (ROAS {runner_up['roas']}x)"
        )

    # Aviso de CPA alto
    if summary["blended_cpa"] is not None:
        high_cpa = [
            c for c in channel_metrics
            if c["cpa"] is not None and c["cpa"] > summary["blended_cpa"] * 1.5
        ]
        for ch in high_cpa:
            recs.append(
                f"Investigue CPA de {ch['name']} (${ch['cpa']:.2f}) \u2014 "
                f"50%+ acima da média blended (${summary['blended_cpa']:.2f})"
            )

    # Orientação sobre LTV:CAC
    ltv_channels = [c for c in channel_metrics if c["ltv_cac_ratio"] is not None]
    low_ltv = [c for c in ltv_channels if c["ltv_cac_ratio"] < 3.0]
    for ch in low_ltv:
        recs.append(
            f"Razão LTV:CAC de {ch['name']} é {ch['ltv_cac_ratio']} \u2014 "
            f"abaixo do limite saudável de 3:1. Revise targeting ou reduza gasto."
        )

    if not recs:
        recs.append(
            "Todos os canais estão performando bem. Considere testes A/B de criativo "
            "ou expansão para novos canais para crescimento."
        )

    return recs


# ---------------------------------------------------------------------------
# Leitura de entrada
# ---------------------------------------------------------------------------

def load_channels(args):
    """Carrega dados de canal de JSON --channels ou caminho --file."""
    if args.file:
        path = Path(args.file)
        if not path.exists():
            return None, f"Arquivo não encontrado: {args.file}"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            return None, f"Falha ao ler arquivo: {exc}"
    elif args.channels:
        try:
            data = json.loads(args.channels)
        except json.JSONDecodeError as exc:
            return None, f"JSON inválido em --channels: {exc}"
    else:
        return None, "Forneça --channels ou --file"

    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list) or len(data) == 0:
        return None, "Dados de canal devem ser um array JSON não vazio de objetos"

    required_keys = {"name", "spend", "conversions", "revenue"}
    for i, ch in enumerate(data):
        if not isinstance(ch, dict):
            return None, f"Entrada do canal {i} não é um objeto"
        missing = required_keys - set(ch.keys())
        if missing:
            return None, f"Canal '{ch.get('name', i)}' faltam chaves: {', '.join(sorted(missing))}"
        if ch["spend"] < 0:
            return None, f"Canal '{ch['name']}' tem gasto negativo"
        if ch["conversions"] < 0:
            return None, f"Canal '{ch['name']}' tem conversões negativas"
        if ch["revenue"] < 0:
            return None, f"Canal '{ch['name']}' tem receita negativa"

    return data, None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Calculadora de ROI de campanha com modelos de atribuição multi-touch"
    )
    parser.add_argument(
        "--channels", default=None,
        help='Array JSON de objetos de canal: [{"name":"...","spend":N,"conversions":N,"revenue":N}]',
    )
    parser.add_argument(
        "--file", default=None,
        help="Caminho do arquivo JSON com dados de canal (alternativa a --channels)",
    )
    parser.add_argument(
        "--attribution", default="last_touch",
        choices=sorted(VALID_MODELS),
        help="Modelo de atribuição (padrão: last_touch)",
    )
    parser.add_argument(
        "--period", default=None,
        help='Rótulo de período de tempo (ex: "Q1 2026")',
    )
    parser.add_argument(
        "--ltv", type=float, default=None,
        help="Valor médio de lifetime value do cliente (habilita razão LTV:CAC)",
    )
    args = parser.parse_args()

    # --- Carregar e validar ---
    channels, err = load_channels(args)
    if err:
        json.dump({"error": err}, sys.stdout, indent=2)
        print()
        return

    if args.ltv is not None and args.ltv <= 0:
        json.dump({"error": "LTV deve ser um número positivo"}, sys.stdout, indent=2)
        print()
        return

    # --- Calcular métricas por canal ---
    total_revenue = sum(ch["revenue"] for ch in channels)
    channel_metrics = [
        calculate_channel_metrics(ch, total_revenue, ltv=args.ltv)
        for ch in channels
    ]

    # --- Pesos de atribuição ---
    weights = apply_attribution(channels, args.attribution)
    for i, cm in enumerate(channel_metrics):
        cm["attribution_weight"] = round(weights[i], 4)

    # --- Resumo ---
    summary = calculate_summary(channel_metrics)

    # --- Recomendações ---
    recommendations = generate_recommendations(channel_metrics, summary)

    # --- Construir saída ---
    output = {}
    if args.period:
        output["period"] = args.period
    output["attribution_model"] = args.attribution
    output["channels"] = channel_metrics
    output["summary"] = summary
    output["recommendations"] = recommendations

    json.dump(output, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
