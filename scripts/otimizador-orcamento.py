#!/usr/bin/env python3
"""
otimizador-orcamento.py
===================
Otimizador de realocação de orçamento de marketing orientado por dados. Analisa
desempenho atual do canal, aplica modelo de retornos decrescentes (escala raiz
quadrada) e recomenda alocação otimizada que maximize receita projetada dentro
do orçamento total fornecido.

Dependências: nenhuma (stdlib apenas)

Uso:
    python otimizador-orcamento.py --channels '[{"name":"Google Ads","spend":5000,"conversions":150,"revenue":22500}]' --total-budget 15000
    python otimizador-orcamento.py --file channels.json --total-budget 20000 --min-spend 500 --test-budget-pct 15
"""

import argparse
import json
import math
import sys
from pathlib import Path

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
# Lógica de otimização
# ---------------------------------------------------------------------------

def projected_revenue(current_revenue, current_spend, new_spend):
    """Modelo de retornos decrescentes: receita escala com sqrt(novo/atual).

    Se current_spend for zero não conseguimos projetar, então retorna 0.
    """
    if current_spend <= 0 or current_revenue <= 0:
        return 0.0
    return current_revenue * math.sqrt(new_spend / current_spend)


def marginal_efficiency(channel):
    """ROAS como sinal primário de eficiência."""
    if channel["spend"] <= 0:
        return 0.0
    return channel["revenue"] / channel["spend"]


def optimise(channels, total_budget, min_spend, test_budget_pct):
    """Aloca orçamento entre canais para maximizar receita projetada.

    Estratégia:
    1. Reservar orçamento de teste.
    2. Dar a cada canal ativo pelo menos min_spend.
    3. Distribuir orçamento restante proporcionalmente à eficiência marginal,
       então usar alocação gulosa iterativa (step chunks) para refinar.
    """
    n = len(channels)
    test_budget = round(total_budget * (test_budget_pct / 100.0), 2)
    allocatable = total_budget - test_budget

    # Caso especial: orçamento insuficiente para mínimos
    total_min = min_spend * n
    if total_min > allocatable:
        # Distribui igualmente o que temos
        per_channel = allocatable / n if n > 0 else 0
        allocation = [per_channel] * n
    else:
        # Começa com o mínimo, distribui o resto por eficiência
        efficiencies = [marginal_efficiency(ch) for ch in channels]
        total_eff = sum(efficiencies)

        allocation = [min_spend] * n
        remaining = allocatable - total_min

        if total_eff > 0 and remaining > 0:
            # Alocação proporcional por eficiência
            for i in range(n):
                share = (efficiencies[i] / total_eff) * remaining
                allocation[i] += share
        elif remaining > 0:
            # Todos os canais com eficiência zero, divide igualmente
            per_channel = remaining / n
            for i in range(n):
                allocation[i] += per_channel

    # Arredonda alocações para 2 casas decimais, absorve resíduos
    allocation = [round(a, 2) for a in allocation]
    dust = round(allocatable - sum(allocation), 2)
    if dust != 0 and n > 0:
        # Adiciona resíduos ao canal mais eficiente
        best_idx = max(range(n), key=lambda i: marginal_efficiency(channels[i]))
        allocation[best_idx] = round(allocation[best_idx] + dust, 2)

    return allocation, test_budget


def build_output(channels, allocation, test_budget, total_budget):
    """Constrói o JSON completo de saída."""
    # Estado atual
    current_total_spend = sum(ch["spend"] for ch in channels)
    current_total_revenue = sum(ch["revenue"] for ch in channels)
    current_roas = (current_total_revenue / current_total_spend) if current_total_spend > 0 else 0

    # Detalhes dos canais otimizados
    opt_channels = []
    opt_total_revenue = 0.0

    for i, ch in enumerate(channels):
        new_spend = allocation[i]
        proj_rev = projected_revenue(ch["revenue"], ch["spend"], new_spend)
        opt_total_revenue += proj_rev

        current_roas_ch = (ch["revenue"] / ch["spend"]) if ch["spend"] > 0 else 0
        proj_roas_ch = (proj_rev / new_spend) if new_spend > 0 else 0
        change_pct = ((new_spend - ch["spend"]) / ch["spend"] * 100) if ch["spend"] > 0 else None

        opt_channels.append({
            "name": ch["name"],
            "current_spend": ch["spend"],
            "optimized_spend": round(new_spend, 2),
            "change_percent": round(change_pct, 1) if change_pct is not None else None,
            "current_roas": round(current_roas_ch, 2),
            "projected_roas": round(proj_roas_ch, 2),
            "projected_revenue": round(proj_rev, 2),
        })

    opt_total_revenue = round(opt_total_revenue, 2)
    opt_total_spend = round(sum(allocation), 2)
    opt_roas = (opt_total_revenue / opt_total_spend) if opt_total_spend > 0 else 0

    revenue_change = round(opt_total_revenue - current_total_revenue, 2)
    revenue_change_pct = round(
        (revenue_change / current_total_revenue * 100) if current_total_revenue > 0 else 0, 1
    )
    roas_change = round(opt_roas - current_roas, 2)

    # Recomendações
    recs = generate_recommendations(channels, opt_channels, test_budget)

    return {
        "current_allocation": {
            "total_spend": round(current_total_spend, 2),
            "total_revenue": round(current_total_revenue, 2),
            "blended_roas": round(current_roas, 2),
        },
        "optimized_allocation": {
            "total_spend": round(total_budget, 2),
            "total_revenue": opt_total_revenue,
            "blended_roas": round(opt_roas, 2),
            "test_budget": round(test_budget, 2),
            "channels": opt_channels,
        },
        "projected_improvement": {
            "revenue_change": revenue_change,
            "revenue_change_percent": revenue_change_pct,
            "roas_change": roas_change,
        },
        "recommendations": recs,
    }


