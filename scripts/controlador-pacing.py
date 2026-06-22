#!/usr/bin/env python3
"""Rastreador e previsão de pacing de gasto de anúncios.

Rastreia pacing de orçamento de anúncios contra cronograma linear de gasto. Calcula status de
pacing (sub/normal/sobre), requisitos de orçamento remanescente, gasto projetado para fim de período
e análise de tendências quando dados de gasto diário são fornecidos. Gera recomendações acionáveis
para realocação de orçamento.

Uso:
    python controlador-pacing.py --budget 30000 --period-days 30 --days-elapsed 15 --spend-to-date 12000
    python controlador-pacing.py --budget 10000 --period-days 14 --days-elapsed 7 --spend-to-date 6000 \
        --daily-spend '[500,600,700,800,900,1000,1100]'
    python controlador-pacing.py --budget 50000 --period-days 30 --days-elapsed 10 --spend-to-date 15000 \
        --channels '[{"name":"google","budget":30000,"spend":9000},{"name":"meta","budget":20000,"spend":6000}]'
"""

import argparse
import json
import sys

# ---------------------------------------------------------------------------
# Cálculos de pacing
# ---------------------------------------------------------------------------

def classify_pace(pace_percent):
    """Classifica status e severidade do pacing."""
    if pace_percent < 75:
        return "under_pacing", "severe"
    elif pace_percent < 90:
        return "under_pacing", "moderate"
    elif pace_percent <= 110:
        return "on_pace", "none"
    elif pace_percent <= 125:
        return "over_pacing", "moderate"
    else:
        return "over_pacing", "severe"


def compute_pacing(budget, period_days, days_elapsed, spend_to_date):
    """Cálculos core de pacing."""
    expected_spend = budget * (days_elapsed / period_days)
    remaining_budget = budget - spend_to_date
    remaining_days = period_days - days_elapsed

    pace_percent = (spend_to_date / expected_spend * 100) if expected_spend > 0 else 0.0
    status, severity = classify_pace(pace_percent)

    current_daily_avg = spend_to_date / days_elapsed if days_elapsed > 0 else 0.0
    required_daily = remaining_budget / remaining_days if remaining_days > 0 else 0.0

    adjustment_pct = 0.0
    if current_daily_avg > 0:
        adjustment_pct = ((required_daily - current_daily_avg) / current_daily_avg) * 100

    projected_total = current_daily_avg * period_days if days_elapsed > 0 else 0.0
    projected_variance = projected_total - budget
    projected_utilization = (projected_total / budget * 100) if budget > 0 else 0.0

    return {
        "pacing": {
            "expected_spend": round(expected_spend, 2),
            "actual_spend": round(spend_to_date, 2),
            "pace_percent": round(pace_percent, 1),
            "status": status,
            "severity": severity,
        },
        "remaining": {
            "budget": round(remaining_budget, 2),
            "days": remaining_days,
            "required_daily_spend": round(required_daily, 2),
            "current_daily_average": round(current_daily_avg, 2),
            "adjustment_needed_percent": round(adjustment_pct, 1),
        },
        "projection": {
            "projected_total_spend": round(projected_total, 2),
            "projected_variance": round(projected_variance, 2),
            "projected_utilization_percent": round(projected_utilization, 1),
        },
    }


# ---------------------------------------------------------------------------
# Análise de tendência
# ---------------------------------------------------------------------------

def analyze_trend(daily_spend, period_days, budget):
    """Analisa tendência de gasto diário quando dados históricos são fornecidos."""
    n = len(daily_spend)
    if n < 2:
        return None

    # Média móvel de 7 dias (ou janela completa se menos de 7 dias)
    window = min(7, n)
    recent = daily_spend[-window:]
    moving_avg = sum(recent) / len(recent)

    # Direção de tendência: compara média da primeira metade com a segunda
    mid = n // 2
    first_half_avg = sum(daily_spend[:mid]) / mid if mid > 0 else 0
    second_half_avg = sum(daily_spend[mid:]) / (n - mid) if (n - mid) > 0 else 0

    if second_half_avg > first_half_avg * 1.10:
        direction = "crescente"
    elif second_half_avg < first_half_avg * 0.90:
        direction = "decrescente"
    else:
        direction = "estável"

    # Padrão fim de semana vs dia útil (se ao menos 7 dias)
    weekday_weeknd = None
    if n >= 7:
        # Assume dia 0 = Segunda-feira para detecção de padrão
        weekday_vals = [daily_spend[i] for i in range(n) if i % 7 < 5]
        weekend_vals = [daily_spend[i] for i in range(n) if i % 7 >= 5]
        if weekday_vals and weekend_vals:
            wd_avg = sum(weekday_vals) / len(weekday_vals)
            we_avg = sum(weekend_vals) / len(weekend_vals)
            weekday_weeknd = {
                "weekday_average": round(wd_avg, 2),
                "weekend_average": round(we_avg, 2),
                "pattern": (
                    "dias úteis maiores" if wd_avg > we_avg * 1.15
                    else "fim de semana maior" if we_avg > wd_avg * 1.15
                    else "uniforme"
                ),
            }

    # Projeção baseada em tendência
    total_spent = sum(daily_spend)
    remaining_days = period_days - n
    if remaining_days > 0:
        # Usa média móvel como taxa diária projetada
        trend_projected_total = total_spent + moving_avg * remaining_days
    else:
        trend_projected_total = total_spent

    trend = {
        "direction": direction,
        "7_day_average": round(moving_avg, 2),
        "trend_projected_total": round(trend_projected_total, 2),
        "data_points": n,
    }

    if weekday_weeknd:
        trend["weekday_weekend_pattern"] = weekday_weeknd

    return trend


