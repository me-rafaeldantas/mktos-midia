#!/usr/bin/env python3
"""
log-tarefas.py
===========
Fonte da Verdade (SoT) de tarefas para o mktOS.

Registra tarefas planejadas e executadas por conta, com status e histórico de comentários.
Armazena em ./data/work-log/tasks.jsonl (append-only, uma linha por tarefa).

Uso:
    python log-tarefas.py --action log --data '{"account_slug":"cliente-exemplo","title":"[Ads] Criar campanha Search","category":"Ads","source_skill":"lançar"}'
    python log-tarefas.py --action update --id abc12345 --status in_progress --comment "Iniciando configuração"
    python log-tarefas.py --action done --id abc12345 --comment "Campanha criada com ID 12345"
    python log-tarefas.py --action status
    python log-tarefas.py --action report --account cliente-exemplo --days 30
    python log-tarefas.py --action list --status queued
"""

import sys
import os
from pathlib import Path

# Auto-bootstrap inside venv
venv_python = Path(__file__).parent.parent / ".venv" / "bin" / "python3"
if venv_python.exists() and sys.executable != str(venv_python) and not os.environ.get("MKTOS_VENV_ACTIVE"):
    os.environ["MKTOS_VENV_ACTIVE"] = "1"
    os.execv(str(venv_python), [str(venv_python)] + sys.argv)

import argparse
import json
import uuid
from datetime import datetime, timedelta, timezone

WORK_LOG_DIR = Path(__file__).parent.parent / "data" / "work-log"
TASKS_FILE = WORK_LOG_DIR / "tasks.jsonl"

VALID_STATUSES = {"queued", "in_progress", "done", "blocked", "cancelled"}


def ensure_dir():
    WORK_LOG_DIR.mkdir(parents=True, exist_ok=True)


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def short_id():
    return str(uuid.uuid4()).replace("-", "")[:8]


def read_tasks() -> list:
    if not TASKS_FILE.exists():
        return []
    tasks = []
    with open(TASKS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    tasks.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return tasks


def write_tasks(tasks: list):
    ensure_dir()
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")


def append_task(task: dict):
    ensure_dir()
    with open(TASKS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(task, ensure_ascii=False) + "\n")


def log_task(data: dict) -> dict:
    ts = now_iso()
    task = {
        "id": short_id(),
        "account_slug": data.get("account_slug", ""),
        "title": data.get("title", "").strip(),
        "category": data.get("category", ""),
        "status": "queued",
        "priority": data.get("priority", "normal"),
        "source_skill": data.get("source_skill", ""),
        "created_at": ts,
        "updated_at": ts,
        "comments": [],
    }
    if data.get("comment"):
        task["comments"].append({"timestamp": ts, "text": data["comment"]})
    append_task(task)
    return task


def update_task(task_id: str, status: str = None, comment: str = None):
    tasks = read_tasks()
    updated = None
    for task in tasks:
        if task["id"] == task_id:
            ts = now_iso()
            if status:
                if status not in VALID_STATUSES:
                    print(f"Status inválido: {status}. Use: {', '.join(VALID_STATUSES)}", file=sys.stderr)
                    sys.exit(1)
                task["status"] = status
            task["updated_at"] = ts
            if comment:
                task["comments"].append({"timestamp": ts, "text": comment})
            updated = task
    if updated:
        write_tasks(tasks)
    else:
        print(f"Tarefa não encontrada: {task_id}", file=sys.stderr)
        sys.exit(1)
    return updated


def filter_tasks(tasks: list, account_slug: str = None, days: int = None, status: str = None) -> list:
    filtered = tasks
    if account_slug:
        filtered = [t for t in filtered if t.get("account_slug") == account_slug]
    if status:
        filtered = [t for t in filtered if t.get("status") == status]
    if days:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        filtered = [t for t in filtered if t.get("created_at", "") >= cutoff]
    return filtered


def report(account_slug: str = None, days: int = 30) -> dict:
    tasks = read_tasks()
    filtered = filter_tasks(tasks, account_slug=account_slug, days=days)

    by_status = {}
    by_account = {}
    by_category = {}

    for task in filtered:
        s = task.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1

        a = task.get("account_slug", "unknown")
        if a not in by_account:
            by_account[a] = {"total": 0, "done": 0}
        by_account[a]["total"] += 1
        if s == "done":
            by_account[a]["done"] += 1

        c = task.get("category", "geral")
        by_category[c] = by_category.get(c, 0) + 1

    return {
        "period_days": days,
        "account_filter": account_slug,
        "total": len(filtered),
        "by_status": by_status,
        "by_account": by_account,
        "by_category": by_category,
        "tasks": filtered,
    }


def status_summary() -> dict:
    tasks = read_tasks()
    in_progress = [t for t in tasks if t.get("status") == "in_progress"]
    queued = [t for t in tasks if t.get("status") == "queued"]
    blocked = [t for t in tasks if t.get("status") == "blocked"]

    return {
        "in_progress": in_progress,
        "queued": queued[:10],
        "queued_total": len(queued),
        "blocked": blocked,
    }


def list_tasks(status: str = None, account_slug: str = None, days: int = None) -> list:
    tasks = read_tasks()
    return filter_tasks(tasks, account_slug=account_slug, days=days, status=status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerenciador de Work Log do mktOS")
    parser.add_argument("--action", required=True,
                        choices=["log", "update", "done", "status", "report", "list"])
    parser.add_argument("--data", help="JSON com dados da tarefa (para --action log)")
    parser.add_argument("--id", help="ID da tarefa (para update/done)")
    parser.add_argument("--status", help="Novo status da tarefa")
    parser.add_argument("--comment", help="Comentário a adicionar")
    parser.add_argument("--account", help="Slug da conta para filtro")
    parser.add_argument("--days", type=int, default=30, help="Janela de dias para relatório")
    args = parser.parse_args()

    if args.action == "log":
        if not args.data:
            print("--data é obrigatório para --action log", file=sys.stderr)
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"JSON inválido em --data: {e}", file=sys.stderr)
            sys.exit(1)
        if args.comment:
            data["comment"] = args.comment
        result = log_task(data)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.action == "update":
        if not args.id:
            print("--id é obrigatório para --action update", file=sys.stderr)
            sys.exit(1)
        result = update_task(args.id, status=args.status, comment=args.comment)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.action == "done":
        if not args.id:
            print("--id é obrigatório para --action done", file=sys.stderr)
            sys.exit(1)
        result = update_task(args.id, status="done", comment=args.comment)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.action == "status":
        result = status_summary()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.action == "report":
        result = report(account_slug=args.account, days=args.days)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.action == "list":
        result = list_tasks(status=args.status, account_slug=args.account, days=args.days)
        print(json.dumps(result, ensure_ascii=False, indent=2))
