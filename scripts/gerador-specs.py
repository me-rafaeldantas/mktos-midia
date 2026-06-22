#!/usr/bin/env python3
"""
gerador-specs.py
========================
Database de especificações técnicas de assets para plataformas de mídia paga.

Retorna specs completas (dimensões, peso, safe zone, codec, nomenclatura) para
qualquer combinação de plataforma e formato. Base para briefs de produção criativa.

Uso:
    python3 gerador-specs.py --platforms meta --formats feed,stories,reels --variants 3 --output-format json
    python3 gerador-specs.py --platforms youtube --formats bumper,skippable --output-format checklist
    python3 gerador-specs.py --platforms meta,google,youtube --output-format table
    python3 gerador-specs.py --platforms tiktok,linkedin --variants 2 --output-format checklist
    python3 gerador-specs.py --list-platforms
"""

import argparse
import json
import sys

# ── Database de Specs ──────────────────────────────────────────────────────────
# Campos por formato:
#   plataforma        str   — nome exibível da plataforma
#   formato           str   — nome exibível do formato
#   tipo              str   — "imagem" | "video" | "imagem_ou_video"
#   tags              list  — aliases para filtro via --formats
#   largura_px        int   — largura em pixels
#   altura_px         int   — altura em pixels
#   ratio             str   — ex. "1:1", "9:16", "1.91:1"
#   peso_maximo_mb    float — peso máximo em MB
#   duracao_min_s     int|None  — duração mínima em segundos (vídeo)
#   duracao_max_s     int|None  — duração máxima em segundos (vídeo)
#   safe_zone_larg    int|None  — largura da safe zone em px
#   safe_zone_alt     int|None  — altura da safe zone em px
#   overlay_texto     str   — regra de sobreposição de texto
#   codec             str|None  — codec recomendado (vídeo)
#   extensoes         list  — extensões de arquivo aceitas
#   prioridade        str   — "obrigatorio" | "recomendado" | "opcional"
#   obs               str   — observação adicional

