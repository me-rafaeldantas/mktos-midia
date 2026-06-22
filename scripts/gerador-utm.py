#!/usr/bin/env python3
"""Geração em lote de parâmetros UTM com validação de agrupamento de canal GA4."""

import argparse
import csv
import json
import re
import sys
import io
import base64
from pathlib import Path
from urllib.parse import urlencode, urlparse

# Agrupamentos de canal padrão GA4 e seus padrões esperados de source/medium
GA4_CHANNEL_RULES = {
    "Organic Search": {"medium": ["organic"]},
    "Paid Search": {"medium": ["cpc", "ppc", "paid_search"]},
    "Display": {"medium": ["display", "banner", "cpm"]},
    "Paid Social": {"medium": ["paid_social", "paidsocial"], "source": ["facebook", "instagram", "linkedin", "twitter", "tiktok", "pinterest"]},
    "Organic Social": {"medium": ["social", "organic_social"], "source": ["facebook", "instagram", "linkedin", "twitter", "tiktok", "pinterest"]},
    "Email": {"medium": ["email"]},
    "Affiliates": {"medium": ["affiliate"]},
    "Referral": {"medium": ["referral"]},
    "SMS": {"medium": ["sms"]},
    "Video": {"medium": ["video"]},
    "Audio": {"medium": ["audio", "podcast"]},
}


def sanitize_param(value):
    """Minúsculas, substitua espaços por underscores, remova caracteres não seguros para URL."""
    if not value:
        return ""
    value = value.strip().lower()
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"[^a-z0-9_\-.]", "", value)
    return value


def validate_base_url(url):
    """Verifique se uma URL tem scheme e netloc."""
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)
    if not parsed.netloc:
        return None, "URL inválida: nenhum domínio encontrado"
    return url, None


def detect_ga4_channel(source, medium):
    """Retorne o provável agrupamento de canal padrão GA4."""
    for channel, rules in GA4_CHANNEL_RULES.items():
        medium_match = medium in rules.get("medium", [])
        source_list = rules.get("source", [])
        if medium_match:
            if source_list and source not in source_list:
                continue
            return channel
    return "Unassigned"


def generate_qr(url):
    """Retorne código QR PNG codificado em base64 ou None se biblioteca indisponível."""
    try:
        import qrcode
        from io import BytesIO
        qr = qrcode.make(url)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except ImportError:
        return None


def build_utm_url(base_url, source, medium, campaign, content="", term="", with_qr=False):
    """Construa uma única URL marcada com UTM e retorne um dict de resultado."""
    base_url, err = validate_base_url(base_url)
    if err:
        return {"error": err, "base_url": base_url}

    params = {}
    source = sanitize_param(source)
    medium = sanitize_param(medium)
    campaign = sanitize_param(campaign)
    content = sanitize_param(content)
    term = sanitize_param(term)

    warnings = []
    if not source:
        warnings.append("utm_source está vazio")
    if not medium:
        warnings.append("utm_medium está vazio")
    if not campaign:
        warnings.append("utm_campaign está vazio")

    if source:
        params["utm_source"] = source
    if medium:
        params["utm_medium"] = medium
    if campaign:
        params["utm_campaign"] = campaign
    if content:
        params["utm_content"] = content
    if term:
        params["utm_term"] = term

    separator = "&" if "?" in base_url else "?"
    tagged_url = base_url + separator + urlencode(params) if params else base_url

    channel = detect_ga4_channel(source, medium)

    result = {
        "base_url": base_url,
        "tagged_url": tagged_url,
        "params": params,
        "ga4_channel_grouping": channel,
    }
    if warnings:
        result["warnings"] = warnings
    if with_qr:
        qr_data = generate_qr(tagged_url)
        if qr_data:
            result["qr_code_base64_png"] = qr_data
        else:
            result["qr_code_note"] = "Instale pacotes 'qrcode' e 'Pillow' para geração de QR"
    return result


def process_csv(filepath, with_qr=False):
    """Leia um CSV com colunas: base_url, source, medium, campaign, content, term."""
    path = Path(filepath)
    if not path.exists():
        return {"error": f"Arquivo não encontrado: {filepath}"}
    results = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                r = build_utm_url(
                    base_url=row.get("base_url", row.get("url", "")),
                    source=row.get("source", row.get("utm_source", "")),
                    medium=row.get("medium", row.get("utm_medium", "")),
                    campaign=row.get("campaign", row.get("utm_campaign", "")),
                    content=row.get("content", row.get("utm_content", "")),
                    term=row.get("term", row.get("utm_term", "")),
                    with_qr=with_qr,
                )
                r["row"] = i + 1
                results.append(r)
    except Exception as e:
        return {"error": f"Parsing CSV falhou: {str(e)}"}
    return results


def main():
    parser = argparse.ArgumentParser(description="Geração em lote de parâmetros UTM com validação GA4")
    parser.add_argument("--base-url", help="URL base para marcar")
    parser.add_argument("--campaign", default="", help="Nome da campanha")
    parser.add_argument("--source", default="", help="Fonte de tráfego")
    parser.add_argument("--medium", default="", help="Meio de tráfego")
    parser.add_argument("--content", default="", help="Identificador de conteúdo de anúncio")
    parser.add_argument("--term", default="", help="Termo de palavra-chave paga")
    parser.add_argument("--csv", dest="csv_file", help="Arquivo CSV para modo em lote")
    parser.add_argument("--qr", action="store_true", help="Gerar códigos QR")
    args = parser.parse_args()

    if not args.base_url and not args.csv_file:
        parser.error("Forneça --base-url ou --csv")

    if args.csv_file:
        output = {"mode": "batch", "results": process_csv(args.csv_file, with_qr=args.qr)}
    else:
        result = build_utm_url(
            base_url=args.base_url,
            source=args.source,
            medium=args.medium,
            campaign=args.campaign,
            content=args.content,
            term=args.term,
            with_qr=args.qr,
        )
        output = {"mode": "single", "result": result}

    json.dump(output, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
