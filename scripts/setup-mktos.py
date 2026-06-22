#!/usr/bin/env python3
"""
setup-mktos.py — Inicializa e gerencia o workspace raiz do mktOS Mídia.

Uso:
  python3 setup-mktos.py --action init [--nome "..."] [--email "..."] [--tipo agencia|empresa|freela|eugencia] [--moeda BRL|USD|EUR]
  python3 setup-mktos.py --action status
  python3 setup-mktos.py --action check-deps
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
from datetime import datetime, timezone

MEMORIA_DIR = Path(__file__).parent.parent / "data"
WORKSPACE_FILE = MEMORIA_DIR / "workspace.json"
CLIENTES_DIR = MEMORIA_DIR / "clientes"
CONTA_ATIVA_FILE = CLIENTES_DIR / "_conta-ativa.json"

TIPOS_VALIDOS = ["agencia", "empresa", "freela", "eugencia"]
MOEDAS_VALIDAS = ["BRL", "USD", "EUR"]

DESCRICAO_TIPOS = {
    "agencia": "Agência com equipe — SOPs completos, controles de aprovação, dashboards por cliente",
    "empresa": "Empresa usando o plugin para o próprio marketing — fluxo simplificado",
    "freela": "Freelancer gerenciando múltiplos clientes — troca de conta frequente",
    "eugencia": "Solo-agency (estrategista + executor) — micro-agência sem equipe formal",
}


def carregar_workspace():
    if not WORKSPACE_FILE.exists():
        return None
    with open(WORKSPACE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_workspace(dados: dict):
    MEMORIA_DIR.mkdir(parents=True, exist_ok=True)
    with open(WORKSPACE_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def action_init(args):
    # Tenta migrar se o diretório antigo existir e o novo estiver vazio/não configurado
    diretorio_antigo = Path.home() / ".claude-marketing"
    if diretorio_antigo.exists() and not WORKSPACE_FILE.exists():
        import shutil
        try:
            MEMORIA_DIR.mkdir(parents=True, exist_ok=True)
            for item in diretorio_antigo.iterdir():
                if item.name == "workspace.json":
                    shutil.copy(item, WORKSPACE_FILE)
                elif item.is_dir() and item.name in ("clientes", "sops", "work-log"):
                    target_dir = MEMORIA_DIR / item.name
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    shutil.copytree(item, target_dir)
        except Exception:
            pass

    if WORKSPACE_FILE.exists():
        ws = carregar_workspace()
        print(json.dumps({
            "status": "ja_existe",
            "mensagem": f"Workspace '{ws.get('nome', '?')}' já está configurado. Use /mktos:configurar para reconfigurar.",
            "workspace": ws,
        }, ensure_ascii=False, indent=2))
        return

    nome = args.nome or "Meu Workspace"
    email = args.email or ""
    tipo = args.tipo or "empresa"
    moeda = args.moeda or "BRL"

    if tipo not in TIPOS_VALIDOS:
        print(json.dumps({"status": "erro", "mensagem": f"Tipo inválido: '{tipo}'. Use: {', '.join(TIPOS_VALIDOS)}"}, ensure_ascii=False))
        sys.exit(1)

    if moeda not in MOEDAS_VALIDAS:
        print(json.dumps({"status": "erro", "mensagem": f"Moeda inválida: '{moeda}'. Use: {', '.join(MOEDAS_VALIDAS)}"}, ensure_ascii=False))
        sys.exit(1)

    agora = datetime.now(timezone.utc).isoformat()

    workspace = {
        "nome": nome,
        "tipo": tipo,
        "email_admin": email,
        "moeda_padrao": moeda,
        "aprovacao_obrigatoria": True,
        "limite_orcamento_diario_global": None,
        "clientes": [],
        "integracoes_ativas": [],
        "criado_em": agora,
        "atualizado_em": agora,
    }

    CLIENTES_DIR.mkdir(parents=True, exist_ok=True)

    if not CONTA_ATIVA_FILE.exists():
        with open(CONTA_ATIVA_FILE, "w", encoding="utf-8") as f:
            json.dump({"slug": None, "nome": None, "atualizado_em": None}, f, ensure_ascii=False, indent=2)

    (MEMORIA_DIR / "sops").mkdir(exist_ok=True)

    salvar_workspace(workspace)

    print(json.dumps({
        "status": "criado",
        "mensagem": f"Workspace '{nome}' criado com sucesso.",
        "workspace": workspace,
    }, ensure_ascii=False, indent=2))


def action_status(args):
    ws = carregar_workspace()

    if not ws:
        print(json.dumps({
            "status": "nao_configurado",
            "mensagem": "Workspace não configurado. Execute /mktos:configurar para iniciar.",
        }, ensure_ascii=False, indent=2))
        return

    conta_ativa = None
    if CONTA_ATIVA_FILE.exists():
        with open(CONTA_ATIVA_FILE, "r", encoding="utf-8") as f:
            conta_ativa = json.load(f)

    clientes_dir = CLIENTES_DIR
    clientes_cadastrados = [
        d.name for d in clientes_dir.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    ] if clientes_dir.exists() else []

    print(json.dumps({
        "status": "ok",
        "workspace": {
            "nome": ws.get("nome"),
            "tipo": ws.get("tipo"),
            "descricao_tipo": DESCRICAO_TIPOS.get(ws.get("tipo", ""), ""),
            "email_admin": ws.get("email_admin"),
            "moeda_padrao": ws.get("moeda_padrao"),
            "aprovacao_obrigatoria": ws.get("aprovacao_obrigatoria"),
            "limite_orcamento_diario_global": ws.get("limite_orcamento_diario_global"),
            "integracoes_ativas": ws.get("integracoes_ativas", []),
            "criado_em": ws.get("criado_em"),
        },
        "clientes_cadastrados": clientes_cadastrados,
        "total_clientes": len(clientes_cadastrados),
        "conta_ativa": conta_ativa,
    }, ensure_ascii=False, indent=2))


def action_check_deps(args):
    resultados = []
    erros = []

    # Python 3.8+
    versao_python = sys.version_info
    ok_python = versao_python >= (3, 8)
    resultados.append({
        "dependencia": f"Python {versao_python.major}.{versao_python.minor}.{versao_python.micro}",
        "status": "ok" if ok_python else "erro",
        "mensagem": "OK" if ok_python else "Python 3.8+ necessário",
    })
    if not ok_python:
        erros.append("Python 3.8+")

    # Bibliotecas opcionais
    libs_opcionais = [
        ("nltk", "Análise de copy e conteúdo"),
        ("textstat", "Análise de legibilidade"),
        ("requests", "Validação de landing pages"),
        ("openpyxl", "Exportação de negativos para Excel"),
    ]

    for lib, descricao in libs_opcionais:
        try:
            __import__(lib)
            resultados.append({"dependencia": lib, "status": "ok", "descricao": descricao})
        except ImportError:
            resultados.append({
                "dependencia": lib,
                "status": "ausente",
                "descricao": descricao,
                "instrucao": f"pip install {lib}",
            })

    # Diretório de memória
    memoria_ok = MEMORIA_DIR.exists()
    resultados.append({
        "dependencia": "data/",
        "status": "ok" if memoria_ok else "aviso",
        "mensagem": "Diretório de dados (data/) presente" if memoria_ok else "Execute /mktos:configurar para criar",
    })

    # Workspace configurado
    ws_ok = WORKSPACE_FILE.exists()
    resultados.append({
        "dependencia": "workspace.json",
        "status": "ok" if ws_ok else "aviso",
        "mensagem": "Workspace configurado" if ws_ok else "Execute /mktos:configurar para criar",
    })

    status_geral = "ok" if not erros else "erro"
    print(json.dumps({
        "status": status_geral,
        "dependencias": resultados,
        "erros_criticos": erros,
        "resumo": f"{sum(1 for r in resultados if r['status'] == 'ok')}/{len(resultados)} verificações OK",
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Inicializa e gerencia o workspace raiz do mktOS Mídia"
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["init", "status", "check-deps"],
        help="Ação a executar",
    )
    parser.add_argument("--nome", help="Nome do workspace")
    parser.add_argument("--email", help="Email do administrador")
    parser.add_argument("--tipo", choices=TIPOS_VALIDOS, help="Tipo de workspace")
    parser.add_argument("--moeda", choices=MOEDAS_VALIDAS, default="BRL", help="Moeda padrão")

    args = parser.parse_args()

    acoes = {
        "init": action_init,
        "status": action_status,
        "check-deps": action_check_deps,
    }
    acoes[args.action](args)


if __name__ == "__main__":
    main()