SPECS_DB = [
    # ── META ──────────────────────────────────────────────────────────────────
    {
        "plataforma": "Meta",
        "formato": "Feed Imagem 1:1",
        "tipo": "imagem",
        "tags": ["feed", "meta"],
        "largura_px": 1080, "altura_px": 1080, "ratio": "1:1",
        "peso_maximo_mb": 30,
        "duracao_min_s": None, "duracao_max_s": None,
        "safe_zone_larg": None, "safe_zone_alt": None,
        "overlay_texto": "Sem limite oficial — recomendado menos de 20% da área",
        "codec": None,
        "extensoes": ["jpg", "png"],
        "prioridade": "obrigatorio",
        "obs": "Formato principal de feed. Alta compatibilidade entre placements.",
    },
    {
        "plataforma": "Meta",
        "formato": "Feed Imagem 4:5",
        "tipo": "imagem",
        "tags": ["feed", "meta"],
        "largura_px": 1080, "altura_px": 1350, "ratio": "4:5",
        "peso_maximo_mb": 30,
        "duracao_min_s": None, "duracao_max_s": None,
        "safe_zone_larg": None, "safe_zone_alt": None,
        "overlay_texto": "Sem limite oficial — recomendado menos de 20% da área",
        "codec": None,
        "extensoes": ["jpg", "png"],
        "prioridade": "recomendado",
        "obs": "Ocupa mais espaço no feed mobile — maior viewability.",
    },
    {
        "plataforma": "Meta",
        "formato": "Stories / Reels 9:16",
        "tipo": "imagem_ou_video",
        "tags": ["stories", "reels", "meta"],
        "largura_px": 1080, "altura_px": 1920, "ratio": "9:16",
        "peso_maximo_mb": 30,
        "duracao_min_s": 1, "duracao_max_s": 60,
        "safe_zone_larg": 1080, "safe_zone_alt": 1420,
        "overlay_texto": "Manter texto e elementos fora dos 250px superiores e inferiores (safe zone)",
        "codec": "H.264",
        "extensoes": ["jpg", "png", "mp4", "mov"],
        "prioridade": "obrigatorio",
        "obs": "Stories: até 15s por card. Reels: até 90s. Safe zone: 250px top e bottom reservados para UI.",
    },
    {
        "plataforma": "Meta",
        "formato": "Carrossel (por card)",
        "tipo": "imagem",
        "tags": ["carrossel", "meta"],
        "largura_px": 1080, "altura_px": 1080, "ratio": "1:1",
        "peso_maximo_mb": 30,
        "duracao_min_s": None, "duracao_max_s": None,
        "safe_zone_larg": None, "safe_zone_alt": None,
        "overlay_texto": "Sem limite oficial — manter consistência visual entre cards",
        "codec": None,
        "extensoes": ["jpg", "png"],
        "prioridade": "recomendado",
        "obs": "Mínimo 2 cards, máximo 10. Cada card é independente. Último card pode ser CTA.",
    },
    # ── GOOGLE DISPLAY ────────────────────────────────────────────────────────
    {
        "plataforma": "Google Display",
        "formato": "Medium Rectangle 300×250",
        "tipo": "imagem",
        "tags": ["display", "google"],
        "largura_px": 300, "altura_px": 250, "ratio": "6:5",
        "peso_maximo_mb": 0.15,
        "duracao_min_s": None, "duracao_max_s": None,
        "safe_zone_larg": None, "safe_zone_alt": None,
        "overlay_texto": "Logo e CTA devem ser visíveis dentro dos 300×250px",
        "codec": None,
        "extensoes": ["jpg", "png", "gif", "html5"],
        "prioridade": "obrigatorio",
        "obs": "Formato mais utilizado na Rede de Display. Maior cobertura de inventário.",
    },
    {
        "plataforma": "Google Display",
        "formato": "Leaderboard 728×90",
        "tipo": "imagem",
        "tags": ["display", "google"],
        "largura_px": 728, "altura_px": 90, "ratio": "728:90",
        "peso_maximo_mb": 0.15,
        "duracao_min_s": None, "duracao_max_s": None,
        "safe_zone_larg": None, "safe_zone_alt": None,
        "overlay_texto": "Banner horizontal — texto deve ser legível em altura de 90px",
        "codec": None,
        "extensoes": ["jpg", "png", "gif", "html5"],
        "prioridade": "obrigatorio",
        "obs": "Aparece no topo de páginas desktop. Alto impacto de visibilidade.",
    },
    {
        "plataforma": "Google Display",
        "formato": "Wide Skyscraper 160×600",
        "tipo": "imagem",
        "tags": ["display", "google"],
        "largura_px": 160, "altura_px": 600, "ratio": "4:15",
        "peso_maximo_mb": 0.15,
        "duracao_min_s": None, "duracao_max_s": None,
        "safe_zone_larg": None, "safe_zone_alt": None,
        "overlay_texto": "Banner vertical — usar elementos empilhados verticalmente",
        "codec": None,
        "extensoes": ["jpg", "png", "gif", "html5"],
        "prioridade": "recomendado",
        "obs": "Aparece nas laterais de páginas. Bom para storytelling visual vertical.",
    },
    {
        "plataforma": "Google Display",
        "formato": "Half Page 300×600",
        "tipo": "imagem",
        "tags": ["display", "google"],
        "largura_px": 300, "altura_px": 600, "ratio": "1:2",
        "peso_maximo_mb": 0.15,
        "duracao_min_s": None, "duracao_max_s": None,
        "safe_zone_larg": None, "safe_zone_alt": None,
        "overlay_texto": "Alta visibilidade — espaço suficiente para hierarquia completa de informação",
        "codec": None,
        "extensoes": ["jpg", "png", "gif", "html5"],
        "prioridade": "recomendado",
        "obs": "Alto impacto visual. Um dos formatos premium da Rede de Display.",
    },
    {
        "plataforma": "Google Display",
        "formato": "Billboard 970×250",
        "tipo": "imagem",
        "tags": ["display", "google"],
        "largura_px": 970, "altura_px": 250, "ratio": "97:25",
        "peso_maximo_mb": 0.15,
        "duracao_min_s": None, "duracao_max_s": None,
        "safe_zone_larg": None, "safe_zone_alt": None,
        "overlay_texto": "Amplo espaço horizontal — ideal para mensagem única e impactante",
        "codec": None,
        "extensoes": ["jpg", "png", "gif", "html5"],
        "prioridade": "opcional",
        "obs": "Formato premium desktop. Inventário mais limitado.",
    },
    # ── GOOGLE PMAX ───────────────────────────────────────────────────────────
    {
        "plataforma": "Google PMax",
        "formato": "Landscape 1.91:1",
        "tipo": "imagem",
        "tags": ["pmax", "google"],
        "largura_px": 1200, "altura_px": 628, "ratio": "1.91:1",
        "peso_maximo_mb": 5,
        "duracao_min_s": None, "duracao_max_s": None,
        "safe_zone_larg": None, "safe_zone_alt": None,
        "overlay_texto": "Google sobrepõe texto automaticamente — evitar texto na imagem",
        "codec": None,
        "extensoes": ["jpg", "png"],
        "prioridade": "obrigatorio",
        "obs": "Formato principal para campanhas PMax e Discovery. Usado em Gmail, YouTube e Display.",
    },
    {
        "plataforma": "Google PMax",
        "formato": "Square 1:1 (1200×1200)",
        "tipo": "imagem",
        "tags": ["pmax", "google"],
        "largura_px": 1200, "altura_px": 1200, "ratio": "1:1",
        "peso_maximo_mb": 5,
        "duracao_min_s": None, "duracao_max_s": None,
        "safe_zone_larg": None, "safe_zone_alt": None,
        "overlay_texto": "Google sobrepõe texto automaticamente — evitar texto na imagem",
        "codec": None,
        "extensoes": ["jpg", "png"],
        "prioridade": "obrigatorio",
        "obs": "Complementa o landscape. Obrigatório para coverage completa de placements.",
    },
    {
        "plataforma": "Google PMax",
        "formato": "Square mínimo 300×300",
        "tipo": "imagem",
        "tags": ["pmax", "google"],
        "largura_px": 300, "altura_px": 300, "ratio": "1:1",
        "peso_maximo_mb": 5,
        "duracao_min_s": None, "duracao_max_s": None,
        "safe_zone_larg": None, "safe_zone_alt": None,
        "overlay_texto": "Tamanho mínimo aceito — preferir 1200×1200px quando possível",
        "codec": None,
        "extensoes": ["jpg", "png"],
        "prioridade": "recomendado",
        "obs": "Aceito como substituto ao 1200×1200px se o asset original for menor.",
    },
    # ── YOUTUBE ───────────────────────────────────────────────────────────────
    {
        "plataforma": "YouTube",
        "formato": "Bumper Ad (6s)",
        "tipo": "video",
        "tags": ["bumper", "youtube"],
        "largura_px": 1920, "altura_px": 1080, "ratio": "16:9",
        "peso_maximo_mb": 1024,
        "duracao_min_s": 6, "duracao_max_s": 6,
        "safe_zone_larg": 1920, "safe_zone_alt": 880,
        "overlay_texto": "Manter elementos críticos fora dos 100px inferiores (botão Skip/UI)",
        "codec": "H.264",
        "extensoes": ["mp4", "mov", "avi"],
        "prioridade": "recomendado",
        "obs": "Exatamente 6 segundos — não pulável. Ideal para awareness e reforço de mensagem. CTA nos últimos 2s.",
    },
    {
        "plataforma": "YouTube",
        "formato": "Skippable In-stream (15-30s)",
        "tipo": "video",
        "tags": ["skippable", "youtube"],
        "largura_px": 1920, "altura_px": 1080, "ratio": "16:9",
        "peso_maximo_mb": 1024,
        "duracao_min_s": 12, "duracao_max_s": 60,
        "safe_zone_larg": 1920, "safe_zone_alt": 880,
        "overlay_texto": "Manter elementos críticos fora dos 100px inferiores (botão Skip/UI)",
        "codec": "H.264",
        "extensoes": ["mp4", "mov", "avi"],
        "prioridade": "obrigatorio",
        "obs": "Pulável após 5s. Mensagem principal e logo nos primeiros 5s. Recomendado: 15-30s. CTA verbal e visual antes dos 5s.",
    },
    {
        "plataforma": "YouTube",
        "formato": "Non-skippable In-stream (15s)",
        "tipo": "video",
        "tags": ["non-skippable", "nonskippable", "youtube"],
        "largura_px": 1920, "altura_px": 1080, "ratio": "16:9",
        "peso_maximo_mb": 1024,
        "duracao_min_s": 15, "duracao_max_s": 15,
        "safe_zone_larg": 1920, "safe_zone_alt": 880,
        "overlay_texto": "Manter elementos críticos fora dos 100px inferiores",
        "codec": "H.264",
        "extensoes": ["mp4", "mov", "avi"],
        "prioridade": "opcional",
        "obs": "Exatamente 15s — não pulável. Atenção total garantida. CTA no final. Alguns mercados aceitam até 20s.",
    },
    # ── LINKEDIN ──────────────────────────────────────────────────────────────
    {
        "plataforma": "LinkedIn",
        "formato": "Feed Imagem 1.91:1",
        "tipo": "imagem",
        "tags": ["feed", "linkedin"],
        "largura_px": 1200, "altura_px": 628, "ratio": "1.91:1",
        "peso_maximo_mb": 5,
        "duracao_min_s": None, "duracao_max_s": None,
        "safe_zone_larg": None, "safe_zone_alt": None,
        "overlay_texto": "Texto no anúncio acima da imagem — imagem deve complementar, não repetir o texto",
        "codec": None,
        "extensoes": ["jpg", "png"],
        "prioridade": "obrigatorio",
        "obs": "Formato principal de Sponsored Content no LinkedIn. Ideal para B2B.",
    },
    {
        "plataforma": "LinkedIn",
        "formato": "Feed Imagem 1:1",
        "tipo": "imagem",
        "tags": ["feed", "linkedin"],
        "largura_px": 1200, "altura_px": 1200, "ratio": "1:1",
        "peso_maximo_mb": 5,
        "duracao_min_s": None, "duracao_max_s": None,
        "safe_zone_larg": None, "safe_zone_alt": None,
        "overlay_texto": "Formato quadrado — maior visibilidade no mobile",
        "codec": None,
        "extensoes": ["jpg", "png"],
        "prioridade": "recomendado",
        "obs": "Melhor desempenho no feed mobile LinkedIn.",
    },
    {
        "plataforma": "LinkedIn",
        "formato": "Stories 9:16",
        "tipo": "imagem_ou_video",
        "tags": ["stories", "linkedin"],
        "largura_px": 1080, "altura_px": 1920, "ratio": "9:16",
        "peso_maximo_mb": 200,
        "duracao_min_s": 3, "duracao_max_s": 20,
        "safe_zone_larg": 1080, "safe_zone_alt": 1420,
        "overlay_texto": "Safe zone: 250px top e bottom reservados para UI",
        "codec": "H.264",
        "extensoes": ["jpg", "png", "mp4"],
        "prioridade": "opcional",
        "obs": "LinkedIn Stories disponível apenas em mobile. Menor alcance vs. feed.",
    },
    # ── TIKTOK ────────────────────────────────────────────────────────────────
    {
        "plataforma": "TikTok",
        "formato": "In-Feed Video 9:16",
        "tipo": "video",
        "tags": ["feed", "tiktok"],
        "largura_px": 1080, "altura_px": 1920, "ratio": "9:16",
        "peso_maximo_mb": 500,
        "duracao_min_s": 5, "duracao_max_s": 60,
        "safe_zone_larg": 1080, "safe_zone_alt": 1420,
        "overlay_texto": "Safe zone: 250px top e bottom. Texto nativo do TikTok sobrepõe na base.",
        "codec": "H.264 ou H.265",
        "extensoes": ["mp4", "mov"],
        "prioridade": "obrigatorio",
        "obs": "Formato principal TikTok Ads. Recomendado: 15-30s. Audio é fundamental — 80% dos usuários assistem com som.",
    },
    {
        "plataforma": "TikTok",
        "formato": "In-Feed Video 1:1",
        "tipo": "video",
        "tags": ["feed", "tiktok"],
        "largura_px": 1080, "altura_px": 1080, "ratio": "1:1",
        "peso_maximo_mb": 500,
        "duracao_min_s": 5, "duracao_max_s": 60,
        "safe_zone_larg": None, "safe_zone_alt": None,
        "overlay_texto": "Formato quadrado — menos imersivo que 9:16 no TikTok",
        "codec": "H.264 ou H.265",
        "extensoes": ["mp4", "mov"],
        "prioridade": "opcional",
        "obs": "Alternativa ao 9:16 quando o asset nativo for quadrado. Performance tipicamente menor.",
    },
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def _slug(texto: str) -> str:
    """Converte texto para slug simples."""
    import re
    s = texto.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _naming_convention(spec: dict, n_variantes: int) -> list:
    """Gera lista de nomes de arquivo para N variantes."""
    plat = _slug(spec["plataforma"])
    fmt = _slug(spec["formato"])[:20]
    ext = spec["extensoes"][0]
    return [f"{{slug}}-{plat}-{fmt}-v{i}.{ext}" for i in range(1, n_variantes + 1)]


def _duracao_str(spec: dict) -> str:
    """Formata campo de duração."""
    lo, hi = spec["duracao_min_s"], spec["duracao_max_s"]
    if lo is None:
        return "-"
    if lo == hi:
        return f"{lo}s (fixo)"
    return f"{lo}–{hi}s"


def _safe_zone_str(spec: dict) -> str:
    """Formata campo de safe zone."""
    lw, lh = spec["safe_zone_larg"], spec["safe_zone_alt"]
    if lw is None:
        return "-"
    return f"{lw}×{lh}px"


def _peso_str(spec: dict) -> str:
    mb = spec["peso_maximo_mb"]
    if mb < 1:
        return f"{int(mb * 1000)} KB"
    if mb >= 1000:
        return f"{int(mb / 1024)} GB"
    return f"{int(mb)} MB"


# ── Filtros ────────────────────────────────────────────────────────────────────

def _filtrar(specs: list, platforms: list, formats: list) -> list:
    result = specs

    if platforms:
        plat_norm = [p.strip().lower() for p in platforms]
        result = [s for s in result if any(t in s["tags"] for t in plat_norm)]

    if formats:
        fmt_norm = [f.strip().lower() for f in formats]
        result = [s for s in result if any(t in s["tags"] for t in fmt_norm)]

    return result


# ── Formatadores de Output ─────────────────────────────────────────────────────

def _output_json(specs: list, n_variantes: int) -> str:
    saida = []
    for s in specs:
        entry = {k: v for k, v in s.items()}
        entry["dimensoes_px"] = f"{s['largura_px']}×{s['altura_px']}px"
        entry["peso_maximo"] = _peso_str(s)
        entry["duracao"] = _duracao_str(s)
        entry["safe_zone"] = _safe_zone_str(s)
        entry["naming_convention"] = _naming_convention(s, n_variantes)
        # remove campos internos renomeados
        for k in ["largura_px", "altura_px"]:
            entry.pop(k, None)
        saida.append(entry)
    return json.dumps(saida, ensure_ascii=False, indent=2)


def _output_table(specs: list, n_variantes: int) -> str:
    cols = [
        ("Plataforma",   "plataforma",    24),
        ("Formato",      "formato",       30),
        ("Dimensões",    "_dim",          16),
        ("Ratio",        "ratio",         9),
        ("Peso Máx",     "_peso",         10),
        ("Duração",      "_dur",          13),
        ("Safe Zone",    "_safe",         16),
        ("Tipo",         "tipo",          18),
    ]

    def cell(spec, key, width):
        if key == "_dim":
            v = f"{spec['largura_px']}×{spec['altura_px']}px"
        elif key == "_peso":
            v = _peso_str(spec)
        elif key == "_dur":
            v = _duracao_str(spec)
        elif key == "_safe":
            v = _safe_zone_str(spec)
        else:
            v = str(spec.get(key, "-"))
        return v[:width].ljust(width)

    sep = "+" + "+".join("-" * (w + 2) for _, _, w in cols) + "+"
    header = "|" + "|".join(f" {name.ljust(w)} " for name, _, w in cols) + "|"

    linhas = [sep, header, sep]
    for spec in specs:
        row = "|" + "|".join(f" {cell(spec, key, w)} " for _, key, w in cols) + "|"
        linhas.append(row)
    linhas.append(sep)

    if n_variantes > 0:
        linhas.append("")
        linhas.append("Nomenclatura de Variantes:")
        linhas.append("-" * 60)
        for spec in specs:
            plat = spec["plataforma"]
            fmt = spec["formato"]
            nomes = _naming_convention(spec, n_variantes)
            linhas.append(f"  {plat} — {fmt}:")
            for nome in nomes:
                linhas.append(f"    {nome}")

    return "\n".join(linhas)


def _output_checklist(specs: list, n_variantes: int) -> str:
    blocos = []
    for spec in specs:
        titulo = f"## {spec['plataforma']} — {spec['formato']}"
        tipo_str = {"imagem": "Imagem", "video": "Vídeo", "imagem_ou_video": "Imagem ou Vídeo"}[spec["tipo"]]

        obrig = []
        obrig.append(f"- [ ] Dimensões: {spec['largura_px']}×{spec['altura_px']}px (ratio {spec['ratio']})")
        obrig.append(f"- [ ] Tipo de asset: {tipo_str}")
        obrig.append(f"- [ ] Peso máximo: {_peso_str(spec)}")
        obrig.append(f"- [ ] Extensões aceitas: {', '.join(e.upper() for e in spec['extensoes'])}")
        if spec["duracao_min_s"] is not None:
            obrig.append(f"- [ ] Duração: {_duracao_str(spec)}")
        if spec["codec"]:
            obrig.append(f"- [ ] Codec: {spec['codec']}")

        recom = []
        if spec["safe_zone_larg"]:
            recom.append(f"- [ ] Safe zone: {_safe_zone_str(spec)} — manter elementos críticos dentro desta área")
        recom.append(f"- [ ] Texto no overlay: {spec['overlay_texto']}")
        if spec["obs"]:
            recom.append(f"- [ ] Atenção: {spec['obs']}")

        bloco = [titulo, ""]
        bloco += ["**Obrigatório**"] + obrig + [""]
        bloco += ["**Recomendado**"] + recom + [""]

        if n_variantes > 0:
            nomes = _naming_convention(spec, n_variantes)
            bloco += ["**Nomenclatura de Variantes**"]
            for nome in nomes:
                bloco.append(f"- `{nome}`")
            bloco.append("")

        bloco.append("---")
        blocos.append("\n".join(bloco))

    return "\n".join(blocos)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Gerador de especificações técnicas de assets para mídia paga.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  python3 gerador-specs.py --platforms meta --formats feed,stories --variants 3\n"
            "  python3 gerador-specs.py --platforms youtube --formats bumper,skippable --output-format checklist\n"
            "  python3 gerador-specs.py --platforms meta,google,youtube --output-format table\n"
            "  python3 gerador-specs.py --list-platforms\n"
        ),
    )
    parser.add_argument(
        "--platforms",
        help="Plataformas separadas por vírgula: meta, google, youtube, linkedin, tiktok",
    )
    parser.add_argument(
        "--formats",
        help=(
            "Formatos separados por vírgula: feed, stories, reels, carrossel, "
            "display, pmax, bumper, skippable, non-skippable, linkedin, tiktok"
        ),
    )
    parser.add_argument(
        "--variants", type=int, default=0, metavar="N",
        help="Número de variantes criativas para gerar nomenclatura (ex: 3 → v1, v2, v3)",
    )
    parser.add_argument(
        "--output-format", choices=["json", "table", "checklist"], default="json",
        help="Formato de saída: json (padrão) | table | checklist",
    )
    parser.add_argument(
        "--list-platforms", action="store_true",
        help="Lista todas as plataformas e formatos disponíveis no banco de dados",
    )
    args = parser.parse_args()

    if args.list_platforms:
        plataformas: dict = {}
        for s in SPECS_DB:
            p = s["plataforma"]
            if p not in plataformas:
                plataformas[p] = []
            plataformas[p].append(s["formato"])
        print(json.dumps(plataformas, ensure_ascii=False, indent=2))
        return

    platforms = [p.strip() for p in args.platforms.split(",")] if args.platforms else []
    formats = [f.strip() for f in args.formats.split(",")] if args.formats else []

    specs = _filtrar(SPECS_DB, platforms, formats)

    if not specs:
        print(json.dumps({
            "status": "vazio",
            "mensagem": "Nenhum formato encontrado para a combinação de plataformas/formatos informada.",
            "plataformas_disponiveis": sorted({s["plataforma"] for s in SPECS_DB}),
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    n = args.variants
    fmt = args.output_format

    if fmt == "json":
        print(_output_json(specs, n))
    elif fmt == "table":
        print(_output_table(specs, n))
    elif fmt == "checklist":
        print(_output_checklist(specs, n))


if __name__ == "__main__":
    main()