def generate_recommendations(channels, opt_channels, test_budget):
    """Gera recomendações de realocação acionáveis."""
    recs = []

    # Identifica maiores aumentos e reduções
    increases = sorted(
        [c for c in opt_channels if c["change_percent"] is not None and c["change_percent"] > 5],
        key=lambda c: c["change_percent"],
        reverse=True,
    )
    decreases = sorted(
        [c for c in opt_channels if c["change_percent"] is not None and c["change_percent"] < -5],
        key=lambda c: c["change_percent"],
    )

    for inc in increases[:2]:
        # Encontra de onde vem o orçamento
        source = decreases[0]["name"] if decreases else "underperforming channels"
        shift = round(inc["optimized_spend"] - inc["current_spend"], 2)
        recs.append(
            f"Realoque ${shift:,.0f} de {source} para {inc['name']} "
            f"(maior eficiência marginal)"
        )

    for dec in decreases[:2]:
        recs.append(
            f"Reduza {dec['name']} em {abs(dec['change_percent']):.0f}% "
            f"\u2014 ROAS atual ({dec['current_roas']}x) está abaixo do ideal"
        )

    # Canais com variação mínima
    stable = [
        c for c in opt_channels
        if c["change_percent"] is not None and abs(c["change_percent"]) <= 5
    ]
    for ch in stable:
        recs.append(
            f"Mantenha {ch['name']} no nível atual (já próximo do ideal)"
        )

    if test_budget > 0:
        recs.append(
            f"Reserve ${test_budget:,.0f} ({test_budget / sum(c['optimized_spend'] for c in opt_channels) * 100 if sum(c['optimized_spend'] for c in opt_channels) > 0 else 0:.0f}%) "
            f"para testar novos canais"
        )

    if not recs:
        recs.append(
            "Alocação atual já está bem balanceada. Foque em otimização criativa "
            "dentro dos canais existentes."
        )

    return recs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Otimizador de realocação de orçamento de marketing orientado por dados"
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
        "--total-budget", type=float, required=True,
        help="Orçamento total disponível para realocação",
    )
    parser.add_argument(
        "--min-spend", type=float, default=0,
        help="Gasto mínimo por canal (padrão: 0)",
    )
    parser.add_argument(
        "--test-budget-pct", type=float, default=10,
        help="Percentual de orçamento para reservar para testes (padrão: 10)",
    )
    args = parser.parse_args()

    # --- Carregar e validar ---
    channels, err = load_channels(args)
    if err:
        json.dump({"error": err}, sys.stdout, indent=2)
        print()
        return

    if args.total_budget <= 0:
        json.dump({"error": "total-budget deve ser um número positivo"}, sys.stdout, indent=2)
        print()
        return

    if args.min_spend < 0:
        json.dump({"error": "min-spend deve ser não-negativo"}, sys.stdout, indent=2)
        print()
        return

    if not (0 <= args.test_budget_pct < 100):
        json.dump({"error": "test-budget-pct deve estar entre 0 e 99"}, sys.stdout, indent=2)
        print()
        return

    # --- Otimizar ---
    allocation, test_budget = optimise(
        channels, args.total_budget, args.min_spend, args.test_budget_pct
    )

    # --- Construir e emitir saída ---
    output = build_output(channels, allocation, test_budget, args.total_budget)
    json.dump(output, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