# ---------------------------------------------------------------------------
# Pacing por canal
# ---------------------------------------------------------------------------

def analyze_channels(channels, period_days, days_elapsed):
    """Análise de pacing por canal."""
    results = []
    for ch in channels:
        name = ch.get("name", "unknown")
        ch_budget = ch.get("budget", 0)
        ch_spend = ch.get("spend", 0)

        if ch_budget <= 0:
            results.append({"name": name, "error": "Orçamento inválido"})
            continue

        ch_result = compute_pacing(ch_budget, period_days, days_elapsed, ch_spend)
        ch_result["name"] = name
        ch_result["budget"] = ch_budget
        results.append(ch_result)

    return results


# ---------------------------------------------------------------------------
# Recomendações
# ---------------------------------------------------------------------------

def generate_recommendations(pacing, remaining, projection, trend, channels):
    """Gera recomendações acionáveis de pacing de orçamento."""
    recs = []
    status = pacing["status"]
    severity = pacing["severity"]
    adj = remaining["adjustment_needed_percent"]
    utilization = projection["projected_utilization_percent"]

    if status == "under_pacing":
        if severity == "severe":
            recs.append(
                f"Ritmo severamente abaixo do esperado em {pacing['pace_percent']:.0f}% do gasto esperado. "
                f"Aumentar gasto diário em {adj:.0f}% (${remaining['current_daily_average']:,.0f} -> "
                f"${remaining['required_daily_spend']:,.0f}) para utilizar orçamento completamente."
            )
            recs.append(
                f"Ritmo atual deixará ${abs(projection['projected_variance']):,.0f} não gasto "
                f"-- realoque para canais com melhor desempenho ou expanda direcionamento."
            )
        else:
            recs.append(
                f"Aumentar gasto diário em {adj:.0f}% "
                f"(${remaining['current_daily_average']:,.0f} -> ${remaining['required_daily_spend']:,.0f}) "
                f"para utilizar orçamento completamente."
            )
            recs.append(
                f"Ritmo atual deixará ${abs(projection['projected_variance']):,.0f} não gasto "
                f"-- realoque para canais com melhor desempenho."
            )
        recs.append(
            "Considere aumentar lances ou expandir direcionamento para distribuir orçamento remanescente."
        )

    elif status == "over_pacing":
        if severity == "severe":
            recs.append(
                f"Ritmo severamente acelerado em {pacing['pace_percent']:.0f}% do gasto esperado. "
                f"Reduzir gasto diário em {abs(adj):.0f}% para evitar esgotar orçamento cedo."
            )
            recs.append(
                "Considere pausar campanhas com menor desempenho ou reduzir lances imediatamente."
            )
        else:
            recs.append(
                f"Ritmo levemente acelerado. Reduza gasto diário em {abs(adj):.0f}% para manter-se no caminho."
            )
        recs.append(
            f"Na taxa atual, orçamento será esgotado "
            f"{remaining['days']} dias antes do período terminar. Aplique limites de orçamento diário."
        )

    else:
        recs.append(
            f"Pacing de orçamento está no caminho em {pacing['pace_percent']:.0f}%. "
            f"Mantenha os níveis de gasto atuais."
        )
        if utilization < 95:
            recs.append(
                "Há espaço para aumentar gasto. Considere testar novas variações de anúncios "
                "ou expandir para públicos adicionais."
            )

    if trend:
        if trend["direction"] == "decrescente" and status != "over_pacing":
            recs.append(
                f"Tendência de gasto está diminuindo (média 7 dias: ${trend['7_day_average']:,.0f}). "
                f"Investigue problemas de entrega ou saturação de público."
            )
        elif trend["direction"] == "crescente" and status == "over_pacing":
            recs.append(
                "Tendência de gasto está acelerando enquanto já está acelerado. "
                "Aplique limites diários mais rígidos para evitar esgotamento antecipado de orçamento."
            )

    if channels:
        over_channels = [c["name"] for c in channels if c.get("pacing", {}).get("status") == "over_pacing"]
        under_channels = [c["name"] for c in channels if c.get("pacing", {}).get("status") == "under_pacing"]
        if over_channels and under_channels:
            recs.append(
                f"Rebalancear orçamento: {', '.join(over_channels)} acelerado enquanto "
                f"{', '.join(under_channels)} abaixo do esperado. Redistribua fundos adequadamente."
            )

    return recs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Rastreador e previsão de pacing de gasto de anúncios"
    )
    parser.add_argument(
        "--budget", required=True, type=float,
        help="Orçamento total para o período",
    )
    parser.add_argument(
        "--period-days", required=True, type=int,
        help="Dias totais do período de orçamento",
    )
    parser.add_argument(
        "--days-elapsed", required=True, type=int,
        help="Dias decorridos até agora",
    )
    parser.add_argument(
        "--spend-to-date", required=True, type=float,
        help="Valor gasto até agora",
    )
    parser.add_argument(
        "--daily-spend", default=None,
        help="Array JSON de valores de gasto diário para análise de tendência",
    )
    parser.add_argument(
        "--channels", default=None,
        help='Array JSON de objetos de canal: [{"name":"google","budget":10000,"spend":5000}]',
    )
    args = parser.parse_args()

    # --- Validação ---
    if args.budget <= 0:
        json.dump({"error": "Orçamento deve ser um número positivo"}, sys.stdout, indent=2)
        print()
        sys.exit(0)

    if args.period_days <= 0:
        json.dump({"error": "Dias do período devem ser um inteiro positivo"}, sys.stdout, indent=2)
        print()
        sys.exit(0)

    if args.days_elapsed < 0:
        json.dump({"error": "Dias decorridos não podem ser negativos"}, sys.stdout, indent=2)
        print()
        sys.exit(0)

    if args.days_elapsed > args.period_days:
        json.dump({"error": "Dias decorridos não podem exceder dias do período"}, sys.stdout, indent=2)
        print()
        sys.exit(0)

    if args.days_elapsed == 0:
        json.dump({"error": "Dias decorridos devem ser pelo menos 1 para análise de pacing"}, sys.stdout, indent=2)
        print()
        sys.exit(0)

    if args.spend_to_date < 0:
        json.dump({"error": "Gasto até agora não pode ser negativo"}, sys.stdout, indent=2)
        print()
        sys.exit(0)

    # Processa gasto diário opcional
    daily_spend = None
    if args.daily_spend:
        try:
            daily_spend = json.loads(args.daily_spend)
            if not isinstance(daily_spend, list):
                json.dump({"error": "daily-spend deve ser um array JSON de números"}, sys.stdout, indent=2)
                print()
                sys.exit(0)
            daily_spend = [float(v) for v in daily_spend]
        except (json.JSONDecodeError, ValueError) as exc:
            json.dump({"error": f"JSON inválido em daily-spend: {exc}"}, sys.stdout, indent=2)
            print()
            sys.exit(0)

    # Processa canais opcionais
    channels_data = None
    if args.channels:
        try:
            channels_data = json.loads(args.channels)
            if not isinstance(channels_data, list):
                json.dump({"error": "channels deve ser um array JSON"}, sys.stdout, indent=2)
                print()
                sys.exit(0)
        except json.JSONDecodeError as exc:
            json.dump({"error": f"JSON inválido em channels: {exc}"}, sys.stdout, indent=2)
            print()
            sys.exit(0)

    # --- Cálculos principais ---
    try:
        result = compute_pacing(args.budget, args.period_days, args.days_elapsed, args.spend_to_date)

        output = {
            "budget": args.budget,
            "period_days": args.period_days,
            "days_elapsed": args.days_elapsed,
        }
        output.update(result)

        # Análise de tendência
        trend = None
        if daily_spend:
            trend = analyze_trend(daily_spend, args.period_days, args.budget)
            if trend:
                output["trend"] = trend

        # Pacing por canal
        channel_results = None
        if channels_data:
            channel_results = analyze_channels(channels_data, args.period_days, args.days_elapsed)
            output["channels"] = channel_results

        # Recomendações
        output["recommendations"] = generate_recommendations(
            result["pacing"], result["remaining"], result["projection"],
            trend, channel_results,
        )

        json.dump(output, sys.stdout, indent=2)
        print()

    except Exception as exc:
        json.dump({"error": f"Falha no cálculo de pacing: {exc}"}, sys.stdout, indent=2)
        print()


if __name__ == "__main__":
    main()
