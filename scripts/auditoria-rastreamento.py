#!/usr/bin/env python3
"""
auditoria-rastreamento.py
=================
Auditoria de rastreamento e validação de UTMs para mktOS Mídia.

Três ações:
  validate-params  — valida UTMs de uma URL, prediz GA4 channel group, retorna quality score 0-100
  audit-utms       — valida lista de URLs em batch, retorna issues por URL com severidade
  check-naming     — valida nomenclatura de campanhas contra um padrão configurável

Uso:
    python auditoria-rastreamento.py --action validate-params \
        --url "https://site.com?utm_source=facebook&utm_medium=paid_social&utm_campaign=promo-junho"

    python auditoria-rastreamento.py --action audit-utms \
        --urls '[{"url":"https://site.com?utm_source=google&utm_medium=cpc&utm_campaign=marca","adset":"Marca - Exato"}]'

    python auditoria-rastreamento.py --action check-naming \
        --campaign-list '[{"name":"Meta - Conversao - Retargeting","platform":"meta"},{"name":"Google Search Marca","platform":"google"}]' \
        --naming-pattern "{plataforma} - {tipo} - {estrategia}"
"""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# ---------------------------------------------------------------------------
# GA4 Channel Groups — replica as regras do gerador-utm.py
# ---------------------------------------------------------------------------

GA4_CHANNEL_RULES = [
    ("Paid Search",   {"medium": ["cpc", "ppc", "paid_search", "paidsearch"]}),
    ("Paid Social",   {"medium": ["paid_social", "paidsocial"],
                       "source": ["facebook", "instagram", "linkedin", "twitter", "tiktok", "pinterest", "meta"]}),
    ("Display",       {"medium": ["display", "banner", "cpm"]}),
    ("Video",         {"medium": ["video"]}),
    ("Email",         {"medium": ["email"]}),
    ("SMS",           {"medium": ["sms"]}),
    ("Affiliates",    {"medium": ["affiliate"]}),
    ("Referral",      {"medium": ["referral"]}),
    ("Organic Search",{"medium": ["organic"]}),
    ("Organic Social",{"medium": ["social", "organic_social"],
                       "source": ["facebook", "instagram", "linkedin", "twitter", "tiktok", "pinterest"]}),
    ("Direct",        {"medium": ["(none)"], "source": ["(direct)"]}),
]

# Parâmetros UTM obrigatórios
REQUIRED_PARAMS = ["utm_source", "utm_medium", "utm_campaign"]

# Regex de valor válido: lowercase, apenas letras, dígitos, hífen, underscore, ponto
VALID_VALUE_RE = re.compile(r"^[a-z0-9_\-\.]+$")


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

def _detect_ga4_channel(source: str, medium: str) -> str:
    for channel, rules in GA4_CHANNEL_RULES:
        medium_ok = medium in rules.get("medium", [])
        sources   = rules.get("source", [])
        if medium_ok:
            if sources and source not in sources:
                continue
            return channel
    # Paid Social por source mesmo com medium genérico
    if source in ("facebook", "instagram", "meta", "tiktok", "linkedin", "pinterest", "twitter"):
        return "Paid Social"
    return "Unassigned"


def _issue(severity: str, param: str, message: str) -> dict:
    return {"severity": severity, "param": param, "message": message}


def _quality_score(issues: list) -> int:
    score = 100
    deductions = {"error": 20, "warning": 10, "info": 0}
    for issue in issues:
        score -= deductions.get(issue["severity"], 0)
    return max(0, score)


# ---------------------------------------------------------------------------
# Ação 1: validate-params
# ---------------------------------------------------------------------------

