#!/usr/bin/env python3
"""
planejador-keywords.py
==================
Pesquisa de palavras-chave via Google Ads Keyword Planner para mktOS Mídia.

Fontes de dados em cascata:
  1. API Google Ads (GenerateKeywordIdeas) — dados exatos em tempo real
  2. CSV exportado do Google Keyword Planner — dados reais exportados manualmente
  3. WebSearch via skill — estimativas de fontes públicas (último recurso)

Uso:
    # Via API
    python planejador-keywords.py --account 1234567890 --action suggest \
        --seed-keywords "escola técnica,cursos técnicos" --language pt --geo 2076

    # Via URL de referência
    python planejador-keywords.py --account 1234567890 --action suggest \
        --url "https://escola.com.br" --language pt --geo 1001773

    # Importar CSV do Keyword Planner (fallback nível 2)
    python planejador-keywords.py --action import-csv --file /caminho/keywords.csv
"""

import argparse
import csv
import io
import json
import sys
from pathlib import Path

CLIENTES_DIR = Path(__file__).parent.parent / "data" / "clientes"

LANGUAGE_CODES = {
    "pt": 1014,
    "en": 1000,
    "es": 1003,
    "fr": 1002,
    "de": 1001,
}

COMPETITION_MAP = {
    0: "UNSPECIFIED",
    1: "UNKNOWN",
    2: "LOW",
    3: "MEDIUM",
    4: "HIGH",
}

# Mapeamento de texto → label normalizado (PT e EN)
COMPETITION_TEXT_MAP = {
    "baixa": "LOW",   "low": "LOW",
    "média": "MEDIUM", "media": "MEDIUM", "medium": "MEDIUM",
    "alta": "HIGH",   "high": "HIGH",
}

# Nomes de colunas aceitos (PT e EN), em minúsculo para comparação
COL_CANDIDATES = {
    "keyword":          ["palavra-chave", "keyword"],
    "volume":           ["média de pesquisas mensais", "avg. monthly searches", "average monthly searches"],
    "competition":      ["concorrência", "concorrencia", "competition"],
    "competition_idx":  ["concorrência (valor indexado)", "concorrencia (valor indexado)", "competition (indexed value)"],
    "bid_low":          ["lance no topo da página (intervalo baixo)", "lance no topo da pagina (intervalo baixo)",
                         "top of page bid (low range)"],
    "bid_high":         ["lance no topo da página (intervalo alto)", "lance no topo da pagina (intervalo alto)",
                         "top of page bid (high range)"],
}


# ---------------------------------------------------------------------------
# Helpers de parsing CSV
# ---------------------------------------------------------------------------

def _find_col(headers: list, candidates: list):
    """Retorna o nome real da coluna que bate com algum candidato (case-insensitive)."""
    for h in headers:
        h_lower = h.lower().strip()
        for c in candidates:
            if c in h_lower:
                return h
    return None


def _parse_volume(val: str) -> int:
    """
    Converte volume mensal do Keyword Planner para int.
    Aceita: "1.000 - 10.000", "1,000 - 10,000", "< 10", "> 100.000", "5000".
    Para faixas, usa o ponto médio.
    """
    val = val.strip().replace(" ", "")
    if not val or val == "--":
        return 0

    def _clean(s: str) -> int:
        s = s.replace(".", "").replace(",", "").replace("<", "").replace(">", "")
        try:
            return int(s)
        except ValueError:
            return 0

    if "-" in val:
        parts = val.split("-", 1)
        low = _clean(parts[0])
        high = _clean(parts[1])
        return (low + high) // 2

    return _clean(val)


def _parse_bid(val: str) -> int:
    """
    Converte valor de lance (BRL ou USD) para micros.
    Aceita: "R$ 1,23", "1.234,56", "1,234.56", "2.50".
    """
    val = val.strip()
    for prefix in ("R$", "US$", "$", "€"):
        val = val.replace(prefix, "")
    val = val.strip()

    if not val or val in ("--", "-"):
        return 0

    # Detecta formato: ambos "." e ","
    if "," in val and "." in val:
        if val.index(",") > val.index("."):
            # PT: "1.234,56" → dot=milhar, comma=decimal
            val = val.replace(".", "").replace(",", ".")
        else:
            # EN: "1,234.56" → comma=milhar, dot=decimal
            val = val.replace(",", "")
    elif "," in val:
        # Apenas comma → decimal PT: "1,23"
        val = val.replace(",", ".")

    try:
        return int(float(val) * 1_000_000)
    except ValueError:
        return 0


def _parse_competition_index(val: str) -> int:
    val = val.strip().replace(",", ".").replace("%", "")
    try:
        return int(float(val))
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Ação 1: suggest via API
# ---------------------------------------------------------------------------

