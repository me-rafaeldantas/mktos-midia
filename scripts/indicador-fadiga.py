#!/usr/bin/env python3
"""
indicador-fadiga.py
=============================
Prevê fadiga de criativos publicitários e rastreia decaimento de conteúdo.

Pontua saúde criativa a partir de métricas de desempenho, prevê datas de fadiga usando
análise de tendências, gera briefs de refresh, examina bibliotecas de conteúdo em busca
de decaimento e prioriza trabalho de refresh por impacto no negócio.

Armazenamento: ./data/clientes/{slug}/creative/

Dependências: nenhuma (stdlib apenas)

Uso:
    python indicador-fadiga.py --action score-health --creative-id ad_001 --data '{"impressions":50000,"frequency":4.2,"ctr_current":0.018,"ctr_baseline":0.025,"cpm_current":12.5,"cpm_baseline":9.0,"engagement_rate_current":0.03,"engagement_rate_baseline":0.05,"days_running":28,"audience_size":200000}'
    python indicador-fadiga.py --action predict-fatigue --creative-id ad_001 --performance-history '[{"date":"2026-01-01","impressions":5000,"ctr":0.025,"cpm":9.0,"engagement_rate":0.05}]'
    python indicador-fadiga.py --action generate-refresh-brief --creative-id ad_001 --data '{"format":"image","channel":"facebook","target_audience":"25-34 profissionais","current_headline":"Experimente grátis","current_cta":"Começar agora","current_visual_description":"Screenshot do produto","performing_elements":["headline"],"fatiguing_elements":["visual"]}'
    python indicador-fadiga.py --action decay-scan --data '[{"content_id":"blog_01","url":"/blog/guia-seo","title":"Guia SEO","monthly_traffic_current":1200,"monthly_traffic_previous":1800,"monthly_traffic_6mo_ago":2500,"keyword_positions_current":{"dicas seo":12},"keyword_positions_previous":{"dicas seo":7},"publish_date":"2024-06-15","last_updated":"2025-01-10","backlinks":45}]'
    python indicador-fadiga.py --action priority-refresh --data '[{"content_id":"blog_01","monthly_traffic_current":1200,"monthly_traffic_previous":2500,"conversion_rate":0.03,"revenue_per_conversion":50}]'
    python indicador-fadiga.py --action batch-health --data '[...]'
"""

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

CLIENTES_DIR = Path(__file__).parent.parent / "data" / "clientes"


def _clamp(val, lo=0.0, hi=100.0):
    return max(lo, min(hi, val))


# ── Regressão linear (stdlib) ──────────────────────────────────────────────

def _linear_regression(x, y):
    """Coeficiente angular e intercepto por OLS."""
    n = len(x)
    if n < 2:
        return 0.0, y[0] if y else 0.0
    sx = sum(x)
    sy = sum(y)
    sxy = sum(a * b for a, b in zip(x, y))
    sx2 = sum(a * a for a in x)
    denom = n * sx2 - sx * sx
    if denom == 0:
        return 0.0, sy / n
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n
    return slope, intercept


# ── Pontuação de Saúde ───────────────────────────────────────────────────────

