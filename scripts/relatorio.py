#!/usr/bin/env python3
"""
relatorio.py
=========================
Gerador de relatórios de mídia cross-platform para mktOS Mídia.

Calcula ROAS, CPA, CPL, CTR e CPM por canal, consolida métricas cross-platform,
aplica comparação período-a-período com semáforo e gera relatório formatado
adaptado à audiência (cliente ou equipe interna).

Uso:
    python relatorio.py \
        --brand teste-cliente \
        --period "2026-05-01:2026-05-31" \
        --channels '[{"nome":"Google Ads","spend":5000,"impressions":80000,"clicks":1500,"conversions":100,"revenue":25000}]' \
        --format markdown \
        --audience client

    # Com comparativo PoP
    python relatorio.py \
        --brand teste-cliente \
        --period "2026-05-01:2026-05-31" \
        --channels '[...]' \
        --previous-period '[...]' \
        --format markdown \
        --audience internal
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

CLIENTES_DIR = Path(__file__).parent.parent / "data" / "clientes"

# Semáforo de variação PoP
TRAFFIC_GREEN  = "🟢"
TRAFFIC_YELLOW = "🟡"
TRAFFIC_RED    = "🔴"


# ---------------------------------------------------------------------------
# Cálculo de métricas
# ---------------------------------------------------------------------------

def _safe_div(numerator, denominator, multiplier=1):
    if denominator and denominator > 0:
        return round(numerator / denominator * multiplier, 2)
    return None


def _pct_change(current, previous):
    if previous and previous > 0 and current is not None:
        return round((current - previous) / previous * 100, 1)
    return None


def _traffic_light(pct, cost_metric=False):
    """🟢 bom / 🟡 neutro / 🔴 ruim. Para métricas de custo, direção invertida."""
    if pct is None:
        return "—"
    if cost_metric:
        return TRAFFIC_GREEN if pct <= -5 else (TRAFFIC_RED if pct >= 5 else TRAFFIC_YELLOW)
    return TRAFFIC_GREEN if pct >= 5 else (TRAFFIC_RED if pct <= -5 else TRAFFIC_YELLOW)


def calc_channel(ch):
    """Calcula todas as métricas de um canal a partir dos dados brutos."""
    spend       = ch.get("spend", 0) or 0
    impressions = ch.get("impressions", 0) or 0
    clicks      = ch.get("clicks", 0) or 0
    conversions = ch.get("conversions", 0) or 0
    revenue     = ch.get("revenue", 0) or 0
    leads       = ch.get("leads", 0) or 0

    return {
        "nome":        ch.get("nome", ch.get("name", "Canal")),
        "spend":       round(spend, 2),
        "impressions": impressions,
        "clicks":      clicks,
        "conversions": conversions,
        "leads":       leads,
        "revenue":     round(revenue, 2),
        "roas":        _safe_div(revenue, spend),
        "cpa":         _safe_div(spend, conversions),
        "cpl":         _safe_div(spend, leads) if leads > 0 else None,
        "ctr":         _safe_div(clicks, impressions, 100),
        "cpm":         _safe_div(spend, impressions, 1000),
    }


def calc_summary(channels):
    """Agrega métricas de todos os canais."""
    total_spend       = sum(c["spend"] for c in channels)
    total_impressions = sum(c["impressions"] for c in channels)
    total_clicks      = sum(c["clicks"] for c in channels)
    total_conversions = sum(c["conversions"] for c in channels)
    total_revenue     = sum(c["revenue"] for c in channels)
    total_leads       = sum(c["leads"] for c in channels)

    return {
        "total_spend":       round(total_spend, 2),
        "total_impressions": total_impressions,
        "total_clicks":      total_clicks,
        "total_conversions": total_conversions,
        "total_revenue":     round(total_revenue, 2),
        "total_leads":       total_leads,
        "blended_roas":      _safe_div(total_revenue, total_spend),
        "blended_cpa":       _safe_div(total_spend, total_conversions),
        "blended_cpl":       _safe_div(total_spend, total_leads) if total_leads > 0 else None,
        "blended_ctr":       _safe_div(total_clicks, total_impressions, 100),
        "blended_cpm":       _safe_div(total_spend, total_impressions, 1000),
    }


def calc_pop(current, previous):
    """Calcula variação PoP entre dois dicts de métricas."""
    metrics = ["spend", "impressions", "clicks", "conversions", "leads", "revenue",
               "roas", "cpa", "cpl", "ctr", "cpm",
               "total_spend", "total_impressions", "total_clicks", "total_conversions",
               "total_revenue", "total_leads", "blended_roas", "blended_cpa",
               "blended_cpl", "blended_ctr", "blended_cpm"]
    cost_metrics = {"cpa", "cpl", "cpm", "spend", "total_spend",
                    "blended_cpa", "blended_cpl", "blended_cpm"}
    result = {}
    for m in metrics:
        if m in current and m in previous:
            pct = _pct_change(current.get(m), previous.get(m))
            result[m] = {
                "current":  current.get(m),
                "previous": previous.get(m),
                "pct":      pct,
                "signal":   _traffic_light(pct, cost_metric=(m in cost_metrics)),
            }
    return result


# ---------------------------------------------------------------------------
# Benchmarks vs. KPI targets
# ---------------------------------------------------------------------------

def compare_kpis(summary, kpis, moeda):
    """Compara métricas atuais com targets do perfil.json."""
    checks = []
    mappings = [
        ("roas_target",  "blended_roas", "ROAS",  False),
        ("cpa_target",   "blended_cpa",  "CPA",   True),
        ("cpl_target",   "blended_cpl",  "CPL",   True),
        ("ctr_target",   "blended_ctr",  "CTR",   False),
    ]
    for kpi_key, summary_key, label, lower_is_better in mappings:
        target = kpis.get(kpi_key)
        actual = summary.get(summary_key)
        if target is None or actual is None:
            continue
        pct = _pct_change(actual, target)
        if lower_is_better:
            ok = actual <= target
            signal = TRAFFIC_GREEN if ok else TRAFFIC_RED
        else:
            ok = actual >= target
            signal = TRAFFIC_GREEN if ok else TRAFFIC_RED
        suffix = "x" if "roas" in kpi_key else ("%" if "ctr" in kpi_key else f" {moeda}")
        checks.append({
            "kpi":     label,
            "actual":  actual,
            "target":  target,
            "signal":  signal,
            "status":  "atingido" if ok else "abaixo da meta",
            "suffix":  suffix,
        })
    return checks


# ---------------------------------------------------------------------------
# Formatação Markdown
# ---------------------------------------------------------------------------

def _fmt(value, moeda="R$", suffix=""):
    if value is None:
        return "—"
    if suffix == "x":
        return f"{value:.2f}x"
    if suffix == "%":
        return f"{value:.2f}%"
    return f"{moeda} {value:,.2f}"


def _pop_row(label, pop_data, key, moeda="R$", suffix="", integer=False):
    if key not in pop_data:
        return ""
    d = pop_data[key]
    pct_str = f"{d['pct']:+.1f}%" if d["pct"] is not None else "—"

    def _fv(v):
        if v is None:
            return "—"
        if integer:
            return f"{int(v):,}"
        return _fmt(v, moeda, suffix)

    return (
        f"| {label} | {_fv(d['previous'])} | {_fv(d['current'])} | {pct_str} {d['signal']} |"
    )


def render_markdown(brand_name, period, channels_data, summary,
                    pop_channels, pop_summary, kpi_checks,
                    audience, moeda="R$"):
    lines = []
    now   = datetime.now().strftime("%d/%m/%Y")

    # Cabeçalho
    lines.append(f"# Relatório de Mídia — {brand_name}")
    lines.append(f"**Período:** {period}  |  **Gerado em:** {now}  |  "
                 f"**Audiência:** {'Cliente' if audience == 'client' else 'Equipe Interna'}\n")

    # Executive summary — adaptado por audiência
    lines.append("## Resumo Executivo\n")
    roas_str = f"{summary['blended_roas']:.2f}x" if summary["blended_roas"] else "—"
    cpa_str  = f"{moeda} {summary['blended_cpa']:,.2f}" if summary["blended_cpa"] else "—"
    cpl_str  = f"{moeda} {summary['blended_cpl']:,.2f}" if summary["blended_cpl"] else "—"

    if audience == "client":
        lines.append(
            f"No período de **{period}**, as campanhas geraram "
            f"**{summary['total_conversions']} conversões** "
            + (f"e **{summary['total_leads']} leads** " if summary["total_leads"] > 0 else "")
            + f"com investimento total de **{moeda} {summary['total_spend']:,.2f}**. "
            f"Para cada R$ 1,00 investido, o retorno foi de **{roas_str}** em valor de conversão. "
            f"O custo médio por resultado foi de **{cpl_str if summary['total_leads'] > 0 else cpa_str}**."
        )
    else:
        best = max(channels_data, key=lambda c: c["roas"] or 0, default=None)
        worst = min(channels_data, key=lambda c: c["roas"] or 0, default=None)
        lines.append(
            f"**Canal mais eficiente:** {best['nome']} (ROAS {best['roas']:.2f}x)  \n"
            f"**Canal menos eficiente:** {worst['nome'] if worst != best else '—'} "
            + (f"(ROAS {worst['roas']:.2f}x)" if worst != best and worst["roas"] else "")
            + f"  \n**ROAS blended:** {roas_str}  |  **CPA médio:** {cpa_str}"
        )
    lines.append("")

    # KPI targets
    if kpi_checks:
        lines.append("## Metas vs. Realizado\n")
        lines.append("| KPI | Meta | Realizado | Status |")
        lines.append("|-----|------|-----------|--------|")
        for k in kpi_checks:
            lines.append(
                f"| {k['kpi']} | {k['target']}{k['suffix']} | "
                f"{k['actual']}{k['suffix']} | {k['signal']} {k['status']} |"
            )
        lines.append("")

    # Tabela por plataforma
    def _cell(val, prefix="", suffix=""):
        if val is None:
            return "—"
        if prefix:
            return f"{prefix} {val:,.2f}{suffix}"
        return f"{val:,.2f}{suffix}" if isinstance(val, float) else str(val)

    lines.append("## Resultados por Plataforma\n")
    lines.append("| Plataforma | Gasto | Impressões | Cliques | CTR | CPM | Conversões | ROAS | CPA |")
    lines.append("|-----------|-------|-----------|---------|-----|-----|-----------|------|-----|")
    for c in channels_data:
        row = (
            f"| {c['nome']} "
            f"| {moeda} {c['spend']:,.2f} "
            f"| {c['impressions']:,} "
            f"| {c['clicks']:,} "
            f"| {_cell(c['ctr'], suffix='%')} "
            f"| {_cell(c['cpm'], prefix=moeda)} "
            f"| {c['conversions']} "
            f"| {_cell(c['roas'], suffix='x')} "
            f"| {_cell(c['cpa'], prefix=moeda)} |"
        )
        lines.append(row)

    # Linha de totais
    s = summary
    tot = (
        f"| **Total** "
        f"| **{moeda} {s['total_spend']:,.2f}** "
        f"| **{s['total_impressions']:,}** "
        f"| **{s['total_clicks']:,}** "
        f"| **{_cell(s['blended_ctr'], suffix='%')}** "
        f"| **{_cell(s['blended_cpm'], prefix=moeda)}** "
        f"| **{s['total_conversions']}** "
        f"| **{_cell(s['blended_roas'], suffix='x')}** "
        f"| **{_cell(s['blended_cpa'], prefix=moeda)}** |"
    )
    lines.append(tot)
    lines.append("")

    # Comparativo PoP
    if pop_summary:
        lines.append("## Comparativo Período Anterior\n")
        lines.append("| Métrica | Período Anterior | Período Atual | Variação |")
        lines.append("|---------|-----------------|---------------|----------|")
        lines.append(_pop_row("Gasto total",    pop_summary, "total_spend",       moeda))
        lines.append(_pop_row("Impressões",     pop_summary, "total_impressions", integer=True))
        lines.append(_pop_row("Cliques",        pop_summary, "total_clicks",      integer=True))
        lines.append(_pop_row("Conversões",     pop_summary, "total_conversions", integer=True))
        lines.append(_pop_row("Receita",        pop_summary, "total_revenue",     moeda))
        lines.append(_pop_row("ROAS blended",   pop_summary, "blended_roas",      suffix="x"))
        lines.append(_pop_row("CPA médio",      pop_summary, "blended_cpa",       moeda))
        lines.append(_pop_row("CTR médio",      pop_summary, "blended_ctr",       suffix="%"))
        lines.append(_pop_row("CPM médio",      pop_summary, "blended_cpm",       moeda))
        lines.append("")

    # Seção interna: oportunidades de realocação
    if audience == "internal" and len(channels_data) > 1:
        valid = [c for c in channels_data if c["roas"] is not None]
        if valid:
            sorted_c = sorted(valid, key=lambda c: c["roas"], reverse=True)
            lines.append("## Oportunidades de Otimização (Uso Interno)\n")
            lines.append(f"**Ranking de eficiência por ROAS:** "
                         + " > ".join(f"{c['nome']} ({c['roas']:.2f}x)" for c in sorted_c))
            lines.append("")

            # Share de gasto vs. share de conversões
            total_spend_val = s["total_spend"] or 1
            total_conv_val  = s["total_conversions"] or 1
            lines.append("| Canal | Share de Gasto | Share de Conversões | Eficiência |")
            lines.append("|-------|---------------|---------------------|-----------|")
            for c in sorted_c:
                spend_share = c["spend"] / total_spend_val * 100
                conv_share  = c["conversions"] / total_conv_val * 100 if total_conv_val > 0 else 0
                efficiency  = TRAFFIC_GREEN if conv_share > spend_share else TRAFFIC_RED
                lines.append(
                    f"| {c['nome']} | {spend_share:.1f}% | {conv_share:.1f}% | {efficiency} |"
                )
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Carregamento de dados
# ---------------------------------------------------------------------------

def load_profile(slug):
    """Lê perfil.json do cliente. Retorna dict vazio se não encontrado."""
    if not slug:
        return {}
    path = CLIENTES_DIR / slug / "perfil.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def parse_channels(raw):
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else [data], None
    except json.JSONDecodeError as e:
        return None, f"JSON inválido: {e}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Gerador de relatórios de mídia cross-platform"
    )
    parser.add_argument("--brand",           default="", help="Slug do cliente")
    parser.add_argument("--period",          default="", help="Período atual (YYYY-MM-DD:YYYY-MM-DD)")
    parser.add_argument("--channels",        required=True,
                        help='Array JSON de canais com spend, impressions, clicks, conversions, revenue')
    parser.add_argument("--previous-period", default="",
                        help="Array JSON dos mesmos canais no período anterior (para PoP)")
    parser.add_argument("--format",          choices=["markdown", "json"], default="markdown")
    parser.add_argument("--audience",        choices=["client", "internal"], default="client")

    args = parser.parse_args()

    channels_raw, err = parse_channels(args.channels)
    if err:
        print(json.dumps({"error": f"--channels: {err}"}, ensure_ascii=False))
        sys.exit(1)

    prev_raw = None
    if args.previous_period:
        prev_raw, err = parse_channels(args.previous_period)
        if err:
            print(json.dumps({"error": f"--previous-period: {err}"}, ensure_ascii=False))
            sys.exit(1)

    # Perfil do cliente
    profile  = load_profile(args.brand)
    moeda    = profile.get("moeda", "R$")
    kpis     = profile.get("kpis", {})
    nome     = profile.get("nome", args.brand or "Cliente")

    # Cálculo
    channels_data = [calc_channel(c) for c in channels_raw]
    summary       = calc_summary(channels_data)
    kpi_checks    = compare_kpis(summary, kpis, moeda)

    pop_summary  = None
    pop_channels = []
    if prev_raw:
        prev_data   = [calc_channel(c) for c in prev_raw]
        prev_summary = calc_summary(prev_data)
        pop_summary  = calc_pop(summary, prev_summary)
        pop_channels = [calc_pop(c, p) for c, p in zip(channels_data, prev_data)]

    if args.format == "json":
        output = {
            "brand":       args.brand,
            "period":      args.period,
            "audience":    args.audience,
            "channels":    channels_data,
            "summary":     summary,
            "kpi_checks":  kpi_checks,
            "pop_summary": pop_summary,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        md = render_markdown(
            brand_name=nome,
            period=args.period or "período informado",
            channels_data=channels_data,
            summary=summary,
            pop_channels=pop_channels,
            pop_summary=pop_summary,
            kpi_checks=kpi_checks,
            audience=args.audience,
            moeda=moeda,
        )
        print(md)


if __name__ == "__main__":
    main()