def suggest_keywords(account_id: str, seed_keywords: list[str], url: str,
                     language: str, geo: int) -> dict:
    """Chama GenerateKeywordIdeas via google-ads library."""
    try:
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException
    except ImportError:
        return {
            "status": "fallback",
            "fallback_level": 2,
            "reason": "google-ads library não instalada (pip install google-ads).",
            "keywords": [],
        }

    try:
        client = GoogleAdsClient.load_from_storage()
    except Exception as exc:
        return {
            "status": "fallback",
            "fallback_level": 2,
            "reason": f"Credenciais Google Ads indisponíveis (~/google-ads.yaml): {exc}",
            "keywords": [],
        }

    kp_service = client.get_service("KeywordPlanIdeaService")
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = str(account_id).replace("-", "")

    lang_id = LANGUAGE_CODES.get(language.lower(), LANGUAGE_CODES["pt"])
    request.language = f"languageConstants/{lang_id}"

    if geo:
        request.geo_target_constants.append(f"geoTargetConstants/{geo}")

    request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH

    if seed_keywords:
        keyword_seed = client.get_type("KeywordSeed")
        keyword_seed.keywords.extend(seed_keywords)
        request.keyword_seed = keyword_seed
    elif url:
        site_seed = client.get_type("SiteSeed")
        site_seed.site = url
        request.site_seed = site_seed
    else:
        return {"status": "error", "reason": "Informe --seed-keywords ou --url", "keywords": []}

    try:
        response = kp_service.generate_keyword_ideas(request=request)
    except GoogleAdsException as exc:
        errors = [str(e.message) for e in exc.failure.errors]
        return {
            "status": "fallback",
            "fallback_level": 2,
            "reason": f"Erro na API Google Ads: {'; '.join(errors)}",
            "keywords": [],
        }
    except Exception as exc:
        return {
            "status": "fallback",
            "fallback_level": 2,
            "reason": f"Erro inesperado: {exc}",
            "keywords": [],
        }

    results = []
    for idea in response:
        m = idea.keyword_idea_metrics
        results.append({
            "keyword": idea.text,
            "avg_monthly_searches": m.avg_monthly_searches,
            "competition": COMPETITION_MAP.get(m.competition.value, "UNKNOWN"),
            "competition_index": m.competition_index,
            "low_top_of_page_bid_micros": m.low_top_of_page_bid_micros,
            "high_top_of_page_bid_micros": m.high_top_of_page_bid_micros,
        })

    results.sort(key=lambda k: k["avg_monthly_searches"], reverse=True)

    return {
        "status": "ok",
        "data_source": "api",
        "account_id": account_id,
        "seed_keywords": seed_keywords,
        "url": url,
        "language": language,
        "geo": geo,
        "total": len(results),
        "keywords": results,
    }


# ---------------------------------------------------------------------------
# Ação 2: import-csv (fallback nível 2)
# ---------------------------------------------------------------------------

