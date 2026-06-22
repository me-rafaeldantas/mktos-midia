#!/usr/bin/env python3
"""
gerenciar-contas.py — CRUD de sub-contas (clientes) no workspace do mktOS Mídia.

Uso:
  python3 gerenciar-contas.py --action adicionar --slug {slug} --nome "{nome}" [--google-ads-id {id}] [--meta-account {id}]
  python3 gerenciar-contas.py --action trocar --slug {slug}
  python3 gerenciar-contas.py --action listar
  python3 gerenciar-contas.py --action status
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
import re
from datetime import datetime, timezone

MEMORIA_DIR = Path(__file__).parent.parent / "data"
WORKSPACE_FILE = MEMORIA_DIR / "workspace.json"
CLIENTES_DIR = MEMORIA_DIR / "clientes"
CONTA_ATIVA_FILE = CLIENTES_DIR / "_conta-ativa.json"

SLUG_REGEX = re.compile(r'^[a-z0-9][a-z0-9\-]{0,48}[a-z0-9]$|^[a-z0-9]$')


def agora_iso():
    return datetime.now(timezone.utc).isoformat()


def validar_slug(slug: str) -> bool:
    return bool(SLUG_REGEX.match(slug))


def carregar_workspace():
    if not WORKSPACE_FILE.exists():
        return None
    with open(WORKSPACE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_workspace(dados: dict):
    with open(WORKSPACE_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def carregar_perfil(slug: str):
    perfil_file = CLIENTES_DIR / slug / "perfil.json"
    if not perfil_file.exists():
        return None
    with open(perfil_file, "r", encoding="utf-8") as f:
        return json.load(f)


def conta_ativa_slug():
    if not CONTA_ATIVA_FILE.exists():
        return None
    with open(CONTA_ATIVA_FILE, "r", encoding="utf-8") as f:
        dados = json.load(f)
    return dados.get("slug")


def listar_slugs():
    if not CLIENTES_DIR.exists():
        return []
    return sorted([
        d.name for d in CLIENTES_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    ])


def contar_campanhas(slug: str) -> int:
    campanhas_dir = CLIENTES_DIR / slug / "campanhas"
    if not campanhas_dir.exists():
        return 0
    return len([f for f in campanhas_dir.iterdir() if f.is_file() and f.suffix == ".json"])


def action_adicionar(args):
    if not args.slug:
        print(json.dumps({"status": "erro", "mensagem": "Parâmetro --slug é obrigatório."}, ensure_ascii=False))
        sys.exit(1)
    if not args.nome:
        print(json.dumps({"status": "erro", "mensagem": "Parâmetro --nome é obrigatório."}, ensure_ascii=False))
        sys.exit(1)

    slug = args.slug.lower()

    if not validar_slug(slug):
        print(json.dumps({
            "status": "erro",
            "mensagem": f"Slug inválido: '{slug}'. Use apenas letras minúsculas, números e hífens. Deve ter entre 1 e 50 caracteres.",
        }, ensure_ascii=False))
        sys.exit(1)

    cliente_dir = CLIENTES_DIR / slug

    if cliente_dir.exists():
        print(json.dumps({
            "status": "ja_existe",
            "mensagem": f"Cliente com slug '{slug}' já está cadastrado. Use /mktos:conta status para ver os dados.",
        }, ensure_ascii=False))
        return

    # Criar estrutura de diretórios
    for subdir in ["campanhas", "criativos", "performance"]:
        (cliente_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Criar perfil.json
    perfil = {
        "nome": args.nome,
        "slug": slug,
        "google_ads_id": getattr(args, 'google_ads_id', None) or None,
        "meta_ad_account": getattr(args, 'meta_account', None) or None,
        "moeda": getattr(args, 'moeda', None) or "BRL",
        "kpis": {
            "roas_alvo": None,
            "cpa_alvo": None,
            "cpl_alvo": None,
            "ctr_benchmark": None,
        },
        "orcamento_mensal": None,
        "canais_ativos": [],
        "criado_em": agora_iso(),
        "atualizado_em": agora_iso(),
    }

    with open(cliente_dir / "perfil.json", "w", encoding="utf-8") as f:
        json.dump(perfil, f, ensure_ascii=False, indent=2)

    # Atualizar workspace.json
    ws = carregar_workspace()
    if ws and slug not in ws.get("clientes", []):
        ws.setdefault("clientes", []).append(slug)
        ws["atualizado_em"] = agora_iso()
        salvar_workspace(ws)

    print(json.dumps({
        "status": "criado",
        "mensagem": f"Cliente '{args.nome}' (slug: {slug}) adicionado com sucesso.",
        "perfil": perfil,
        "diretorios_criados": [
            str(cliente_dir / "campanhas"),
            str(cliente_dir / "criativos"),
            str(cliente_dir / "performance"),
        ],
    }, ensure_ascii=False, indent=2))


def action_trocar(args):
    if not args.slug:
        print(json.dumps({"status": "erro", "mensagem": "Parâmetro --slug é obrigatório."}, ensure_ascii=False))
        sys.exit(1)

    slug = args.slug.lower()
    cliente_dir = CLIENTES_DIR / slug

    if not cliente_dir.exists():
        slugs_disponiveis = listar_slugs()
        print(json.dumps({
            "status": "erro",
            "mensagem": f"Cliente '{slug}' não encontrado.",
            "clientes_disponiveis": slugs_disponiveis,
        }, ensure_ascii=False))
        sys.exit(1)

    perfil = carregar_perfil(slug)
    nome = perfil.get("nome", slug) if perfil else slug

    conta_ativa = {
        "slug": slug,
        "nome": nome,
        "atualizado_em": agora_iso(),
    }

    CLIENTES_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONTA_ATIVA_FILE, "w", encoding="utf-8") as f:
        json.dump(conta_ativa, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "status": "ok",
        "mensagem": f"Contexto ativo alterado para: {nome} ({slug})",
        "conta_ativa": conta_ativa,
        "perfil": perfil,
    }, ensure_ascii=False, indent=2))


def action_listar(args):
    slugs = listar_slugs()

    if not slugs:
        print(json.dumps({
            "status": "ok",
            "mensagem": "Nenhum cliente cadastrado ainda. Use /mktos:conta adicionar para criar o primeiro.",
            "clientes": [],
            "total": 0,
        }, ensure_ascii=False, indent=2))
        return

    ativo = conta_ativa_slug()
    clientes = []

    for slug in slugs:
        perfil = carregar_perfil(slug)
        campanhas = contar_campanhas(slug)

        clientes.append({
            "slug": slug,
            "nome": perfil.get("nome", slug) if perfil else slug,
            "google_ads_id": perfil.get("google_ads_id") if perfil else None,
            "meta_ad_account": perfil.get("meta_ad_account") if perfil else None,
            "canais_ativos": perfil.get("canais_ativos", []) if perfil else [],
            "campanhas_registradas": campanhas,
            "ativo": slug == ativo,
        })

    print(json.dumps({
        "status": "ok",
        "clientes": clientes,
        "total": len(clientes),
        "conta_ativa": ativo,
    }, ensure_ascii=False, indent=2))


def action_status(args):
    if not CONTA_ATIVA_FILE.exists():
        print(json.dumps({
            "status": "sem_conta_ativa",
            "mensagem": "Nenhuma conta ativa. Use /mktos:conta trocar {slug} para selecionar um cliente.",
        }, ensure_ascii=False))
        return

    with open(CONTA_ATIVA_FILE, "r", encoding="utf-8") as f:
        conta_ativa = json.load(f)

    slug = conta_ativa.get("slug")

    if not slug:
        print(json.dumps({
            "status": "sem_conta_ativa",
            "mensagem": "Nenhuma conta ativa. Use /mktos:conta trocar {slug} para selecionar um cliente.",
        }, ensure_ascii=False))
        return

    perfil = carregar_perfil(slug)
    campanhas = contar_campanhas(slug)

    # Verificar se workspace está configurado
    ws = carregar_workspace()

    # Carregar .mcp.json para listar integrações disponíveis
    mcp_file = Path(__file__).parent.parent / ".mcp.json"
    integracoes_disponiveis = []
    if mcp_file.exists():
        with open(mcp_file, "r", encoding="utf-8") as f:
            mcp_data = json.load(f)
        integracoes_disponiveis = list(mcp_data.get("mcpServers", {}).keys())

    print(json.dumps({
        "status": "ok",
        "conta_ativa": {
            "slug": slug,
            "nome": perfil.get("nome", slug) if perfil else slug,
            "trocado_em": conta_ativa.get("atualizado_em"),
        },
        "perfil": perfil,
        "campanhas_registradas": campanhas,
        "workspace": {
            "nome": ws.get("nome") if ws else None,
            "tipo": ws.get("tipo") if ws else None,
        },
        "integracoes_disponiveis": integracoes_disponiveis,
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Gerencia sub-contas (clientes) no workspace do mktOS Mídia"
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["adicionar", "trocar", "listar", "status"],
        help="Ação a executar",
    )
    parser.add_argument("--slug", help="Slug único do cliente (ex: clinica-exemplo, loja-beta)")
    parser.add_argument("--nome", help="Nome completo do cliente")
    parser.add_argument("--google-ads-id", dest="google_ads_id", help="ID da conta Google Ads")
    parser.add_argument("--meta-account", dest="meta_account", help="ID da conta Meta Ads (ex: act_123456)")
    parser.add_argument("--moeda", default="BRL", choices=["BRL", "USD", "EUR"], help="Moeda do cliente")

    args = parser.parse_args()

    acoes = {
        "adicionar": action_adicionar,
        "trocar": action_trocar,
        "listar": action_listar,
        "status": action_status,
    }
    acoes[args.action](args)


if __name__ == "__main__":
    main()
