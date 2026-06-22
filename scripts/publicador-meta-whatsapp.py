#!/usr/bin/env python3
"""
publicador-meta-whatsapp.py
================================
Publicação em lote de criativos WhatsApp (Mensagens Iniciadas) no Meta Ads.

Diferenças vs publicador-meta.py:
  - CTA: WHATSAPP_MESSAGE (não formulário de leads)
  - Arquivos planos (sem subpastas); unidade extraída do nome da pasta-pai
  - Roteamento por adset baseado em keyword de segmento no nome do arquivo
  - Múltiplas pastas (uma por unidade) em uma única execução

Uso:
    python publicador-meta-whatsapp.py \\
        --account   act_XXXXXXXXXXXXXXXXXX \\
        --page      XXXXXXXXXXXXXXXXXXX \\
        --instagram XXXXXXXXXXXXXXXXXXX \\
        --campaign  XXXXXXXXXXXXXXXXXXX \\
        --adset-map "SEGMENTO-A:XXXXXXXXXXXXXXXXXXX,SEGMENTO-B:XXXXXXXXXXXXXXXXXXX" \\
        --folders   temp/Unidade-SP/Produto-A temp/Unidade-RJ/Produto-A \\
        --product   "Produto A" \\
        --caption   "..." \\
        --prefix    "NEW - "

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
            "Configure o MCP meta-marketing no arquivo .mcp.json com um token válido."
        )
    return t


def _post(path: str, data: dict, token: str) -> dict:
    data["access_token"] = token
    return requests.post(f"{BASE_URL}/{path}", data=data).json()


def _ascii_slug(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")


def _active_brand_slug() -> str:
    active_file = Path(__file__).parent.parent / "data" / "clientes" / "_conta-ativa.json"
    try:
        data = json.loads(active_file.read_text())
        return data.get("slug", "")
    except (FileNotFoundError, json.JSONDecodeError):
        return ""


# ---------------------------------------------------------------------------
# Detecção de criativos (pastas planas)
# ---------------------------------------------------------------------------

def _is_story(filename: str) -> bool:
    return STORY_MARKER.upper() in Path(filename).stem.upper()


def _detect_segment(stem: str, adset_map: dict[str, str]) -> str | None:
    """Retorna a keyword de segmento encontrada no stem do arquivo."""
    stem_upper = stem.upper()
    for keyword in adset_map:
        if keyword.upper() in stem_upper:
            return keyword
    return None


def detect_creatives(folders: list[Path], adset_map: dict[str, str]) -> list[dict]:
    """
    Varre pastas planas e agrupa pares feed/story por (unit, segment).

    Retorna:
        [{"unit": str, "segment": str, "adset_id": str, "feed": Path|None, "story": Path|None}, ...]
    """
    pairs: dict[str, dict] = {}

    for folder in folders:
        if not folder.is_dir():
            print(f"⚠  Pasta não encontrada, pulando: {folder}")
            continue

        unit   = folder.parent.name          # ex: "Unidade-SP", "Unidade-RJ"
        images = [f for f in sorted(folder.iterdir()) if f.suffix.lower() in IMAGE_EXTENSIONS]

        for img in images:
            segment = _detect_segment(img.stem, adset_map)
            if segment is None:
                print(f"  ⚠  Segmento não reconhecido, pulando: {img.name}")
                continue

            key = f"{unit}__{segment}"
            if key not in pairs:
                pairs[key] = {
                    "unit":     unit,
                    "segment":  segment,
                    "adset_id": adset_map[segment],
                    "feed":     None,
                    "story":    None,
                }

            if _is_story(img.name):
                pairs[key]["story"] = img
            else:
                pairs[key]["feed"] = img

    return list(pairs.values())


# ---------------------------------------------------------------------------
# Upload de imagens
# ---------------------------------------------------------------------------

def upload_image(account_id: str, token: str, path: Path) -> str:
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
# Criação de creative e anúncio (WhatsApp)
# ---------------------------------------------------------------------------

def create_whatsapp_creative(
    account_id: str,
    token: str,
    name: str,
    page_id: str,
    instagram_user_id: str,
    feed_hash: str,
    caption: str,
) -> str:
    data = _post(
        f"{account_id}/adcreatives",
        {
            "name": name,
            "object_story_spec": json.dumps({
                "page_id": page_id,
                "instagram_user_id": instagram_user_id,
                "link_data": {
                    "message": caption,
                    "link": "https://api.whatsapp.com/send",
                    "image_hash": feed_hash,
                    "name": "Fale Conosco",
                    "call_to_action": {
                        "type": "WHATSAPP_MESSAGE",
                        "value": {
                            "app_destination": "WHATSAPP",
                            "link": "https://api.whatsapp.com/send",
                        },
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

def _ad_name(unit: str, segment: str, product: str, prefix: str = "") -> str:
    name = f"{unit} - {segment} - {product}"
    return f"{prefix}{name}" if prefix else name


# ---------------------------------------------------------------------------
# Orquestrador principal
# ---------------------------------------------------------------------------

def publish(config: dict) -> dict:
    """
    config obrigatório:
        account_id, page_id, instagram_id, adset_map, folders, product, caption

    config opcional:
        campaign_id, ad_status, prefix
    """
    _load_env()
    token = _token()

    account_id   = config["account_id"]
    page_id      = config["page_id"]
    instagram_id = config["instagram_id"]
    campaign_id  = config.get("campaign_id", "")
    folders      = [Path(f) for f in config["folders"]]
    adset_map    = config["adset_map"]
    product      = config["product"]
    caption      = config["caption"]
    ad_status    = config.get("ad_status", "PAUSED")
    prefix       = config.get("prefix", "")

    result = {
        "timestamp":      datetime.now().isoformat(timespec="seconds"),
        "account_id":     account_id,
        "campaign_id":    campaign_id,
        "product":        product,
        "source_folders": [str(f) for f in folders],
        "adset_map":      adset_map,
        "summary":        {"images_uploaded": 0, "creatives_created": 0, "ads_created": 0, "status": "ok"},
        "images":         [],
        "creatives":      [],
        "ads":            [],
        "errors":         [],
    }

    items = detect_creatives(folders, adset_map)
    if not items:
        raise ValueError("Nenhum criativo detectado nas pastas informadas.")

    print(f"\n=== Publicação WhatsApp: {product} ===")
    print(f"{len(items)} criativo(s) detectado(s)\n")

    for item in items:
        unit     = item["unit"]
        segment  = item["segment"]
        adset_id = item["adset_id"]
        name     = _ad_name(unit, segment, product, prefix)

        print(f"▸ {name}  [adset: {adset_id}]")

        feed_hash  = None
        story_hash = None

        # Upload feed
        if item["feed"]:
            try:
                feed_hash = upload_image(account_id, token, item["feed"])
                result["images"].append({"key": f"{unit}_{segment}_feed", "path": str(item["feed"]), "hash": feed_hash})
                result["summary"]["images_uploaded"] += 1
                print(f"  ✓ Feed  → {feed_hash}")
            except Exception as e:
                result["errors"].append({"step": "upload_feed", "creative": name, "error": str(e)})
                print(f"  ✗ Feed upload falhou: {e}")
                continue

        # Upload story
        if item["story"]:
            try:
                story_hash = upload_image(account_id, token, item["story"])
                result["images"].append({"key": f"{unit}_{segment}_story", "path": str(item["story"]), "hash": story_hash})
                result["summary"]["images_uploaded"] += 1
                print(f"  ✓ Story → {story_hash}")
                print(f"  ⚠  Story salva mas precisa ser adicionada manualmente no Ads Manager")
            except Exception as e:
                result["errors"].append({"step": "upload_story", "creative": name, "error": str(e)})
                print(f"  ⚠  Story upload falhou: {e}")

        if not feed_hash:
            result["errors"].append({"step": "creative", "creative": name, "error": "Sem imagem feed"})
            continue

        # Criar creative
        try:
            creative_id = create_whatsapp_creative(
                account_id, token, name, page_id, instagram_id, feed_hash, caption
            )
            result["creatives"].append({
                "name":      name,
                "id":        creative_id,
                "feed_hash": feed_hash,
                "story_hash": story_hash,
                "adset_id":  adset_id,
            })
            result["summary"]["creatives_created"] += 1
            print(f"  ✓ Creative → {creative_id}")
        except Exception as e:
            result["errors"].append({"step": "creative", "creative": name, "error": str(e)})
            print(f"  ✗ Creative falhou: {e}")
            continue

        # Criar anúncio
        try:
            ad_id = create_ad(account_id, token, name, adset_id, creative_id, ad_status)
            result["ads"].append({
                "name":        name,
                "id":          ad_id,
                "creative_id": creative_id,
                "adset_id":    adset_id,
                "status":      ad_status.upper(),
            })
            result["summary"]["ads_created"] += 1
            print(f"  ✓ Anúncio → {ad_id} [{ad_status.upper()}]")
        except Exception as e:
            result["errors"].append({"step": "ad", "creative": name, "error": str(e)})
            print(f"  ✗ Anúncio falhou: {e}")

    total   = len(items)
    created = result["summary"]["ads_created"]
    result["summary"]["status"] = "ok" if created == total else ("partial" if created > 0 else "failed")

    _save_report(result, product)
    _print_summary(result)
    return result


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _save_report(result: dict, product: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date    = datetime.now().strftime("%Y-%m-%d")
    brand   = _active_brand_slug()
    context = _ascii_slug(f"{brand}-{product}" if brand else product)
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

def _parse_adset_map(value: str) -> dict[str, str]:
    """Parseia 'SEGMENTO-A:id1,SEGMENTO-B:id2' em {"SEGMENTO-A": "id1", ...}"""
    result = {}
    for part in value.split(","):
        part = part.strip()
        if ":" not in part:
            raise argparse.ArgumentTypeError(
                f"Formato inválido em --adset-map: '{part}' (esperado KEY:adset_id)"
            )
        key, _, adset_id = part.partition(":")
        result[key.strip()] = adset_id.strip()
    return result


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Publica criativos WhatsApp (Mensagens Iniciadas) no Meta Ads.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Estrutura esperada das pastas (arquivos planos, sem subpastas):
  temp/Unidade-SP/Produto-A/
    CLIENTE---PRODUTO-A-SEGMENTO-X-SP.jpg        ← feed
    CLIENTE---PRODUTO-A-SEGMENTO-X-STORY-SP.jpg  ← story
    CLIENTE---PRODUTO-A-SEGMENTO-Y-SP.jpg
    ...

  A unidade é extraída do nome da pasta-pai (ex: "Unidade-SP").
  O segmento é detectado por keyword no nome do arquivo.
        """,
    )
    p.add_argument("--account",    required=True,  help="ID da conta (ex: act_XXXXXXXXXXXXXXXXXX)")
    p.add_argument("--page",       required=True,  help="ID da Página do Facebook")
    p.add_argument("--instagram",  required=True,  help="ID da conta do Instagram")
    p.add_argument("--campaign",   default="",     help="ID da campanha (para log)")
    p.add_argument("--adset-map",  required=True,
                   help="Mapeamento keyword→adset: 'SEGMENTO-A:id,SEGMENTO-B:id'")
    p.add_argument("--folders",    required=True,  nargs="+",
                   help="Pastas planas com as imagens (uma por unidade)")
    p.add_argument("--product",    required=True,  help="Nome do produto (ex: Produto A)")
    p.add_argument("--caption",    required=True,  help="Legenda dos anúncios")
    p.add_argument("--prefix",     default="",     help="Prefixo no nome do anúncio (ex: 'NEW - ')")
    p.add_argument("--status",     default="PAUSED", choices=["PAUSED", "ACTIVE"],
                   help="Status inicial dos anúncios (default: PAUSED)")
    return p


if __name__ == "__main__":
    args = _parser().parse_args()
    try:
        publish({
            "account_id":      args.account,
            "page_id":         args.page,
            "instagram_id":    args.instagram,
            "campaign_id":     args.campaign,
            "adset_map":       _parse_adset_map(args.adset_map),
            "folders":         args.folders,
            "product":         args.product,
            "caption":         args.caption,
            "prefix":          args.prefix,
            "ad_status":       args.status,
        })
    except (FileNotFoundError, EnvironmentError, ValueError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
