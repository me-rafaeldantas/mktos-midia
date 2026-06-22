#!/usr/bin/env python3
"""Previsão de receita/pipeline de marketing usando tendências históricas.

Toma dados de receita mensal histórica (e gasto opcional) e produz
previsões multi-mês usando regressão linear e modelos de taxa de crescimento.
Suporta multiplicadores sazonais e overrides de taxa de crescimento customizados. Retorna
previsões blended com intervalos de confiança, ROAS projetado e suposições.

Dependências: nenhuma (stdlib apenas)

Uso:
    python previsao-receita.py --historical '[{"month":"2025-01","revenue":50000,"spend":15000}]'
    python previsao-receita.py --file history.json --forecast-months 6
    python previsao-receita.py --file history.json --growth-assumption 0.05
    python previsao-receita.py --file history.json --seasonality '{"1":0.85,"11":1.3,"12":1.5}'
"""

import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Regressão linear (mínimos quadrados)
# ---------------------------------------------------------------------------

def linear_regression(x, y):
    """Calcula slope e intercept usando mínimos quadrados ordinários.

    Parâmetros:
        x: lista de float (variável independente)
        y: lista de float (variável dependente)

    Retorna:
        tupla (slope, intercept)
    """
    n = len(x)
    if n < 2:
        return 0.0, y[0] if y else 0.0

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi ** 2 for xi in x)

    denom = n * sum_x2 - sum_x ** 2
    if denom == 0:
        return 0.0, sum_y / n

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


# ---------------------------------------------------------------------------
# Cálculos de taxa de crescimento
# ---------------------------------------------------------------------------

def compute_growth_rates(revenues):
    """Calcula taxas de crescimento mês-a-mês."""
    rates = []
    for i in range(1, len(revenues)):
        if revenues[i - 1] > 0:
            rate = (revenues[i] - revenues[i - 1]) / revenues[i - 1]
            rates.append(rate)
        else:
            rates.append(0.0)
    return rates


def average_growth(rates, window=None):
    """Taxa de crescimento médio nos últimos períodos `window` (ou todos)."""
    if not rates:
        return 0.0
    if window is not None:
        rates = rates[-window:]
    return sum(rates) / len(rates) if rates else 0.0


# ---------------------------------------------------------------------------
# Aritmética de meses
# ---------------------------------------------------------------------------

def next_month(month_str):
    """Dado 'YYYY-MM', retorna a string do mês seguinte."""
    year, month = int(month_str[:4]), int(month_str[5:7])
    month += 1
    if month > 12:
        month = 1
        year += 1
    return f"{year:04d}-{month:02d}"


def month_index(month_str):
    """Retorna índice de mês 1-12 de 'YYYY-MM'."""
    return int(month_str[5:7])


# ---------------------------------------------------------------------------
# Classificação de tendência
# ---------------------------------------------------------------------------

def classify_trend(growth_rates):
    """Classifica a direção geral da tendência."""
    if not growth_rates:
        return "insufficient_data"

    recent = growth_rates[-3:] if len(growth_rates) >= 3 else growth_rates
    avg_recent = sum(recent) / len(recent)

    if avg_recent > 0.02:
        return "growing"
    elif avg_recent < -0.02:
        return "declining"
    else:
        return "stable"


# ---------------------------------------------------------------------------
# Previsão
# ---------------------------------------------------------------------------