def score_health(creative_id, data):
    ctr_cur = data.get("ctr_current", 0)
    ctr_base = data.get("ctr_baseline", 1)
    cpm_cur = data.get("cpm_current", 0)
    cpm_base = data.get("cpm_baseline", 1)
    eng_cur = data.get("engagement_rate_current", 0)
    eng_base = data.get("engagement_rate_baseline", 1)
    frequency = data.get("frequency", 1)
    days = data.get("days_running", 0)
    audience = data.get("audience_size", 100000)

    factors = []

    # Razão CTR (30%) — maior é mais saudável
    ctr_ratio = (ctr_cur / ctr_base) if ctr_base > 0 else 0
    ctr_score = _clamp(ctr_ratio * 100)
    factors.append({"factor": "ctr_ratio", "score": round(ctr_score, 1), "weight": 0.30, "detail": f"{ctr_ratio:.2f}x baseline"})

    # Razão CPM (20%) — menor é mais saudável (invertido)
    cpm_ratio = (cpm_base / cpm_cur) if cpm_cur > 0 else 1
    cpm_score = _clamp(cpm_ratio * 100)
    factors.append({"factor": "cpm_ratio", "score": round(cpm_score, 1), "weight": 0.20, "detail": f"baseline/atual = {cpm_ratio:.2f}"})

    # Razão de engajamento (20%)
    eng_ratio = (eng_cur / eng_base) if eng_base > 0 else 0
    eng_score = _clamp(eng_ratio * 100)
    factors.append({"factor": "engagement_ratio", "score": round(eng_score, 1), "weight": 0.20, "detail": f"{eng_ratio:.2f}x baseline"})

    # Fadiga por frequência (20%) — limiar escala com tamanho da audiência
    fatigue_threshold = max(3.0, math.log10(audience) - 1)
    freq_ratio = frequency / fatigue_threshold if fatigue_threshold > 0 else 1
    freq_score = _clamp((1 - max(0, freq_ratio - 1)) * 100) if freq_ratio > 1 else 100.0
    factors.append({"factor": "frequency_fatigue", "score": round(freq_score, 1), "weight": 0.20, "detail": f"freq {frequency:.1f} vs limiar {fatigue_threshold:.1f}"})

    # Decaimento por dias rodando (10%) — decaimento gradual após 14 dias
    if days <= 14:
        days_score = 100.0
    else:
        days_score = _clamp(100 - (days - 14) * 2)
    factors.append({"factor": "days_running", "score": round(days_score, 1), "weight": 0.10, "detail": f"{days} dias"})

    # Total ponderado
    health = sum(f["score"] * f["weight"] for f in factors)
    health = round(_clamp(health), 1)

    if health >= 75:
        risk = "healthy"
    elif health >= 50:
        risk = "watch"
    elif health >= 25:
        risk = "fatiguing"
    else:
        risk = "critical"

    # Estima dias até a fadiga (extrapolação linear simples da taxa de queda de CTR)
    if ctr_ratio < 1 and ctr_ratio > 0 and days > 0:
        daily_decay = (1 - ctr_ratio) / days
        remaining_ratio = ctr_ratio - 0.7  # fatigue at 70% of baseline
        days_to_fatigue = max(0, int(remaining_ratio / daily_decay)) if daily_decay > 0 else 999
    else:
        days_to_fatigue = None

    return {
        "creative_id": creative_id,
        "health_score": health,
        "risk_level": risk,
        "days_to_fatigue_estimate": days_to_fatigue,
        "contributing_factors": factors,
    }


# ── Previsão de Fadiga ───────────────────────────────────────────────────────

