#!/usr/bin/env python3
"""
monitor-performance.py
======================
Agregue métricas, detecte anomalias e gerencie baselines para mktOS Mídia.

Armazena snapshots de desempenho com timestamp e usa análise estatística para sinalizar
métricas que desviam significativamente das normas históricas.

Armazenamento: ./data/clientes/{slug}/performance/

Uso:
    python monitor-performance.py --brand acme --action pull-metrics --data '{"sessions": 1234, "conversions": 56, "revenue": 7890, "ctr": 3.2}'
    python monitor-performance.py --brand acme --action save-snapshot --data '{"sessions": 1234, "conversions": 56, "revenue": 7890}'
    python monitor-performance.py --brand acme --action detect-anomalies --data '{"sessions": 500, "conversions": 2, "revenue": 100}'
    python monitor-performance.py --brand acme --action get-baseline
"""

import argparse
import json
import os
import statistics
import sys
from datetime import datetime
from pathlib import Path

# Auto-bootstrap inside venv
venv_python = Path(__file__).parent.parent / ".venv" / "bin" / "python3"
if venv_python.exists() and sys.executable != str(venv_python) and not os.environ.get("MKTOS_VENV_ACTIVE"):
    os.environ["MKTOS_VENV_ACTIVE"] = "1"
    os.execv(str(venv_python), [str(venv_python)] + sys.argv)

MEMORIA_DIR = Path(__file__).parent.parent / "data"
CLIENTES_DIR = MEMORIA_DIR / "clientes"

MAX_SNAPSHOTS = 90
BASELINE_WINDOW = 30
ANOMALY_THRESHOLD = 2.0  # standard deviations


def get_brand_dir(slug):
    """Obtém e valida diretório da marca."""
    brand_dir = CLIENTES_DIR / slug
    if not brand_dir.exists():
        return None, f"Cliente '{slug}' não encontrado. Execute /mktos:configurar primeiro."
    return brand_dir, None


def _load_snapshots(perf_dir):
    """Carrega todos os arquivos de snapshot de desempenho, ordenados de mais antigo a mais recente."""
    snapshots = []
    if not perf_dir.exists():
        return snapshots
    for fp in sorted(perf_dir.glob("snapshot-*.json")):
        try:
            snapshot = json.loads(fp.read_text())
            snapshots.append(snapshot)
        except json.JSONDecodeError:
            continue
    return snapshots


def _prune_snapshots(perf_dir):
    """Remove snapshots mais antigos se contagem exceder MAX_SNAPSHOTS."""
    files = sorted(perf_dir.glob("snapshot-*.json"))
    if len(files) > MAX_SNAPSHOTS:
        for fp in files[: len(files) - MAX_SNAPSHOTS]:
            fp.unlink()


def _extract_metric_keys(snapshots):
    """Coleta todas as chaves de métrica única entre snapshots."""
    keys = set()
    for snap in snapshots:
        metrics = snap.get("metrics", {})
        keys.update(metrics.keys())
    return sorted(keys)


def _safe_stdev(values):
    """Calcula desvio padrão, retornando 0 para menos de 2 valores."""
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def pull_metrics(slug, data):
    """Normaliza e armazena um snapshot de métricas, retornando o resultado normalizado."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    if not data or not isinstance(data, dict):
        return {"error": "Forneça um objeto de métricas em --data."}

    perf_dir = brand_dir / "performance"
    perf_dir.mkdir(exist_ok=True)

    # Normalize: ensure all values are numeric
    normalized = {}
    for key, value in data.items():
        if isinstance(value, (int, float)):
            normalized[key] = value
        elif isinstance(value, str):
            try:
                normalized[key] = float(value)
            except ValueError:
                continue
        # Skip non-numeric values silently

    if not normalized:
        return {"error": "Nenhuma métrica numérica válida encontrada em --data."}

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    snapshot = {
        "snapshot_id": f"snapshot-{timestamp}",
        "recorded_at": datetime.now().isoformat(),
        "metrics": normalized,
    }

    filepath = perf_dir / f"snapshot-{timestamp}.json"
    filepath.write_text(json.dumps(snapshot, indent=2))
    _prune_snapshots(perf_dir)

    return {
        "status": "stored",
        "snapshot_id": snapshot["snapshot_id"],
        "metrics": normalized,
        "path": str(filepath),
    }


def save_snapshot(slug, data):
    """Salva um snapshot de desempenho com timestamp (máx 90 mantidos)."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    if not data or not isinstance(data, dict):
        return {"error": "Forneça um objeto de métricas em --data."}

    perf_dir = brand_dir / "performance"
    perf_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    snapshot = {
        "snapshot_id": f"snapshot-{timestamp}",
        "recorded_at": datetime.now().isoformat(),
        "metrics": data,
    }

    filepath = perf_dir / f"snapshot-{timestamp}.json"
    filepath.write_text(json.dumps(snapshot, indent=2))
    _prune_snapshots(perf_dir)

    # Conta remanescentes
    remaining = len(list(perf_dir.glob("snapshot-*.json")))

    return {
        "status": "saved",
        "snapshot_id": snapshot["snapshot_id"],
        "total_snapshots": remaining,
        "path": str(filepath),
    }