def forecast_revenue(historical, forecast_months, growth_assumption, seasonality):
    """Gera previsões de receita a partir de dados históricos."""
    n = len(historical)
    months = [h["month"] for h in historical]
    revenues = [h["revenue"] for h in historical]
    spends = [h.get("spend") for h in historical]
    has_spend = any(s is not None and s > 0 for s in spends)

    # --- Análise histórica ---
    growth_rates = compute_growth_rates(revenues)
    avg_growth_all = average_growth(growth_rates)
    avg_growth_3mo = average_growth(growth_rates, window=3)
    avg_growth_6mo = average_growth(growth_rates, window=6)
    trend_direction = classify_trend(growth_rates)

    avg_monthly_revenue = sum(revenues) / n if n > 0 else 0
    avg_roas = None
    if has_spend:
        valid_spend = [(r, s) for r, s in zip(revenues, spends) if s and s > 0]
        if valid_spend:
            total_rev = sum(r for r, _ in valid_spend)
            total_sp = sum(s for _, s in valid_spend)
            avg_roas = round(total_rev / total_sp, 2) if total_sp > 0 else None

    historical_analysis = {
        "months_analyzed": n,
        "average_monthly_revenue": round(avg_monthly_revenue, 2),
        "average_monthly_growth_rate": round(avg_growth_all, 4),
        "recent_3mo_growth_rate": round(avg_growth_3mo, 4),
        "trend_direction": trend_direction,
    }
    if avg_roas is not None:
        historical_analysis["average_roas"] = avg_roas

    # --- Previsão ---
    # Regressão linear: x = índice de período (0..n-1), y = receita
    x_vals = list(range(n))
    slope, intercept = linear_regression(x_vals, revenues)

    # Determina taxa de crescimento efetiva
    if growth_assumption is not None:
        effective_growth = growth_assumption
    else:
        effective_growth = avg_growth_3mo if len(growth_rates) >= 3 else avg_growth_all

    # Processa multiplicadores de sazonalidade
    seasonal = {}
    if seasonality:
        for k, v in seasonality.items():
            seasonal[int(k)] = float(v)

    # Taxa média de crescimento de gasto para projeção
    avg_spend = None
    if has_spend:
        valid_spends = [s for s in spends if s is not None and s > 0]
        avg_spend = sum(valid_spends) / len(valid_spends) if valid_spends else None

    # Gera previsões
    forecasts = []
    last_month = months[-1]
    last_revenue = revenues[-1]
    current_month = last_month

    for i in range(forecast_months):
        current_month = next_month(current_month)
        period_idx = n + i  # continuing the x-axis

        # Previsão linear
        linear_val = slope * period_idx + intercept

        # Previsão por taxa de crescimento
        growth_val = last_revenue * ((1 + effective_growth) ** (i + 1))

        # Mesclado (50/50)
        blended = (linear_val + growth_val) / 2

        # Aplica multiplicador sazonal se disponível
        m_idx = month_index(current_month)
        if m_idx in seasonal:
            multiplier = seasonal[m_idx]
            linear_val *= multiplier
            growth_val *= multiplier
            blended *= multiplier

        # Confidence range: +-15% base, widening by 3% per additional month
        confidence_margin = 0.15 + (i * 0.03)
        conf_low = blended * (1 - confidence_margin)
        conf_high = blended * (1 + confidence_margin)

        forecast_entry = {
            "month": current_month,
            "linear_forecast": round(max(0, linear_val), 2),
            "growth_forecast": round(max(0, growth_val), 2),
            "blended_forecast": round(max(0, blended), 2),
            "confidence_low": round(max(0, conf_low), 2),
            "confidence_high": round(conf_high, 2),
        }

        # Gasto projetado e ROAS
        if avg_spend is not None and avg_roas is not None:
            proj_spend = round(blended / avg_roas, 2) if avg_roas > 0 else round(avg_spend, 2)
            forecast_entry["projected_spend"] = proj_spend
            forecast_entry["projected_roas"] = avg_roas

        forecasts.append(forecast_entry)

    # --- Resumo ---
    total_forecasted_rev = sum(f["blended_forecast"] for f in forecasts)
    total_forecasted_spend = sum(f.get("projected_spend", 0) for f in forecasts) if has_spend else None

    first_forecast_month = forecasts[0]["month"] if forecasts else ""
    last_forecast_month = forecasts[-1]["month"] if forecasts else ""

    # Taxa de crescimento projetada no período de previsão
    if forecasts and forecasts[0]["blended_forecast"] > 0:
        proj_growth = (forecasts[-1]["blended_forecast"] - forecasts[0]["blended_forecast"]) / forecasts[0]["blended_forecast"]
        if forecast_months > 1:
            proj_growth = proj_growth / (forecast_months - 1) if forecast_months > 1 else proj_growth
    else:
        proj_growth = effective_growth

    # Nível de confiança baseado na qualidade dos dados
    if n >= 12:
        confidence_level = "high"
    elif n >= 6:
        confidence_level = "moderate"
    elif n >= 3:
        confidence_level = "low"
    else:
        confidence_level = "very_low"

    summary = {
        "forecast_period": f"{first_forecast_month} to {last_forecast_month}",
        "total_forecasted_revenue": round(total_forecasted_rev, 2),
        "projected_growth_rate": round(proj_growth, 4),
        "confidence_level": confidence_level,
    }
    if total_forecasted_spend is not None:
        summary["total_forecasted_spend"] = round(total_forecasted_spend, 2)

    # --- Premissas ---
    assumptions = [
        "Modelos linear e taxa de crescimento com peso igual (blend 50/50)",
    ]
    if growth_assumption is not None:
        assumptions.append(f"Taxa de crescimento sobrescrita para {growth_assumption * 100:.1f}% mensal")
    else:
        assumptions.append(f"Taxa de crescimento derivada de média de {min(3, len(growth_rates))} meses recentes ({effective_growth * 100:.2f}%)")

    if has_spend:
        assumptions.append("Gasto assumido crescer proporcionalmente à receita")
    else:
        assumptions.append("Nenhum dado de gasto fornecido -- projeções de ROAS indisponíveis")

    if seasonality:
        assumptions.append(f"Multiplicadores sazonais aplicados para meses: {', '.join(str(k) for k in sorted(seasonal.keys()))}")

    base_margin = 15
    max_margin = base_margin + (forecast_months - 1) * 3
    assumptions.append(f"Intervalo de confiança: +/-{base_margin}% a +/-{max_margin}% (ampliando para previsões mais longas)")

    # --- Compilar saída ---
    output = {
        "historical_analysis": historical_analysis,
        "forecast": forecasts,
        "summary": summary,
        "assumptions": assumptions,
    }

    return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Previsão de receita/pipeline de marketing usando tendências históricas"
    )
    parser.add_argument(
        "--historical", default=None,
        help='Array JSON de dados mensais: [{"month":"2025-01","revenue":50000,"spend":15000}]',
    )
    parser.add_argument(
        "--file", default=None,
        help="Caminho do arquivo JSON contendo dados históricos (alternativa a --historical)",
    )
    parser.add_argument(
        "--forecast-months", type=int, default=3,
        help="Número de meses para prever (padrão: 3)",
    )
    parser.add_argument(
        "--growth-assumption", type=float, default=None,
        help="Sobrescrever taxa de crescimento (ex: 0.05 para 5%% mensal)",
    )
    parser.add_argument(
        "--seasonality", default=None,
        help='Objeto JSON com índices de mês e multiplicadores: {"11":1.3,"12":1.5}',
    )
    args = parser.parse_args()

    # --- Carregamento de entrada ---
    if not args.historical and not args.file:
        json.dump(
            {"error": "Forneça --historical (array JSON) ou --file (caminho do arquivo JSON)"},
            sys.stdout, indent=2,
        )
        print()
        sys.exit(0)

    historical = None
    if args.file:
        path = Path(args.file)
        if not path.exists():
            json.dump({"error": f"Arquivo não encontrado: {args.file}"}, sys.stdout, indent=2)
            print()
            sys.exit(0)
        try:
            content = path.read_text(encoding="utf-8")
            historical = json.loads(content)
        except json.JSONDecodeError as exc:
            json.dump({"error": f"JSON inválido em arquivo: {exc}"}, sys.stdout, indent=2)
            print()
            sys.exit(0)
        except Exception as exc:
            json.dump({"error": f"Não foi possível ler o arquivo: {exc}"}, sys.stdout, indent=2)
            print()
            sys.exit(0)
    else:
        try:
            historical = json.loads(args.historical)
        except json.JSONDecodeError as exc:
            json.dump({"error": f"JSON inválido em --historical: {exc}"}, sys.stdout, indent=2)
            print()
            sys.exit(0)

    if not isinstance(historical, list):
        json.dump({"error": "Dados históricos devem ser um array JSON"}, sys.stdout, indent=2)
        print()
        sys.exit(0)

    if len(historical) < 2:
        json.dump({"error": "Mínimo de 2 meses de dados históricos requerido para previsão"}, sys.stdout, indent=2)
        print()
        sys.exit(0)

    # Valida cada entrada
    for i, entry in enumerate(historical):
        if not isinstance(entry, dict):
            json.dump({"error": f"Entrada {i} não é um objeto JSON"}, sys.stdout, indent=2)
            print()
            sys.exit(0)
        if "month" not in entry:
            json.dump({"error": f"Entrada {i} falta campo 'month'"}, sys.stdout, indent=2)
            print()
            sys.exit(0)
        if "revenue" not in entry:
            json.dump({"error": f"Entrada {i} falta campo 'revenue'"}, sys.stdout, indent=2)
            print()
            sys.exit(0)
        try:
            entry["revenue"] = float(entry["revenue"])
        except (ValueError, TypeError):
            json.dump({"error": f"Entrada {i} tem valor de receita inválido"}, sys.stdout, indent=2)
            print()
            sys.exit(0)
        if entry["revenue"] < 0:
            json.dump({"error": f"Entrada {i} tem receita negativa"}, sys.stdout, indent=2)
            print()
            sys.exit(0)
        if "spend" in entry and entry["spend"] is not None:
            try:
                entry["spend"] = float(entry["spend"])
            except (ValueError, TypeError):
                entry["spend"] = None

    # Valida meses de previsão
    if args.forecast_months < 1:
        json.dump({"error": "forecast-months deve ser pelo menos 1"}, sys.stdout, indent=2)
        print()
        sys.exit(0)
    if args.forecast_months > 24:
        json.dump({"error": "forecast-months não pode exceder 24"}, sys.stdout, indent=2)
        print()
        sys.exit(0)

    # Processa sazonalidade
    seasonality = None
    if args.seasonality:
        try:
            seasonality = json.loads(args.seasonality)
            if not isinstance(seasonality, dict):
                json.dump({"error": "Sazonalidade deve ser um objeto JSON"}, sys.stdout, indent=2)
                print()
                sys.exit(0)
            # Valida que as chaves são 1-12
            for k, v in seasonality.items():
                ki = int(k)
                if ki < 1 or ki > 12:
                    json.dump({"error": f"Índice de mês de sazonalidade {k} deve estar entre 1-12"}, sys.stdout, indent=2)
                    print()
                    sys.exit(0)
                float(v)  # validate multiplier is numeric
        except json.JSONDecodeError as exc:
            json.dump({"error": f"JSON de sazonalidade inválido: {exc}"}, sys.stdout, indent=2)
            print()
            sys.exit(0)
        except (ValueError, TypeError) as exc:
            json.dump({"error": f"Valores de sazonalidade inválidos: {exc}"}, sys.stdout, indent=2)
            print()
            sys.exit(0)

    # Valida premissa de crescimento
    if args.growth_assumption is not None:
        if args.growth_assumption < -0.5 or args.growth_assumption > 2.0:
            json.dump(
                {"error": "growth-assumption deve estar entre -0.5 (-50%) e 2.0 (200%)"},
                sys.stdout, indent=2,
            )
            print()
            sys.exit(0)

    # Ordena dados históricos por mês
    historical.sort(key=lambda h: h["month"])

    # --- Run forecast ---
    try:
        result = forecast_revenue(
            historical=historical,
            forecast_months=args.forecast_months,
            growth_assumption=args.growth_assumption,
            seasonality=seasonality,
        )
        json.dump(result, sys.stdout, indent=2)
        print()
    except Exception as exc:
        json.dump({"error": f"Previsão falhou: {exc}"}, sys.stdout, indent=2)
        print()


if __name__ == "__main__":
    main()