def validate_params(url: str, platform_hint: str = "") -> dict:
    """
    Valida os parâmetros UTM de uma única URL.
    Retorna quality_score (0-100), ga4_channel e lista de issues.
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)

    # Normaliza: parse_qs retorna listas
    params = {k: v[0] for k, v in qs.items()}
    utm_params = {k: v for k, v in params.items() if k.startswith("utm_")}

    issues = []

    # 1. Parâmetros obrigatórios
    for p in REQUIRED_PARAMS:
        if p not in utm_params or not utm_params[p].strip():
            issues.append(_issue("error", p, f"{p} ausente — obrigatório para rastreamento GA4"))

    # 2. Verificações de formato por parâmetro presente
    for param, value in utm_params.items():
        # Letras maiúsculas
        if value != value.lower():
            issues.append(_issue(
                "error", param,
                f"Valor '{value}' contém maiúsculas — GA4 trata como case-sensitive, use lowercase"
            ))

        # Espaços
        if " " in value:
            issues.append(_issue(
                "error", param,
                f"Valor '{value}' contém espaços — substitua por underscore (_)"
            ))

        # Caracteres especiais (exceto hífen, underscore, ponto)
        clean = value.lower().replace(" ", "_")
        if not VALID_VALUE_RE.match(clean) if clean else False:
            issues.append(_issue(
                "warning", param,
                f"Valor '{value}' contém caracteres especiais — pode causar problemas de parsing"
            ))

    # 3. utm_campaign > 50 chars
    campaign = utm_params.get("utm_campaign", "")
    if len(campaign) > 50:
        issues.append(_issue(
            "warning", "utm_campaign",
            f"Nome da campanha tem {len(campaign)} chars — limite recomendado: 50"
        ))

    # 4. Parâmetros duplicados (ex: utm_source=google&utm_source=goog)
    for k, v in qs.items():
        if len(v) > 1:
            issues.append(_issue(
                "error", k,
                f"Parâmetro '{k}' aparece {len(v)} vezes na URL — mantenha apenas um"
            ))

    # 5. Google auto-tagging + UTMs simultâneos
    if "gclid" in params and "utm_source" in utm_params:
        issues.append(_issue(
            "warning", "gclid",
            "auto-tagging (gclid) e UTMs manuais coexistem — pode causar dados duplicados no GA4"
        ))

    # 6. GA4 channel group
    source = utm_params.get("utm_source", "").lower()
    medium = utm_params.get("utm_medium", "").lower()
    ga4_channel = _detect_ga4_channel(source, medium) if source and medium else "Unassigned"

    if ga4_channel == "Unassigned" and source and medium:
        issues.append(_issue(
            "warning", "utm_medium",
            f"Combinação source='{source}' medium='{medium}' não mapeia para nenhum GA4 channel group padrão"
        ))

    # 7. Validação de coerência source × platform_hint
    PLATFORM_EXPECTED_SOURCES = {
        "google": ["google"],
        "meta":   ["facebook", "instagram", "meta"],
        "tiktok": ["tiktok"],
        "linkedin": ["linkedin"],
    }
    if platform_hint and platform_hint.lower() in PLATFORM_EXPECTED_SOURCES:
        expected = PLATFORM_EXPECTED_SOURCES[platform_hint.lower()]
        if source and source not in expected:
            issues.append(_issue(
                "warning", "utm_source",
                f"utm_source='{source}' parece inconsistente com plataforma '{platform_hint}' (esperado: {expected})"
            ))

    score = _quality_score(issues)

    return {
        "status": "ok",
        "url": url,
        "utm_params": utm_params,
        "ga4_channel": ga4_channel,
        "quality_score": score,
        "issues": issues,
        "issues_count": {
            "error":   sum(1 for i in issues if i["severity"] == "error"),
            "warning": sum(1 for i in issues if i["severity"] == "warning"),
            "info":    sum(1 for i in issues if i["severity"] == "info"),
        },
    }


# ---------------------------------------------------------------------------
# Ação 2: audit-utms (batch)
# ---------------------------------------------------------------------------

def audit_utms(urls_payload: list) -> dict:
    """
    Valida uma lista de URLs em batch.
    Cada item da lista deve ter: {"url": "...", "adset": "..." (opcional), "platform": "..." (opcional)}
    """
    results = []
    total_errors   = 0
    total_warnings = 0

    for item in urls_payload:
        url      = item.get("url", "")
        adset    = item.get("adset", "")
        platform = item.get("platform", "")

        if not url:
            results.append({"adset": adset, "url": "", "status": "skipped", "reason": "URL vazia"})
            continue

        validation = validate_params(url, platform_hint=platform)
        total_errors   += validation["issues_count"]["error"]
        total_warnings += validation["issues_count"]["warning"]

        results.append({
            "adset":          adset,
            "url":            url,
            "ga4_channel":    validation["ga4_channel"],
            "quality_score":  validation["quality_score"],
            "issues":         validation["issues"],
            "issues_count":   validation["issues_count"],
        })

    results.sort(key=lambda r: r.get("quality_score", 100))

    return {
        "status": "ok",
        "total_urls":    len(results),
        "total_errors":   total_errors,
        "total_warnings": total_warnings,
        "overall_health": "ok" if total_errors == 0 else ("warning" if total_warnings > 0 and total_errors == 0 else "critical"),
        "results": results,
    }


# ---------------------------------------------------------------------------
# Ação 3: check-naming
# ---------------------------------------------------------------------------

def check_naming(campaign_list: list, naming_pattern: str = "") -> dict:
    """
    Valida a nomenclatura de campanhas.
    Padrão default: {plataforma} - {tipo} - {estrategia}
    Aceita padrão customizado como string com tokens entre chaves.
    """
    default_pattern = "{plataforma} - {tipo} - {estrategia}"
    pattern = naming_pattern.strip() if naming_pattern else default_pattern

    # Converte o padrão em regex: tokens viram grupos nomeados
    token_re = re.compile(r"\{([a-z_]+)\}")
    tokens   = token_re.findall(pattern)

    # Regex para validar: cada token aceita [^-]+ (qualquer coisa exceto separador)
    separator = re.sub(r"\{[a-z_]+\}", "XXTOKEN", pattern)
    separator_parts = separator.split("XXTOKEN")
    # Escapa separadores e constrói regex
    regex_parts = []
    for i, sep in enumerate(separator_parts):
        if sep:
            regex_parts.append(re.escape(sep.strip()))
        if i < len(tokens):
            regex_parts.append(f"(?P<{tokens[i]}>.+?)")
    pattern_regex = re.compile("^" + "".join(regex_parts) + "$", re.IGNORECASE)

    results  = []
    ok_count = 0
    ko_count = 0

    for item in campaign_list:
        name     = item.get("name", "")
        platform = item.get("platform", "")
        issues   = []

        match = pattern_regex.match(name.strip())
        if not match:
            issues.append(_issue(
                "error", "name",
                f"Nome '{name}' não segue o padrão '{pattern}'"
            ))
            ko_count += 1
        else:
            ok_count += 1
            groups = match.groupdict()

            # Valida token 'plataforma' se presente e platform_hint fornecido
            if "plataforma" in groups and platform:
                if platform.lower() not in groups["plataforma"].lower():
                    issues.append(_issue(
                        "warning", "plataforma",
                        f"Token plataforma='{groups['plataforma']}' pode não corresponder à plataforma '{platform}'"
                    ))

            # Verifica comprimento total
            if len(name) > 80:
                issues.append(_issue(
                    "warning", "name",
                    f"Nome com {len(name)} chars — recomendado até 80 para legibilidade"
                ))

        results.append({
            "name":     name,
            "platform": platform,
            "valid":    match is not None,
            "tokens":   match.groupdict() if match else {},
            "issues":   issues,
        })

    return {
        "status": "ok",
        "pattern_used":    pattern,
        "total":           len(results),
        "valid_count":     ok_count,
        "invalid_count":   ko_count,
        "results":         results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Auditoria de rastreamento e validação de UTMs"
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["validate-params", "audit-utms", "check-naming"],
        help=(
            "validate-params: valida UTMs de uma URL | "
            "audit-utms: batch de URLs | "
            "check-naming: nomenclatura de campanhas"
        ),
    )
    parser.add_argument("--url",             default="", help="URL para --action validate-params")
    parser.add_argument("--platform",        default="", help="Plataforma de origem (google, meta, tiktok, linkedin)")
    parser.add_argument("--urls",            default="", help="JSON array de URLs para --action audit-utms")
    parser.add_argument("--campaign-list",   default="", help="JSON array de campanhas para --action check-naming")
    parser.add_argument("--naming-pattern",  default="", help="Padrão de nomenclatura (ex: '{plataforma} - {tipo} - {estrategia}')")
    parser.add_argument("--output-format",   choices=["json", "summary"], default="json")

    args = parser.parse_args()

    if args.action == "validate-params":
        if not args.url:
            print(json.dumps({"status": "error", "reason": "Informe --url"}, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)
        result = validate_params(args.url, platform_hint=args.platform)

    elif args.action == "audit-utms":
        if not args.urls:
            print(json.dumps({"status": "error", "reason": "Informe --urls como JSON array"}, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)
        try:
            urls_payload = json.loads(args.urls)
        except json.JSONDecodeError as e:
            print(json.dumps({"status": "error", "reason": f"JSON inválido em --urls: {e}"}, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)
        result = audit_utms(urls_payload)

    elif args.action == "check-naming":
        if not args.campaign_list:
            print(json.dumps({"status": "error", "reason": "Informe --campaign-list como JSON array"}, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)
        try:
            campaigns = json.loads(args.campaign_list)
        except json.JSONDecodeError as e:
            print(json.dumps({"status": "error", "reason": f"JSON inválido em --campaign-list: {e}"}, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)
        result = check_naming(campaigns, naming_pattern=args.naming_pattern)

    if args.output_format == "summary" and args.action == "audit-utms":
        _print_audit_summary(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def _print_audit_summary(result: dict):
    print(f"URLs auditadas: {result['total_urls']}  |  Erros: {result['total_errors']}  |  Avisos: {result['total_warnings']}")
    print(f"Saúde geral: {result['overall_health'].upper()}")
    print()
    for r in result["results"]:
        status = "✓" if r["quality_score"] == 100 else ("⚠" if r["issues_count"]["error"] == 0 else "✗")
        print(f"{status} [{r['quality_score']:3d}] {r.get('adset','') or r['url'][:60]}  →  {r['ga4_channel']}")
        for issue in r["issues"]:
            prefix = "  ERROR  " if issue["severity"] == "error" else "  WARN   "
            print(f"{prefix}{issue['param']}: {issue['message']}")


if __name__ == "__main__":
    main()
