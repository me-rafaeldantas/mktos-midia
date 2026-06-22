#!/usr/bin/env python3
"""
publicador-meta.py
=====================
Publicação em lote de criativos de lead gen no Meta Ads.

Detecta automaticamente pares Feed/Story por convenção de nome de arquivo:
  - Arquivos COM "STORY" no nome  → imagem vertical (Story/Reels)
  - Arquivos SEM "STORY" no nome  → imagem quadrada (Feed)

Cada subpasta de --folder = um criativo. Pares feed+story geram um único
AdCreative. Variantes (A, B, C) são detectadas pelo padrão "-X-" no nome
do arquivo.

Uso:
    python publicador-meta.py \\
        --account act_XXXXXXXXXXXXXXXXXX \\
        --adset   XXXXXXXXXXXXXXXXXXX \\
        --form    XXXXXXXXXXXXXXXXXXX \\
        --page    XXXXXXXXXXXXXXXXXXX \\
        --instagram XXXXXXXXXXXXXXXXXXX \\
        --folder  /tmp/meu-cliente/Unidade-SP \\
        --unit    "Unidade SP" \\
        --product "Produto A" \\
        --caption "Texto do anúncio..."

Pré-requisitos:
    - META_ACCESS_TOKEN no ambiente (via MCP meta-marketing configurado no .mcp.json)
      Permissões necessárias: ads_management, ads_read, pages_manage_ads, business_management
    - App Meta em modo Live (não desenvolvimento)

Limitação conhecida da API (v21.0):
    Placement-specific images (imagem diferente para Story vs Feed) em
    creatives de lead gen não são suportadas via Graph API pública.
    A imagem de Story deve ser adicionada manualmente no Ads Manager
    após a publicação via Editar → Personalização de posicionamento.

Log de execução salvo em:
    ./data/reports/publishes/
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

API_VERSION = "v21.0"
BASE_URL    = f"https://graph.facebook.com/{API_VERSION}"
ENV_FILE    = Path(__file__).parent.parent.parent / ".env"
REPORTS_DIR = Path(__file__).parent.parent.parent / "reports" / "publishes"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
STORY_MARKER     = "STORY"


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

def _load_env() -> None:
    """Carrega variáveis do .env sem depender de python-dotenv."""
    if not ENV_FILE.exists():
        return
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _token() -> str:
    t = os.environ.get("META_ACCESS_TOKEN", "")
    if not t:
        raise EnvironmentError(
            "META_ACCESS_TOKEN não encontrado.\n"
            "Configure o MCP meta-marketing no arquivo .mcp.json com um token que tenha "
            "ads_management + pages_manage_ads e o app em modo Live."
        )
    return t


def _post(path: str, data: dict, token: str) -> dict:
    data["access_token"] = token
    return requests.post(f"{BASE_URL}/{path}", data=data).json()


# ---------------------------------------------------------------------------
# Detecção de pares feed/story
# ---------------------------------------------------------------------------

def _is_story(filename: str) -> bool:
    return STORY_MARKER.upper() in Path(filename).stem.upper()


def _variant(stem: str) -> str:
    """Extrai variante do nome (ex: -C- ou _C_ → 'C')."""
    m = re.search(r"[-_]([A-Z])[-_]", stem.upper())
    return m.group(1) if m else ""


def detect_pairs(folder: Path, only: list[str] | None = None) -> list[dict]:
    """
    Varre subpastas e retorna lista de pares feed/story agrupados por variante.

    Args:
        only: se fornecido, processa apenas as subpastas cujos nomes estão na lista.

    Retorna:
        [{"label": str, "variant": str, "feed": Path|None, "story": Path|None}, ...]
    """
    pairs: dict[str, dict] = {}
    only_set = {n.lower() for n in only} if only else None

    for subdir in sorted(folder.iterdir()):
        if not subdir.is_dir():
            continue
        if only_set and subdir.name.lower() not in only_set:
            continue

        label  = subdir.name
        images = [f for f in sorted(subdir.iterdir()) if f.suffix.lower() in IMAGE_EXTENSIONS]

        by_variant: dict[str, dict] = {}
        for img in images:
            v = _variant(img.stem)
            if v not in by_variant:
                by_variant[v] = {"feed": None, "story": None}
            if _is_story(img.name):
                by_variant[v]["story"] = img
            else:
                by_variant[v]["feed"] = img

        for v, files in by_variant.items():
            key = f"{label}__{v}"
            pairs[key] = {"label": label, "variant": v, **files}

    return list(pairs.values())


# ---------------------------------------------------------------------------
# Upload de imagens
# ---------------------------------------------------------------------------

def upload_image(account_id: str, token: str, path: Path) -> str:
    """Faz upload de uma imagem local e retorna o image_hash."""
    with open(path, "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/{account_id}/adimages",
            params={"access_token": token},
            files={"filename": (path.name, f, "image/jpeg")},
        )
    data = resp.json()
    if "images" not in data:
        raise RuntimeError(f"Upload falhou ({path.name}): {data.get('error', data)}")
    fname = list(data["images"].keys())[0]
    return data["images"][fname]["hash"]


# ---------------------------------------------------------------------------
# Criação de creative e anúncio
# ---------------------------------------------------------------------------

def create_leadgen_creative(
    account_id: str,
    token: str,
    name: str,
    page_id: str,
    instagram_user_id: str,
    feed_hash: str,
    form_id: str,
    caption: str,
) -> str:
    """Cria AdCreative de lead gen com imagem de feed."""
    data = _post(
        f"{account_id}/adcreatives",
        {
            "name": name,
            "object_story_spec": json.dumps({
                "page_id": page_id,
                "instagram_user_id": instagram_user_id,
                "link_data": {
                    "message": caption,
                    "link": "http://fb.me/",
                    "image_hash": feed_hash,
                    "call_to_action": {
                        "type": "LEARN_MORE",
                        "value": {"lead_gen_form_id": form_id},
                    },
                },
            }),
        },
        token,
    )
    if "id" not in data:
        raise RuntimeError(f"Creative falhou: {data.get('error', data)}")
    return data["id"]


def create_ad(
    account_id: str,
    token: str,
    name: str,
    adset_id: str,
    creative_id: str,
    status: str = "PAUSED",
) -> str:
    """Cria anúncio vinculando creative a um conjunto."""
    data = _post(
        f"{account_id}/ads",
        {
            "name": name,
            "adset_id": adset_id,
            "creative": json.dumps({"creative_id": creative_id}),
            "status": status.upper(),
        },
        token,
    )
    if "id" not in data:
        raise RuntimeError(f"Anúncio falhou: {data.get('error', data)}")
    return data["id"]


# ---------------------------------------------------------------------------
# Nomenclatura
# ---------------------------------------------------------------------------

def _ad_name(unit: str, label: str, product: str, variant: str, prefix: str = "") -> str:
    parts = [unit, label, "Feed+Story", product]
    if variant:
        parts.append(variant)
    name = " - ".join(parts)
    return f"{prefix}{name}" if prefix else name


# ---------------------------------------------------------------------------
# Orquestrador principal
# ---------------------------------------------------------------------------

def publish(config: dict) -> dict:
    """
    Executa o fluxo completo: detecta pares → upload → creative → anúncio → log.

    config obrigatório:
        account_id, adset_id, form_id, page_id, instagram_id,
        folder, unit, product, caption

    config opcional:
        ad_status   "PAUSED" (default) | "ACTIVE"
        campaign_id  para registro no log
    """
    _load_env()
    token = _token()

    account_id   = config["account_id"]
    adset_id     = config["adset_id"]
    form_id      = config["form_id"]
    page_id      = config["page_id"]
    instagram_id = config["instagram_id"]
    folder       = Path(config["folder"])
    unit         = config["unit"]
    product      = config["product"]
    caption      = config["caption"]
    ad_status    = config.get("ad_status", "PAUSED")
    prefix       = config.get("prefix", "")

    if not folder.is_dir():
        raise FileNotFoundError(f"Pasta não encontrada: {folder}")

    result = {
        "timestamp":   datetime.now().isoformat(timespec="seconds"),
        "account_id":  account_id,
        "campaign_id": config.get("campaign_id", ""),
        "adset_id":    adset_id,
        "form_id":     form_id,
        "unit":        unit,
        "product":     product,
        "source_folder": str(folder),
        "summary":     {"images_uploaded": 0, "creatives_created": 0, "ads_created": 0, "status": "ok"},
        "images":      [],
        "creatives":   [],
        "ads":         [],
        "errors":      [],
    }

    only = config.get("subfolders") or None  # list[str] | None
    pairs = detect_pairs(folder, only)
    if not pairs:
        raise ValueError(f"Nenhuma imagem encontrada em {folder}")

    print(f"\n=== Publicação: {unit} › {product} ===")
    print(f"{len(pairs)} criativo(s) detectado(s) em {folder}\n")

    for pair in pairs:
        label   = pair["label"]
        variant = pair["variant"]
        name    = _ad_name(unit, label, product, variant, prefix)

        print(f"▸ {name}")

        feed_hash  = None
        story_hash = None

        # Upload feed
        if pair["feed"]:
            try:
                feed_hash = upload_image(account_id, token, pair["feed"])
                result["images"].append({"key": f"{label}_{variant}_feed".strip("_"), "path": str(pair["feed"]), "hash": feed_hash})
                result["summary"]["images_uploaded"] += 1
                print(f"  ✓ Feed  → {feed_hash}")
            except Exception as e:
                result["errors"].append({"step": "upload_feed", "creative": name, "error": str(e)})
                print(f"  ✗ Feed upload falhou: {e}")
                continue

        # Upload story
        if pair["story"]:
            try:
                story_hash = upload_image(account_id, token, pair["story"])
                result["images"].append({"key": f"{label}_{variant}_story".strip("_"), "path": str(pair["story"]), "hash": story_hash})
                result["summary"]["images_uploaded"] += 1
                print(f"  ✓ Story → {story_hash}")
                print(f"  ⚠  Story salva mas precisa ser adicionada manualmente no Ads Manager")
            except Exception as e:
                result["errors"].append({"step": "upload_story", "creative": name, "error": str(e)})
                print(f"  ⚠  Story upload falhou (continuando sem ela): {e}")

        if not feed_hash:
            result["errors"].append({"step": "creative", "creative": name, "error": "Sem imagem feed"})
            continue

        # Criar creative
        try:
            creative_id = create_leadgen_creative(
                account_id, token, name, page_id, instagram_id, feed_hash, form_id, caption
            )
            result["creatives"].append({"name": name, "id": creative_id, "feed_hash": feed_hash, "story_hash": story_hash})
            result["summary"]["creatives_created"] += 1
            print(f"  ✓ Creative → {creative_id}")
        except Exception as e:
            result["errors"].append({"step": "creative", "creative": name, "error": str(e)})
            print(f"  ✗ Creative falhou: {e}")
            continue

        # Criar anúncio
        try:
            ad_id = create_ad(account_id, token, name, adset_id, creative_id, ad_status)
            result["ads"].append({"name": name, "id": ad_id, "creative_id": creative_id, "status": ad_status.upper()})
            result["summary"]["ads_created"] += 1
            print(f"  ✓ Anúncio → {ad_id} [{ad_status.upper()}]")
        except Exception as e:
            result["errors"].append({"step": "ad", "creative": name, "error": str(e)})
            print(f"  ✗ Anúncio falhou: {e}")

    # Status global
    total   = len(pairs)
    created = result["summary"]["ads_created"]
    result["summary"]["status"] = "ok" if created == total else ("partial" if created > 0 else "failed")

    # Salvar log
    _save_report(result, unit, product)
    _print_summary(result)

    return result


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _ascii_slug(text: str) -> str:
    """Remove acentos e normaliza para slug ASCII seguro."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")