def predict_fatigue(creative_id, history):
    if len(history) < 3:
        return {"creative_id": creative_id, "error": "São necessários pelo menos 3 pontos de dados para previsão"}

    x = list(range(len(history)))
    ctrs = [h.get("ctr", 0) for h in history]
    cpms = [h.get("cpm", 0) for h in history]

    ctr_slope, ctr_intercept = _linear_regression(x, ctrs)
    cpm_slope, cpm_intercept = _linear_regression(x, cpms)

    baseline_ctr = ctrs[0] if ctrs[0] > 0 else 0.01
    baseline_cpm = cpms[0] if cpms[0] > 0 else 1.0
    fatigue_ctr = baseline_ctr * 0.70
    fatigue_cpm = baseline_cpm * 1.30

    # Encontra pontos de cruzamento
    ctr_days = None
    if ctr_slope < 0:
        # Resolve: ctr_slope * x + ctr_intercept = fatigue_ctr
        ctr_x = (fatigue_ctr - ctr_intercept) / ctr_slope
        if ctr_x > len(history):
            ctr_days = int(ctr_x - len(history))

    cpm_days = None
    if cpm_slope > 0:
        cpm_x = (fatigue_cpm - cpm_intercept) / cpm_slope
        if cpm_x > len(history):
            cpm_days = int(cpm_x - len(history))

    # Pega o mais próximo dos dois
    candidates = [d for d in [ctr_days, cpm_days] if d is not None]
    days_remaining = min(candidates) if candidates else None

    # Confiança baseada em pontos de dados e clareza da tendência
    n = len(history)
    if n >= 14:
        confidence = "high"
    elif n >= 7:
        confidence = "medium"
    else:
        confidence = "low"

    # Data prevista de fadiga
    predicted_date = None
    if days_remaining is not None:
        try:
            last_date = datetime.strptime(history[-1]["date"], "%Y-%m-%d")
            from datetime import timedelta
            predicted_date = (last_date + timedelta(days=days_remaining)).strftime("%Y-%m-%d")
        except (KeyError, ValueError):
            pass

    # Recomendação
    if days_remaining is None:
        rec = "Nenhuma tendência de fadiga detectada. Criativo está performando de forma estável."
    elif days_remaining <= 7:
        rec = "URGENTE: Fadiga de criativo iminente. Prepare um criativo substituto imediatamente."
    elif days_remaining <= 14:
        rec = "Criativo se aproximando da fadiga. Comece a desenvolver variantes de refresh agora."
    elif days_remaining <= 30:
        rec = "Criativo tem fôlego mas planeje refresh no próximo sprint."
    else:
        rec = "Criativo saudável. Agende revisão de rotina em 2-4 semanas."

    return {
        "creative_id": creative_id,
        "predicted_fatigue_date": predicted_date,
        "days_remaining": days_remaining,
        "confidence": confidence,
        "ctr_trend_slope": round(ctr_slope, 6),
        "cpm_trend_slope": round(cpm_slope, 4),
        "recommendation": rec,
    }


# ── Geração de Brief de Refresh ──────────────────────────────────────────────

def generate_refresh_brief(creative_id, data):
    fmt = data.get("format", "image")
    channel = data.get("channel", "unknown")
    audience = data.get("target_audience", "")
    performing = data.get("performing_elements", [])
    fatiguing = data.get("fatiguing_elements", [])

    keep = [f"Manter: {e} (performando bem)" for e in performing]
    if not keep:
        keep = ["Nenhum elemento de alto desempenho identificado — considere revisão completa do criativo"]

    change = [f"Renovar: {e} (sinais de fadiga detectados)" for e in fatiguing]
    if not change:
        change = ["Teste mudanças visuais incrementais primeiro"]

    # Sugestões de teste por formato
    test_map = {
        "image": ["Nova imagem principal com paleta de cores diferente", "Ângulo alternativo do produto ou foto lifestyle", "Variante com conteúdo gerado por usuário (UGC)"],
        "video": ["Novo gancho de abertura (primeiros 3 segundos)", "Frame de thumbnail diferente", "Versão mais curta"],
        "text": ["Novo ângulo de headline", "Proposta de valor diferente no lead", "Cópia baseada em pergunta vs afirmação"],
        "carousel": ["Reordenar sequência de cards", "Substituir card com pior desempenho", "Primeiro card novo com gancho diferente"],
    }
    tests = test_map.get(fmt, ["Teste A/B do visual principal", "Testar headline alternativa", "Experimentar CTA diferente"])

    angle_map = {
        "image": ["Prova social / depoimento sobreposto", "Comparativo antes/depois", "Design com tipografia em destaque"],
        "video": ["Formato história do cliente", "Estrutura problema-agitação-solução", "Ângulo bastidores"],
        "text": ["Dado ou estatística como abertura", "Benefício emocional em destaque", "Enquadramento de urgência/escassez"],
        "carousel": ["Arco narrativo entre cards", "Formato comparativo/lista", "Estilo quiz interativo"],
    }
    angles = angle_map.get(fmt, ["Novo ângulo criativo recomendado"])

    urgency = "high" if len(fatiguing) > len(performing) else ("medium" if fatiguing else "low")

    return {
        "creative_id": creative_id,
        "refresh_brief": {
            "format": fmt,
            "channel": channel,
            "target_audience": audience,
            "what_to_keep": keep,
            "what_to_change": change,
            "what_to_test": tests,
            "suggested_angles": angles,
            "urgency": urgency,
        },
    }


