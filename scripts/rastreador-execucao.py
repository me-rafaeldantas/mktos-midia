#!/usr/bin/env python3
"""
rastreador-execucao.py
====================
Trilha de auditoria para todas as ações executadas em plataformas no mktOS Mídia.

Registra cada publicação, envio, lançamento e sincronização para que o plugin mantenha um
registro completo do que foi feito, quando e em qual plataforma.

Armazenamento: ./data/clientes/{slug}/executions/

Uso:
    python rastreador-execucao.py --brand acme --action log-execution --data '{"platform": "wordpress", "action_type": "publish-blog", "content_id": "q1-recap", "result": "success", "url": "https://example.com/q1", "details": "Published via REST API"}'
    python rastreador-execucao.py --brand acme --action get-history
    python rastreador-execucao.py --brand acme --action get-history --platform wordpress --status success --limit 10
    python rastreador-execucao.py --brand acme --action get-stats
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


def _load_index(executions_dir):
    """Carrega o arquivo de índice de execução."""
    index_path = executions_dir / "_index.json"
    if not index_path.exists():
        return []
    try:
        return json.loads(index_path.read_text())
    except json.JSONDecodeError:
        return []


def _save_index(executions_dir, index):
    """Salva o arquivo de índice de execução."""
    index_path = executions_dir / "_index.json"
    index_path.write_text(json.dumps(index, indent=2))


def log_execution(slug, data):
    """Registra uma ação executada na trilha de auditoria."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    # Valida campos obrigatórios
    platform = data.get("platform")
    if not platform:
        return {"error": "Campo obrigatório ausente: platform"}

    action_type = data.get("action_type")
    if not action_type:
        return {"error": "Campo obrigatório ausente: action_type"}

    result = data.get("result")
    if result not in ("success", "failure"):
        return {"error": "result deve ser 'success' ou 'failure'."}

    executions_dir = brand_dir / "executions"
    executions_dir.mkdir(exist_ok=True)

    # Gera execution_id: exec-{platform}-{YYYYMMDD-HHMMSS}
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    execution_id = f"exec-{platform}-{timestamp}"

    execution = {
        "execution_id": execution_id,
        "platform": platform,
        "action_type": action_type,
        "content_id": data.get("content_id"),
        "result": result,
        "url": data.get("url"),
        "details": data.get("details"),
        "approval_id": data.get("approval_id"),
        "executed_at": datetime.now().isoformat(),
    }

    # Salva arquivo individual de execução
    filepath = executions_dir / f"{execution_id}.json"
    filepath.write_text(json.dumps(execution, indent=2))

    # Atualiza índice
    index = _load_index(executions_dir)
    index.append({
        "execution_id": execution_id,
        "platform": platform,
        "action_type": action_type,
        "result": result,
        "executed_at": execution["executed_at"],
    })
    _save_index(executions_dir, index)

    return {
        "status": "logged",
        "execution_id": execution_id,
        "path": str(filepath),
    }


def get_history(slug, platform=None, status=None, limit=50):
    """Lista todas as execuções com filtros opcionais, mais recentes primeiro."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    executions_dir = brand_dir / "executions"
    if not executions_dir.exists():
        return {"executions": [], "total": 0, "note": "Nenhuma execução registrada ainda."}

    # Carrega todos os arquivos de execução (não só índice) para detalhes completos
    executions = []
    for fp in sorted(executions_dir.glob("exec-*.json"), reverse=True):
        try:
            execution = json.loads(fp.read_text())
            executions.append(execution)
        except json.JSONDecodeError:
            continue

    # Aplica filtros
    if platform:
        executions = [e for e in executions if e.get("platform") == platform]
    if status:
        executions = [e for e in executions if e.get("result") == status]

    # Ordena mais recentes primeiro
    executions.sort(key=lambda e: e.get("executed_at", ""), reverse=True)

    # Aplica limite
    total = len(executions)
    executions = executions[:limit]

    return {
        "executions": executions,
        "returned": len(executions),
        "total": total,
    }


def get_stats(slug):
    """Estatísticas resumidas para todas as execuções."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    executions_dir = brand_dir / "executions"
    if not executions_dir.exists():
        return {
            "total_executed": 0,
            "by_platform": {},
            "by_status": {},
            "success_rate": 0,
            "last_execution": None,
            "note": "Nenhuma execução registrada ainda.",
        }

    # Carrega índice para estatísticas rápidas
    index = _load_index(executions_dir)
    if not index:
        return {
            "total_executed": 0,
            "by_platform": {},
            "by_status": {},
            "success_rate": 0,
            "last_execution": None,
            "note": "Nenhuma execução registrada ainda.",
        }

    total = len(index)
    by_platform = {}
    by_status = {}
    last_execution = None

    for entry in index:
        plat = entry.get("platform", "unknown")
        by_platform[plat] = by_platform.get(plat, 0) + 1

        result = entry.get("result", "unknown")
        by_status[result] = by_status.get(result, 0) + 1

        executed_at = entry.get("executed_at", "")
        if not last_execution or executed_at > last_execution:
            last_execution = executed_at

    success_count = by_status.get("success", 0)
    success_rate = round(success_count / total * 100, 1) if total else 0

    return {
        "total_executed": total,
        "by_platform": by_platform,
        "by_status": by_status,
        "success_rate": success_rate,
        "last_execution": last_execution,
    }


def main():
    parser = argparse.ArgumentParser(description="Trilha de auditoria de execução para mktOS Mídia")
    parser.add_argument("--brand", required=True, help="Slug da marca")
    parser.add_argument("--action", required=True,
                        choices=["log-execution", "get-history", "get-stats"],
                        help="Ação a realizar")
    parser.add_argument("--data", help="Dados JSON (para log-execution)")
    parser.add_argument("--platform", help="Filtrar histórico por plataforma")
    parser.add_argument("--status", help="Filtrar histórico por resultado (success/failure)")
    parser.add_argument("--limit", type=int, default=50, help="Número máximo de itens a retornar")
    args = parser.parse_args()

    if args.action == "log-execution":
        if not args.data:
            print(json.dumps({"error": "Forneça --data com JSON de execução"}))
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(json.dumps({"error": "JSON inválido em --data"}))
            sys.exit(1)
        result = log_execution(args.brand, data)

    elif args.action == "get-history":
        result = get_history(args.brand, args.platform, args.status, args.limit)

    elif args.action == "get-stats":
        result = get_stats(args.brand)

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