def detect_anomalies(slug, data):
    """Detecta métricas que desviam significativamente de baselines recentes."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    if not data or not isinstance(data, dict):
        return {"error": "Forneça métricas atuais em --data."}

    perf_dir = brand_dir / "performance"
    snapshots = _load_snapshots(perf_dir)

    # Usa os últimos BASELINE_WINDOW snapshots
    recent = snapshots[-BASELINE_WINDOW:]

    if len(recent) < 3:
        return {
            "status": "insufficient_data",
            "snapshots_available": len(recent),
            "minimum_required": 3,
            "note": "Precisa de pelo menos 3 snapshots históricos para detectar anomalias.",
        }

    anomalies = []
    metric_keys = set(data.keys())

    for key in sorted(metric_keys):
        current_value = data.get(key)
        if not isinstance(current_value, (int, float)):
            continue

        # Coleta valores históricos para esta métrica
        historical = []
        for snap in recent:
            val = snap.get("metrics", {}).get(key)
            if isinstance(val, (int, float)):
                historical.append(val)

        if len(historical) < 3:
            continue

        mean = statistics.mean(historical)
        stdev = _safe_stdev(historical)

        if stdev == 0:
            # All historical values identical; flag if current differs at all
            if current_value != mean:
                anomalies.append({
                    "metric": key,
                    "current": current_value,
                    "mean": mean,
                    "std_dev": 0,
                    "deviation": "inf",
                    "direction": "above" if current_value > mean else "below",
                })
            continue

        z_score = (current_value - mean) / stdev

        if abs(z_score) > ANOMALY_THRESHOLD:
            anomalies.append({
                "metric": key,
                "current": current_value,
                "mean": round(mean, 2),
                "std_dev": round(stdev, 2),
                "z_score": round(z_score, 2),
                "deviation": f"{abs(round(z_score, 1))} std devs",
                "direction": "above" if z_score > 0 else "below",
            })

    return {
        "anomalies": anomalies,
        "total_anomalies": len(anomalies),
        "snapshots_analyzed": len(recent),
        "threshold": f"{ANOMALY_THRESHOLD} std devs",
    }


def get_baseline(slug):
    """Calcula estatísticas de baseline de snapshots de desempenho armazenados."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    perf_dir = brand_dir / "performance"
    snapshots = _load_snapshots(perf_dir)

    # Usa os últimos BASELINE_WINDOW snapshots
    recent = snapshots[-BASELINE_WINDOW:]

    if len(recent) < 3:
        return {
            "status": "insufficient_data",
            "snapshots_available": len(recent),
            "minimum_required": 3,
            "note": "Precisa de pelo menos 3 snapshots para calcular um baseline significativo.",
        }

    metric_keys = _extract_metric_keys(recent)
    baselines = {}

    for key in metric_keys:
        values = []
        for snap in recent:
            val = snap.get("metrics", {}).get(key)
            if isinstance(val, (int, float)):
                values.append(val)

        if len(values) < 2:
            baselines[key] = {"status": "insufficient_data", "data_points": len(values)}
            continue

        baselines[key] = {
            "mean": round(statistics.mean(values), 2),
            "std_dev": round(_safe_stdev(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "data_points": len(values),
        }

    return {
        "baselines": baselines,
        "snapshots_used": len(recent),
        "window": f"últimos {BASELINE_WINDOW} snapshots",
    }


def main():
    parser = argparse.ArgumentParser(description="Monitoramento de desempenho para mktOS Mídia")
    parser.add_argument("--brand", required=True, help="Slug da marca")
    parser.add_argument("--action", required=True,
                        choices=["pull-metrics", "save-snapshot", "detect-anomalies",
                                 "get-baseline"],
                        help="Ação a executar")
    parser.add_argument("--data", help="Dados JSON (objeto de métricas)")
    args = parser.parse_args()

    if args.action == "pull-metrics":
        if not args.data:
            print(json.dumps({"error": "Forneça --data com JSON de métricas"}))
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(json.dumps({"error": "JSON inválido em --data"}))
            sys.exit(1)
        result = pull_metrics(args.brand, data)

    elif args.action == "save-snapshot":
        if not args.data:
            print(json.dumps({"error": "Forneça --data com JSON de métricas"}))
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(json.dumps({"error": "JSON inválido em --data"}))
            sys.exit(1)
        result = save_snapshot(args.brand, data)

    elif args.action == "detect-anomalies":
        if not args.data:
            print(json.dumps({"error": "Forneça --data com JSON de métricas atuais"}))
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(json.dumps({"error": "JSON inválido em --data"}))
            sys.exit(1)
        result = detect_anomalies(args.brand, data)

    elif args.action == "get-baseline":
        result = get_baseline(args.brand)

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