# ── Varredura de Decaimento ──────────────────────────────────────────────────

def decay_scan(items):
    results = []
    for item in items:
        cid = item.get("content_id", "unknown")
        traffic_cur = item.get("monthly_traffic_current", 0)
        traffic_prev = item.get("monthly_traffic_previous", 0)
        traffic_6mo = item.get("monthly_traffic_6mo_ago", 0)
        kw_cur = item.get("keyword_positions_current", {})
        kw_prev = item.get("keyword_positions_previous", {})
        publish_date = item.get("publish_date", "")
        last_updated = item.get("last_updated", "")

        signals = []
        decay_score = 0

        # Queda de tráfego
        if traffic_prev > 0:
            traffic_drop = (traffic_prev - traffic_cur) / traffic_prev
            if traffic_drop > 0.3:
                signals.append(f"Tráfego caiu {traffic_drop:.0%} vs mês anterior")
                decay_score += 30
            elif traffic_drop > 0.1:
                signals.append(f"Tráfego decaiu {traffic_drop:.0%} vs mês anterior")
                decay_score += 15

        if traffic_6mo > 0:
            long_drop = (traffic_6mo - traffic_cur) / traffic_6mo
            if long_drop > 0.5:
                signals.append(f"Tráfego caiu {long_drop:.0%} vs 6 meses atrás")
                decay_score += 25

        # Queda de posições de palavras-chave
        pos_drops = 0
        for kw in kw_cur:
            cur_pos = kw_cur[kw]
            prev_pos = kw_prev.get(kw)
            if prev_pos is not None and cur_pos > prev_pos + 3:
                pos_drops += 1
        if pos_drops > 0:
            signals.append(f"{pos_drops} palavra(s)-chave perderam 3+ posições")
            decay_score += min(25, pos_drops * 10)

        # Idade do conteúdo
        if last_updated:
            try:
                upd = datetime.strptime(last_updated[:10], "%Y-%m-%d")
                months_stale = (datetime.now() - upd).days / 30
                if months_stale > 12:
                    signals.append(f"Sem atualização há {int(months_stale)} meses")
                    decay_score += 20
                elif months_stale > 6:
                    signals.append(f"Última atualização há {int(months_stale)} meses")
                    decay_score += 10
            except ValueError:
                pass

        decay_score = min(100, decay_score)

        if decay_score >= 60:
            action = "rewrite"
        elif decay_score >= 40:
            action = "major-refresh"
        elif decay_score >= 20:
            action = "minor-refresh"
        elif decay_score >= 10:
            action = "consolidate"
        else:
            action = "no-action"

        if not signals:
            signals.append("Nenhum sinal de decaimento detectado")

        # Prioridade: impacto de tráfego x severidade do decaimento
        priority = round(traffic_cur * (decay_score / 100), 1)

        results.append({
            "content_id": cid,
            "title": item.get("title", ""),
            "decay_score": decay_score,
            "signals_detected": signals,
            "recommended_action": action,
            "priority_score": priority,
        })

    results.sort(key=lambda r: -r["priority_score"])
    return results


# ── Refresh Prioritário ──────────────────────────────────────────────────────

