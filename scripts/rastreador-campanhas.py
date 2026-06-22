#!/usr/bin/env python3
"""
rastreador-campanhas.py
===================
Armazenamento e recuperação persistente de dados de campanha para mktOS Mídia.

Armazena planos de campanha, snapshots de desempenho e aprendizados no diretório
./data/clientes/{slug}/ do cliente para que o plugin possa referenciar
trabalhos passados e melhorar recomendações ao longo do tempo.

Uso:
    python rastreador-campanhas.py --brand acme --action save-campaign --data '{"name": "Q1 Launch", ...}'
    python rastreador-campanhas.py --brand acme --action list-campaigns
    python rastreador-campanhas.py --brand acme --action get-campaign --id q1-launch-2026
    python rastreador-campanhas.py --brand acme --action save-insight --data '{"type": "learning", ...}'
    python rastreador-campanhas.py --brand acme --action get-insights
    python rastreador-campanhas.py --brand acme --action save-performance --data '{"campaign_id": "...", ...}'
    python rastreador-campanhas.py --brand acme --action save-violation --data '{"rule": "...", "category": "restrictions", ...}'
    python rastreador-campanhas.py --brand acme --action get-violations --category restrictions --severity high
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

CLIENTES_DIR = Path(__file__).parent.parent / "data" / "clientes"


def get_brand_dir(slug):
    """Obtém e valida diretório da marca."""
    brand_dir = CLIENTES_DIR / slug
    if not brand_dir.exists():
        return None, f"Cliente '{slug}' não encontrado. Execute /mktos:configurar primeiro."
    return brand_dir, None


def save_campaign(slug, data):
    """Salva um plano/resultado de campanha no diretório de campanhas da marca."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    campaigns_dir = brand_dir / "campaigns"
    campaigns_dir.mkdir(exist_ok=True)

    # Gera ID da campanha a partir do nome
    name = data.get("name", "untitled")
    campaign_id = name.lower().replace(" ", "-")[:50]
    timestamp = datetime.now().strftime("%Y%m%d")
    campaign_id = f"{campaign_id}-{timestamp}"

    campaign = {
        "campaign_id": campaign_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **data,
    }

    # Salva arquivo da campanha
    filepath = campaigns_dir / f"{campaign_id}.json"
    filepath.write_text(json.dumps(campaign, indent=2))

    # Atualiza índice de campanhas
    index_path = campaigns_dir / "_index.json"
    index = []
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text())
        except json.JSONDecodeError:
            index = []

    index.append({
        "campaign_id": campaign_id,
        "name": data.get("name", "Untitled"),
        "status": data.get("status", "planned"),
        "channels": data.get("channels", []),
        "created_at": campaign["created_at"],
    })
    index_path.write_text(json.dumps(index, indent=2))

    return {
        "status": "saved",
        "campaign_id": campaign_id,
        "path": str(filepath),
    }


def list_campaigns(slug):
    """Lista todas as campanhas de uma marca."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    campaigns_dir = brand_dir / "campaigns"
    index_path = campaigns_dir / "_index.json"

    if not index_path.exists():
        return {"campaigns": [], "total": 0, "note": "Nenhuma campanha salva ainda."}

    try:
        index = json.loads(index_path.read_text())
        return {"campaigns": index, "total": len(index)}
    except json.JSONDecodeError:
        return {"error": "Índice de campanhas está corrompido."}


def get_campaign(slug, campaign_id):
    """Recupera uma campanha específica por ID."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    filepath = brand_dir / "campaigns" / f"{campaign_id}.json"
    if not filepath.exists():
        return {"error": f"Campanha '{campaign_id}' não encontrada."}

    try:
        return json.loads(filepath.read_text())
    except json.JSONDecodeError:
        return {"error": f"Arquivo de campanha corrompido: {campaign_id}"}


def save_performance(slug, data):
    """Salva um snapshot de desempenho para uma marca."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    perf_dir = brand_dir / "performance"
    perf_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    campaign_id = data.get("campaign_id", "general")

    snapshot = {
        "snapshot_id": f"{campaign_id}-{timestamp}",
        "recorded_at": datetime.now().isoformat(),
        **data,
    }

    filepath = perf_dir / f"{campaign_id}-{timestamp}.json"
    filepath.write_text(json.dumps(snapshot, indent=2))

    return {"status": "saved", "snapshot_id": snapshot["snapshot_id"], "path": str(filepath)}


def save_insight(slug, data):
    """Salva um aprendizado/insight de marketing para a marca."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    insights_path = brand_dir / "insights.json"
    insights = []
    if insights_path.exists():
        try:
            insights = json.loads(insights_path.read_text())
        except json.JSONDecodeError:
            insights = []

    insight = {
        "recorded_at": datetime.now().isoformat(),
        "type": data.get("type", "learning"),
        "source": data.get("source", "session"),
        "insight": data.get("insight", ""),
        "context": data.get("context", ""),
        "actionable": data.get("actionable", True),
    }
    insights.append(insight)

    # Mantém os últimos 200 insights
    insights = insights[-200:]
    insights_path.write_text(json.dumps(insights, indent=2))

    return {"status": "saved", "total_insights": len(insights)}