def _active_brand_slug() -> str:
    """Lê o slug da marca ativa do sistema mktOS. Retorna '' se não encontrado."""
    active_file = Path(__file__).parent.parent / "data" / "clientes" / "_conta-ativa.json"
    try:
        data = json.loads(active_file.read_text())
        return data.get("slug", "")
    except (FileNotFoundError, json.JSONDecodeError):
        return ""


def _save_report(result: dict, unit: str, product: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date    = datetime.now().strftime("%Y-%m-%d")
    brand   = _active_brand_slug()
    context = _ascii_slug(f"{brand}-{unit}-{product}" if brand else f"{unit}-{product}")
    path    = REPORTS_DIR / f"{date}_{context}.json"

    counter = 1
    while path.exists():
        path = REPORTS_DIR / f"{date}_{context}_{counter}.json"
        counter += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nLog salvo: {path}")
    return path


def _print_summary(result: dict) -> None:
    s = result["summary"]
    print(f"\n{'='*40}")
    print(f"Imagens enviadas:  {s['images_uploaded']}")
    print(f"Creatives criados: {s['creatives_created']}")
    print(f"Anúncios criados:  {s['ads_created']}")
    print(f"Erros:             {len(result['errors'])}")
    print(f"Status:            {s['status'].upper()}")
    print(f"{'='*40}")

    if result["errors"]:
        print("\nErros:")
        for err in result["errors"]:
            print(f"  [{err['step']}] {err['creative']}: {err['error']}")

    pending = [c for c in result["creatives"] if c.get("story_hash")]
    if pending:
        print("\n⚠  Ação manual — adicionar Story no Ads Manager:")
        for c in pending:
            print(f"  • {c['name']}")
            print(f"    Story hash: {c['story_hash']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Publica criativos de lead gen no Meta Ads a partir de uma pasta local.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Estrutura esperada de --folder:
  temp/Unidade-SP/
    Produto-A/
      CLIENTE---PRODUTO-A-SP.jpg           ← feed (quadrado)
      CLIENTE---PRODUTO-A-STORY-SP.jpg     ← story (vertical)
      CLIENTE---PRODUTO-A-B-SP.jpg         ← feed variante B
      CLIENTE---PRODUTO-A-STORY-B-SP.jpg   ← story variante B
    Produto-B/
      ...
        """,
    )
    p.add_argument("--account",    required=True,  help="ID da conta (ex: act_XXXXXXXXXXXXXXXXXX)")
    p.add_argument("--adset",      required=True,  help="ID do conjunto de anúncios")
    p.add_argument("--form",       required=True,  help="ID do formulário instantâneo")
    p.add_argument("--page",       required=True,  help="ID da Página do Facebook")
    p.add_argument("--instagram",  required=True,  help="ID da conta do Instagram")
    p.add_argument("--folder",     required=True,  help="Pasta-raiz com subpastas por criativo")
    p.add_argument("--unit",       required=True,  help="Unidade ou localização (ex: São Paulo)")
    p.add_argument("--product",    required=True,  help="Produto/segmento (ex: Técnico)")
    p.add_argument("--caption",    required=True,  help="Legenda dos anúncios")
    p.add_argument("--campaign",   default="",     help="ID da campanha (opcional, para log)")
    p.add_argument("--status",     default="PAUSED", choices=["PAUSED", "ACTIVE"],
                   help="Status inicial dos anúncios (default: PAUSED)")
    p.add_argument("--prefix",     default="",     help="Prefixo no nome do anúncio (ex: '* ')")
    p.add_argument("--subfolders", default="",     help="Subpastas a processar, separadas por vírgula (default: todas)")
    return p


if __name__ == "__main__":
    args = _parser().parse_args()
    try:
        publish({
            "account_id":   args.account,
            "adset_id":     args.adset,
            "form_id":      args.form,
            "page_id":      args.page,
            "instagram_id": args.instagram,
            "folder":       args.folder,
            "unit":         args.unit,
            "product":      args.product,
            "caption":      args.caption,
            "campaign_id":  args.campaign,
            "ad_status":    args.status,
            "prefix":       args.prefix,
            "subfolders":   [s.strip() for s in args.subfolders.split(",")] if args.subfolders else [],
        })
    except (FileNotFoundError, EnvironmentError, ValueError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