def priority_refresh(items):
    results = []
    for item in items:
        cid = item.get("content_id", "unknown")
        traffic = item.get("monthly_traffic_current", 0)
        traffic_prev = item.get("monthly_traffic_previous", 0)
        cr = item.get("conversion_rate", 0)
        rev = item.get("revenue_per_conversion", 0)

        decay_sev = 0
        if traffic_prev > 0:
            decay_sev = max(0, (traffic_prev - traffic) / traffic_prev)

        priority = round(traffic * cr * rev * max(0.1, decay_sev), 2)
        results.append({
            "content_id": cid,
            "monthly_traffic": traffic,
            "decay_severity": round(decay_sev, 3),
            "conversion_rate": cr,
            "revenue_per_conversion": rev,
            "priority_score": priority,
            "monthly_revenue_at_risk": round(traffic * cr * rev * decay_sev, 2),
        })

    results.sort(key=lambda r: -r["priority_score"])
    return results


# ── Saúde em Lote ────────────────────────────────────────────────────────────

def batch_health(items):
    results = []
    for item in items:
        cid = item.pop("creative_id", item.pop("id", "unknown"))
        result = score_health(cid, item)
        results.append(result)
    results.sort(key=lambda r: r["health_score"])
    return results


# ── Interface de Linha de Comando (CLI) ──────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Indicador de Fadiga de Criativos — Prevê fadiga de anúncios e rastreia decaimento de conteúdo para mktOS Mídia"
    )
    parser.add_argument("--action", required=True,
                        choices=["score-health", "predict-fatigue",
                                 "generate-refresh-brief", "decay-scan",
                                 "priority-refresh", "batch-health"],
                        help="Ação a executar")
    parser.add_argument("--creative-id", help="Identificador do criativo/anúncio")
    parser.add_argument("--data", help="Objeto ou array JSON de dados")
    parser.add_argument("--performance-history",
                        help="Array JSON de dados de desempenho diário (para predict-fatigue)")

    args = parser.parse_args()

    def _parse_json(raw, label="--data"):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"JSON inválido em {label}: {e}"}))
            sys.exit(1)

    if args.action == "score-health":
        if not args.creative_id or not args.data:
            print(json.dumps({"error": "--creative-id e --data são obrigatórios para score-health"}))
            sys.exit(1)
        result = score_health(args.creative_id, _parse_json(args.data))

    elif args.action == "predict-fatigue":
        if not args.creative_id or not args.performance_history:
            print(json.dumps({"error": "--creative-id e --performance-history são obrigatórios para predict-fatigue"}))
            sys.exit(1)
        result = predict_fatigue(args.creative_id, _parse_json(args.performance_history, "--performance-history"))

    elif args.action == "generate-refresh-brief":
        if not args.creative_id or not args.data:
            print(json.dumps({"error": "--creative-id e --data são obrigatórios para generate-refresh-brief"}))
            sys.exit(1)
        result = generate_refresh_brief(args.creative_id, _parse_json(args.data))

    elif args.action == "decay-scan":
        if not args.data:
            print(json.dumps({"error": "--data é obrigatório para decay-scan (array JSON)"}))
            sys.exit(1)
        data = _parse_json(args.data)
        if not isinstance(data, list):
            print(json.dumps({"error": "--data deve ser um array JSON para decay-scan"}))
            sys.exit(1)
        result = decay_scan(data)

    elif args.action == "priority-refresh":
        if not args.data:
            print(json.dumps({"error": "--data é obrigatório para priority-refresh (array JSON)"}))
            sys.exit(1)
        data = _parse_json(args.data)
        if not isinstance(data, list):
            print(json.dumps({"error": "--data deve ser um array JSON para priority-refresh"}))
            sys.exit(1)
        result = priority_refresh(data)

    elif args.action == "batch-health":
        if not args.data:
            print(json.dumps({"error": "--data é obrigatório para batch-health (array JSON)"}))
            sys.exit(1)
        data = _parse_json(args.data)
        if not isinstance(data, list):
            print(json.dumps({"error": "--data deve ser um array JSON para batch-health"}))
            sys.exit(1)
        result = batch_health(data)

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