def import_csv(file_path: str) -> dict:
    """
    Importa CSV exportado do Google Keyword Planner.
    Suporta exports em PT-BR e EN. Detecta delimitador automaticamente.
    """
    path = Path(file_path).expanduser()
    if not path.exists():
        return {
            "status": "error",
            "reason": f"Arquivo não encontrado: {file_path}",
            "keywords": [],
        }

    # Lê com BOM strip (utf-8-sig cobre arquivos exportados no Windows)
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            raw = path.read_text(encoding="latin-1")
        except Exception as exc:
            return {"status": "error", "reason": f"Erro ao ler arquivo: {exc}", "keywords": []}

    lines = raw.splitlines()

    # Localiza a linha de cabeçalho (contém "palavra-chave" ou "keyword")
    header_idx = None
    for i, line in enumerate(lines):
        if "palavra-chave" in line.lower() or '"keyword"' in line.lower() or ",keyword," in line.lower() or line.lower().startswith("keyword"):
            header_idx = i
            break

    if header_idx is None:
        return {
            "status": "error",
            "reason": (
                "Cabeçalho não encontrado. Verifique se o arquivo é um export do "
                "Google Keyword Planner (Ferramentas → Planejador → Baixar ideias)."
            ),
            "keywords": [],
        }

    csv_text = "\n".join(lines[header_idx:])

    # Detecta delimitador: tenta vírgula, depois ponto-e-vírgula
    delimiter = ","
    try:
        dialect = csv.Sniffer().sniff(csv_text[:2048], delimiters=",;\t")
        delimiter = dialect.delimiter
    except csv.Error:
        pass

    reader = csv.DictReader(io.StringIO(csv_text), delimiter=delimiter)
    headers = reader.fieldnames or []

    col_kw      = _find_col(headers, COL_CANDIDATES["keyword"])
    col_vol     = _find_col(headers, COL_CANDIDATES["volume"])
    col_comp    = _find_col(headers, COL_CANDIDATES["competition"])
    col_compidx = _find_col(headers, COL_CANDIDATES["competition_idx"])
    col_bidlow  = _find_col(headers, COL_CANDIDATES["bid_low"])
    col_bidhigh = _find_col(headers, COL_CANDIDATES["bid_high"])

    if not col_kw:
        return {
            "status": "error",
            "reason": f"Coluna de keyword não encontrada. Colunas detectadas: {headers}",
            "keywords": [],
        }

    results = []
    for row in reader:
        kw = row.get(col_kw, "").strip()
        if not kw:
            continue

        vol      = _parse_volume(row.get(col_vol, "0") or "0") if col_vol else 0
        comp_raw = (row.get(col_comp, "") or "").strip().lower()
        comp     = COMPETITION_TEXT_MAP.get(comp_raw, "UNKNOWN")
        compidx  = _parse_competition_index(row.get(col_compidx, "0") or "0") if col_compidx else 0
        bidlow   = _parse_bid(row.get(col_bidlow, "0") or "0") if col_bidlow else 0
        bidhigh  = _parse_bid(row.get(col_bidhigh, "0") or "0") if col_bidhigh else 0

        results.append({
            "keyword": kw,
            "avg_monthly_searches": vol,
            "competition": comp,
            "competition_index": compidx,
            "low_top_of_page_bid_micros": bidlow,
            "high_top_of_page_bid_micros": bidhigh,
        })

    results.sort(key=lambda k: k["avg_monthly_searches"], reverse=True)

    return {
        "status": "ok",
        "data_source": "csv",
        "file": str(path),
        "total": len(results),
        "keywords": results,
        "note": "Volumes são médias de faixas do Keyword Planner — use como referência, não como dado exato.",
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Pesquisa de palavras-chave — API Google Ads ou importação de CSV"
    )
    parser.add_argument(
        "--account",
        default="",
        help="ID da conta Google Ads (ex: 1234567890 ou 123-456-7890)",
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["suggest", "import-csv"],
        help=(
            "suggest: buscar via API Keyword Planner | "
            "import-csv: importar CSV exportado manualmente"
        ),
    )
    parser.add_argument(
        "--seed-keywords",
        default="",
        help="Keywords semente separadas por vírgula (para --action suggest)",
    )
    parser.add_argument(
        "--url",
        default="",
        help="URL de referência para sugestões (alternativa ao --seed-keywords)",
    )
    parser.add_argument(
        "--language",
        default="pt",
        help="Código de idioma: pt, en, es, fr, de (padrão: pt)",
    )
    parser.add_argument(
        "--geo",
        type=int,
        default=2076,
        help="Código de geo do Google Ads (padrão: 2076 = Brasil; 1001773 = RJ)",
    )
    parser.add_argument(
        "--file",
        default="",
        help="Caminho do arquivo CSV (para --action import-csv)",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "table"],
        default="json",
        help="Formato de saída: json (padrão) ou table",
    )

    args = parser.parse_args()

    if args.action == "suggest":
        seeds = [k.strip() for k in args.seed_keywords.split(",") if k.strip()] if args.seed_keywords else []
        if not seeds and not args.url:
            print(
                json.dumps({"status": "error", "reason": "Informe --seed-keywords ou --url"}, ensure_ascii=False),
                file=sys.stderr,
            )
            sys.exit(1)

        result = suggest_keywords(
            account_id=args.account,
            seed_keywords=seeds,
            url=args.url,
            language=args.language,
            geo=args.geo,
        )

    elif args.action == "import-csv":
        if not args.file:
            print(
                json.dumps({"status": "error", "reason": "Informe --file /caminho/arquivo.csv"}, ensure_ascii=False),
                file=sys.stderr,
            )
            sys.exit(1)
        result = import_csv(args.file)

    if args.output_format == "table" and result.get("keywords"):
        _print_table(result["keywords"], result.get("data_source", ""))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def _print_table(keywords: list[dict], source: str = ""):
    source_label = f" [{source.upper()}]" if source else ""
    header = (
        f"{'Keyword':<45} {'Vol/mês':>8} {'Compet.':>8} {'Idx':>4} "
        f"{'CPC Min (R$)':>12} {'CPC Max (R$)':>12}"
    )
    print(f"Fonte{source_label}")
    print(header)
    print("-" * len(header))
    for kw in keywords:
        low_brl  = kw["low_top_of_page_bid_micros"]  / 1_000_000 if kw["low_top_of_page_bid_micros"]  else 0
        high_brl = kw["high_top_of_page_bid_micros"] / 1_000_000 if kw["high_top_of_page_bid_micros"] else 0
        print(
            f"{kw['keyword']:<45} {kw['avg_monthly_searches']:>8,} {kw['competition']:>8} "
            f"{kw['competition_index']:>4} {low_brl:>12.2f} {high_brl:>12.2f}"
        )


if __name__ == "__main__":
    main()