def get_insights(slug, insight_type=None, limit=20):
    """Recupera insights de marketing para uma marca."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    insights_path = brand_dir / "insights.json"
    if not insights_path.exists():
        return {"insights": [], "total": 0, "note": "Nenhum insight salvo ainda."}

    try:
        insights = json.loads(insights_path.read_text())
    except json.JSONDecodeError:
        return {"error": "Arquivo de insights corrompido."}

    if insight_type:
        insights = [i for i in insights if i.get("type") == insight_type]

    # Retorna mais recentes primeiro
    insights = list(reversed(insights[-limit:]))
    return {"insights": insights, "total": len(insights)}


def save_violation(slug, data):
    """Salva uma violação de guideline para rastreamento e análise de padrões."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    violations_path = brand_dir / "guideline-violations.json"
    violations = []
    if violations_path.exists():
        try:
            violations = json.loads(violations_path.read_text())
        except json.JSONDecodeError:
            violations = []

    violation = {
        "recorded_at": datetime.now().isoformat(),
        "rule": data.get("rule", ""),
        "category": data.get("category", ""),
        "severity": data.get("severity", "medium"),
        "content": data.get("content", ""),
        "suggestion": data.get("suggestion", ""),
        "source": data.get("source", "session"),
        "module": data.get("module", ""),
    }
    violations.append(violation)

    # Mantém as últimas 500 violações
    violations = violations[-500:]
    violations_path.write_text(json.dumps(violations, indent=2))

    return {"status": "saved", "total_violations": len(violations)}


def get_violations(slug, category=None, severity=None, limit=50):
    """Recupera violações de guideline para uma marca."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    violations_path = brand_dir / "guideline-violations.json"
    if not violations_path.exists():
        return {"violations": [], "total": 0, "note": "Nenhuma violação registrada."}

    try:
        violations = json.loads(violations_path.read_text())
    except json.JSONDecodeError:
        return {"error": "Arquivo de violações corrompido."}

    if category:
        violations = [v for v in violations if v.get("category") == category]
    if severity:
        violations = [v for v in violations if v.get("severity") == severity]

    # Retorna mais recentes primeiro
    violations = list(reversed(violations[-limit:]))

    # Estatísticas resumidas
    severity_counts = {}
    category_counts = {}
    for v in violations:
        sev = v.get("severity", "medium")
        cat = v.get("category", "unknown")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return {
        "violations": violations,
        "total": len(violations),
        "by_severity": severity_counts,
        "by_category": category_counts,
    }


def main():
    parser = argparse.ArgumentParser(description="Persistência de dados de campanha para mktOS Mídia")
    parser.add_argument("--brand", required=True, help="Slug da marca")
    parser.add_argument("--action", required=True,
                        choices=["save-campaign", "list-campaigns", "get-campaign",
                                 "save-performance", "save-insight", "get-insights",
                                 "save-violation", "get-violations"],
                        help="Ação a executar")
    parser.add_argument("--data", help="Dados JSON (para ações de save)")
    parser.add_argument("--id", help="ID da campanha (para get-campaign)")
    parser.add_argument("--type", dest="insight_type", help="Filtrar insights por tipo")
    parser.add_argument("--category", help="Filtrar violações por categoria de guideline")
    parser.add_argument("--severity", help="Filtrar violações por severidade (low/medium/high)")
    parser.add_argument("--limit", type=int, default=20, help="Máximo de itens a retornar")
    args = parser.parse_args()

    if args.action == "save-campaign":
        if not args.data:
            print(json.dumps({"error": "Forneça --data com JSON de campanha"}))
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(json.dumps({"error": "JSON inválido em --data"}))
            sys.exit(1)
        result = save_campaign(args.brand, data)

    elif args.action == "list-campaigns":
        result = list_campaigns(args.brand)

    elif args.action == "get-campaign":
        if not args.id:
            print(json.dumps({"error": "Forneça --id para get-campaign"}))
            sys.exit(1)
        result = get_campaign(args.brand, args.id)

    elif args.action == "save-performance":
        if not args.data:
            print(json.dumps({"error": "Forneça --data com JSON de desempenho"}))
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(json.dumps({"error": "JSON inválido em --data"}))
            sys.exit(1)
        result = save_performance(args.brand, data)

    elif args.action == "save-insight":
        if not args.data:
            print(json.dumps({"error": "Forneça --data com JSON de insight"}))
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(json.dumps({"error": "JSON inválido em --data"}))
            sys.exit(1)
        result = save_insight(args.brand, data)

    elif args.action == "get-insights":
        result = get_insights(args.brand, args.insight_type, args.limit)

    elif args.action == "save-violation":
        if not args.data:
            print(json.dumps({"error": "Forneça --data com JSON de violação"}))
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(json.dumps({"error": "JSON inválido em --data"}))
            sys.exit(1)
        result = save_violation(args.brand, data)

    elif args.action == "get-violations":
        result = get_violations(args.brand, args.category, args.severity, args.limit)

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
