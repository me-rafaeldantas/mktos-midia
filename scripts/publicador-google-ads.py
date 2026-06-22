#!/usr/bin/env python3
"""
publicador-google-ads.py
=======================
Publicação de campanhas no Google Ads via API para mktOS Mídia.

Cria campanhas, ad groups, keywords e RSAs de forma individual ou em batch
a partir de um JSON de estrutura completa. Todas as campanhas são criadas
com status PAUSED por padrão — ativação manual obrigatória.

Autenticação: ~/google-ads.yaml (mesmo arquivo do MCP google-ads)

Uso:
    # Criar campanha individual
    python publicador-google-ads.py --action create-campaign --account 1234567890 \
        --data '{"name":"Google - Search - Marca","type":"SEARCH","budget_amount_micros":50000000}'

    # Criar ad group
    python publicador-google-ads.py --action create-adgroup --account 1234567890 \
        --campaign-id 111222333 \
        --data '{"name":"Marca - Exato","cpc_bid_micros":2000000,"keywords":[{"text":"minha marca","match_type":"EXACT"}]}'

    # Criar RSA
    python publicador-google-ads.py --action create-rsa --account 1234567890 \
        --adgroup-id 444555666 \
        --data '{"headlines":["Headline 1","Headline 2","Headline 3"],"descriptions":["Descrição completa aqui.","Segunda descrição."],"final_url":"https://site.com"}'

    # Criar estrutura completa a partir de arquivo JSON
    python publicador-google-ads.py --action create-structure --account 1234567890 \
        --file estrutura-campanha.json

    # Validar RSA sem criar
    python publicador-google-ads.py --action validate-rsa \
        --data '{"headlines":[...],"descriptions":[...]}'
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

CLIENTES_DIR  = Path(__file__).parent.parent / "data" / "clientes"
REPORTS_DIR   = Path(__file__).parent.parent / "reports" / "publishes"

# Limites RSA (Google Ads specs)
RSA_MAX_HEADLINES    = 15
RSA_MIN_HEADLINES    = 3
RSA_MAX_HEADLINE_LEN = 30
RSA_MAX_DESCRIPTIONS = 4
RSA_MIN_DESCRIPTIONS = 2
RSA_MAX_DESC_LEN     = 90
RSA_MAX_PATH_LEN     = 15

# Tipos de campanha suportados
CAMPAIGN_TYPES = {"SEARCH", "DISPLAY", "PERFORMANCE_MAX", "VIDEO", "SHOPPING"}

# Match types para keywords
MATCH_TYPES = {"EXACT", "PHRASE", "BROAD"}


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

def _load_client():
    """Carrega GoogleAdsClient. Retorna (client, error)."""
    try:
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException
        client = GoogleAdsClient.load_from_storage()
        return client, None, GoogleAdsException
    except ImportError:
        return None, "google-ads library não instalada (pip install google-ads)", None
    except Exception as exc:
        return None, f"Falha ao carregar credenciais (~/google-ads.yaml): {exc}", None


def _account_id(raw):
    return str(raw).replace("-", "").strip()


def _log_result(action, account_id, data_in, result):
    """Grava log em reports/publishes/."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = REPORTS_DIR / f"google-ads-{ts}.json"
    log  = {
        "timestamp":  datetime.now().isoformat(),
        "action":     action,
        "account_id": account_id,
        "input":      data_in,
        "result":     result,
    }
    path.write_text(json.dumps(log, ensure_ascii=False, indent=2))
    return str(path)


def _check_budget(account_slug, budget_micros):
    """Verifica budget contra perfil.json. Retorna (ok, warning_msg)."""
    if not account_slug:
        return True, None
    perfil_path = CLIENTES_DIR / account_slug / "perfil.json"
    if not perfil_path.exists():
        return True, None
    try:
        perfil = json.loads(perfil_path.read_text(encoding="utf-8"))
        orcamento = perfil.get("orcamento_mensal", 0)
        if orcamento and budget_micros:
            budget_brl = budget_micros / 1_000_000
            if budget_brl > orcamento * 0.5:
                return False, (
                    f"Budget diário de R$ {budget_brl:,.2f} representa mais de 50% do "
                    f"orçamento mensal cadastrado (R$ {orcamento:,.2f}). Confirme antes de criar."
                )
    except (json.JSONDecodeError, OSError):
        pass
    return True, None


# ---------------------------------------------------------------------------
# Validação RSA
# ---------------------------------------------------------------------------

def validate_rsa_data(data):
    """Valida dados de RSA. Retorna lista de erros (vazia = ok)."""
    errors = []
    headlines    = data.get("headlines", [])
    descriptions = data.get("descriptions", [])
    final_url    = data.get("final_url", "")
    path1        = data.get("path1", "")
    path2        = data.get("path2", "")

    if len(headlines) < RSA_MIN_HEADLINES:
        errors.append(f"RSA exige mínimo {RSA_MIN_HEADLINES} headlines — fornecidos: {len(headlines)}")
    if len(headlines) > RSA_MAX_HEADLINES:
        errors.append(f"RSA aceita no máximo {RSA_MAX_HEADLINES} headlines — fornecidos: {len(headlines)}")

    for i, h in enumerate(headlines):
        if len(h) > RSA_MAX_HEADLINE_LEN:
            errors.append(
                f"Headline {i+1} tem {len(h)} chars (máx {RSA_MAX_HEADLINE_LEN}): '{h[:35]}...'"
            )

    if len(descriptions) < RSA_MIN_DESCRIPTIONS:
        errors.append(f"RSA exige mínimo {RSA_MIN_DESCRIPTIONS} descriptions — fornecidas: {len(descriptions)}")
    if len(descriptions) > RSA_MAX_DESCRIPTIONS:
        errors.append(f"RSA aceita no máximo {RSA_MAX_DESCRIPTIONS} descriptions — fornecidas: {len(descriptions)}")

    for i, d in enumerate(descriptions):
        if len(d) > RSA_MAX_DESC_LEN:
            errors.append(
                f"Description {i+1} tem {len(d)} chars (máx {RSA_MAX_DESC_LEN}): '{d[:50]}...'"
            )

    if not final_url:
        errors.append("final_url é obrigatória")
    elif not final_url.startswith(("http://", "https://")):
        errors.append(f"final_url inválida: '{final_url}' — deve começar com http:// ou https://")

    if path1 and len(path1) > RSA_MAX_PATH_LEN:
        errors.append(f"path1 tem {len(path1)} chars (máx {RSA_MAX_PATH_LEN})")
    if path2 and len(path2) > RSA_MAX_PATH_LEN:
        errors.append(f"path2 tem {len(path2)} chars (máx {RSA_MAX_PATH_LEN})")

    return errors


# ---------------------------------------------------------------------------
# Ações de criação
# ---------------------------------------------------------------------------

def create_campaign(client, GoogleAdsException, account, data, slug=""):
    """Cria campanha + budget. Retorna dict com campaign_id e budget_id."""
    name          = data.get("name", "Campanha sem nome")
    campaign_type = data.get("type", "SEARCH").upper()
    budget_micros = data.get("budget_amount_micros", 10_000_000)
    start_date    = data.get("start_date", "")
    end_date      = data.get("end_date", "")

    if campaign_type not in CAMPAIGN_TYPES:
        return {"status": "error", "reason": f"Tipo inválido: '{campaign_type}'. Use: {CAMPAIGN_TYPES}"}

    # Verificação de budget
    ok, warn = _check_budget(slug, budget_micros)
    if not ok:
        return {"status": "error", "reason": warn}

    customer_id = _account_id(account)

    try:
        # 1. Criar budget
        budget_service  = client.get_service("CampaignBudgetService")
        budget_op       = client.get_type("CampaignBudgetOperation")
        budget          = budget_op.create
        budget.name     = f"Budget - {name}"
        budget.amount_micros           = budget_micros
        budget.delivery_method         = client.enums.BudgetDeliveryMethodEnum.STANDARD
        budget.explicitly_shared       = False

        budget_response  = budget_service.mutate_campaign_budgets(
            customer_id=customer_id, operations=[budget_op]
        )
        budget_resource  = budget_response.results[0].resource_name

        # 2. Criar campanha
        campaign_service = client.get_service("CampaignService")
        campaign_op      = client.get_type("CampaignOperation")
        campaign         = campaign_op.create
        campaign.name    = name
        campaign.status  = client.enums.CampaignStatusEnum.PAUSED  # sempre PAUSED
        campaign.campaign_budget = budget_resource

        adv_channel_map = {
            "SEARCH":          client.enums.AdvertisingChannelTypeEnum.SEARCH,
            "DISPLAY":         client.enums.AdvertisingChannelTypeEnum.DISPLAY,
            "PERFORMANCE_MAX": client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX,
            "VIDEO":           client.enums.AdvertisingChannelTypeEnum.VIDEO,
            "SHOPPING":        client.enums.AdvertisingChannelTypeEnum.SHOPPING,
        }
        campaign.advertising_channel_type = adv_channel_map[campaign_type]

        if start_date:
            campaign.start_date = start_date
        if end_date:
            campaign.end_date = end_date

        # Configurações de bidding padrão
        if campaign_type == "SEARCH":
            campaign.manual_cpc.enhanced_cpc_enabled = False
        elif campaign_type == "DISPLAY":
            campaign.target_cpa.target_cpa_micros = data.get("target_cpa_micros", 0) or 0

        campaign_response = campaign_service.mutate_campaigns(
            customer_id=customer_id, operations=[campaign_op]
        )
        campaign_resource = campaign_response.results[0].resource_name
        campaign_id       = campaign_resource.split("/")[-1]

        return {
            "status":            "ok",
            "campaign_id":       campaign_id,
            "campaign_resource": campaign_resource,
            "budget_resource":   budget_resource,
            "name":              name,
            "type":              campaign_type,
            "status_created":    "PAUSED",
            "note":              "Campanha criada com status PAUSED. Ative manualmente após revisão.",
        }

    except GoogleAdsException as exc:
        errors = [str(e.message) for e in exc.failure.errors]
        return {"status": "error", "reason": f"Google Ads API: {'; '.join(errors)}"}
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}


def create_adgroup(client, GoogleAdsException, account, campaign_id, data):
    """Cria ad group e keywords."""
    customer_id   = _account_id(account)
    name          = data.get("name", "Grupo sem nome")
    cpc_bid       = data.get("cpc_bid_micros", 1_000_000)
    keywords      = data.get("keywords", [])

    campaign_resource = f"customers/{customer_id}/campaigns/{campaign_id}"

    try:
        # Ad group
        ag_service  = client.get_service("AdGroupService")
        ag_op       = client.get_type("AdGroupOperation")
        ag          = ag_op.create
        ag.name     = name
        ag.campaign = campaign_resource
        ag.status   = client.enums.AdGroupStatusEnum.ENABLED
        ag.type_    = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
        ag.cpc_bid_micros = cpc_bid

        ag_response   = ag_service.mutate_ad_groups(
            customer_id=customer_id, operations=[ag_op]
        )
        ag_resource   = ag_response.results[0].resource_name
        adgroup_id    = ag_resource.split("/")[-1]

        # Keywords
        kw_results = []
        if keywords:
            kw_service = client.get_service("AdGroupCriterionService")
            kw_ops     = []
            for kw in keywords:
                text       = kw.get("text", "")
                match_raw  = kw.get("match_type", "BROAD").upper()
                match_type = match_raw if match_raw in MATCH_TYPES else "BROAD"
                if not text:
                    continue
                kw_op     = client.get_type("AdGroupCriterionOperation")
                criterion = kw_op.create
                criterion.ad_group = ag_resource
                criterion.status   = client.enums.AdGroupCriterionStatusEnum.ENABLED
                criterion.keyword.text       = text
                criterion.keyword.match_type = getattr(
                    client.enums.KeywordMatchTypeEnum, match_type
                )
                kw_ops.append(kw_op)

            if kw_ops:
                kw_response = kw_service.mutate_ad_group_criteria(
                    customer_id=customer_id, operations=kw_ops
                )
                kw_results = [r.resource_name for r in kw_response.results]

        return {
            "status":           "ok",
            "adgroup_id":       adgroup_id,
            "adgroup_resource": ag_resource,
            "name":             name,
            "keywords_created": len(kw_results),
            "keyword_resources": kw_results,
        }

    except GoogleAdsException as exc:
        errors = [str(e.message) for e in exc.failure.errors]
        return {"status": "error", "reason": f"Google Ads API: {'; '.join(errors)}"}
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}


def create_rsa(client, GoogleAdsException, account, adgroup_id, data):
    """Cria Responsive Search Ad com validação completa."""
    errors = validate_rsa_data(data)
    if errors:
        return {"status": "error", "reason": "Validação RSA falhou", "errors": errors}

    customer_id    = _account_id(account)
    headlines      = data["headlines"]
    descriptions   = data["descriptions"]
    final_url      = data["final_url"]
    path1          = data.get("path1", "")
    path2          = data.get("path2", "")

    ag_resource    = f"customers/{customer_id}/ad_groups/{adgroup_id}"

    try:
        ad_service  = client.get_service("AdGroupAdService")
        ad_op       = client.get_type("AdGroupAdOperation")
        ad_group_ad = ad_op.create
        ad_group_ad.ad_group = ag_resource
        ad_group_ad.status   = client.enums.AdGroupAdStatusEnum.ENABLED

        rsa = ad_group_ad.ad.responsive_search_ad
        for h in headlines:
            asset = client.get_type("AdTextAsset")
            asset.text = h
            rsa.headlines.append(asset)
        for d in descriptions:
            asset = client.get_type("AdTextAsset")
            asset.text = d
            rsa.descriptions.append(asset)
        if path1:
            rsa.path1 = path1
        if path2:
            rsa.path2 = path2

        ad_group_ad.ad.final_urls.append(final_url)

        response = ad_service.mutate_ad_group_ads(
            customer_id=customer_id, operations=[ad_op]
        )
        ad_resource = response.results[0].resource_name
        ad_id       = ad_resource.split("/")[-1]

        return {
            "status":       "ok",
            "ad_id":        ad_id,
            "ad_resource":  ad_resource,
            "headlines":    len(headlines),
            "descriptions": len(descriptions),
            "final_url":    final_url,
        }

    except GoogleAdsException as exc:
        errors_list = [str(e.message) for e in exc.failure.errors]
        return {"status": "error", "reason": f"Google Ads API: {'; '.join(errors_list)}"}
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}


def create_structure(client, GoogleAdsException, account, structure, slug=""):
    """
    Cria estrutura completa: campanha → ad groups → keywords → RSAs.

    Formato do JSON de estrutura:
    {
      "campaign": { <dados da campanha> },
      "adgroups": [
        {
          "adgroup": { <dados do ad group + keywords> },
          "ads": [ { "rsa": { <dados RSA> } } ]
        }
      ]
    }
    """
    results = {
        "status":   "ok",
        "campaign": None,
        "adgroups": [],
        "errors":   [],
    }

    # 1. Criar campanha
    camp_data   = structure.get("campaign", {})
    camp_result = create_campaign(client, GoogleAdsException, account, camp_data, slug=slug)
    results["campaign"] = camp_result

    if camp_result.get("status") != "ok":
        results["status"] = "error"
        results["errors"].append(f"Campanha: {camp_result.get('reason')}")
        return results

    campaign_id = camp_result["campaign_id"]

    # 2. Ad groups
    for ag_block in structure.get("adgroups", []):
        ag_data   = ag_block.get("adgroup", {})
        ag_result = create_adgroup(client, GoogleAdsException, account, campaign_id, ag_data)
        ag_entry  = {"adgroup": ag_result, "ads": []}

        if ag_result.get("status") != "ok":
            results["errors"].append(f"Ad group '{ag_data.get('name')}': {ag_result.get('reason')}")
            results["adgroups"].append(ag_entry)
            continue

        adgroup_id = ag_result["adgroup_id"]

        # 3. Ads (RSA)
        for ad_block in ag_block.get("ads", []):
            if "rsa" in ad_block:
                ad_result = create_rsa(
                    client, GoogleAdsException, account, adgroup_id, ad_block["rsa"]
                )
                ag_entry["ads"].append({"type": "rsa", "result": ad_result})
                if ad_result.get("status") != "ok":
                    results["errors"].append(
                        f"RSA em '{ag_data.get('name')}': {ad_result.get('reason')}"
                    )

        results["adgroups"].append(ag_entry)

    if results["errors"]:
        results["status"] = "partial"

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Publicação de campanhas no Google Ads para mktOS Mídia"
    )
    parser.add_argument(
        "--action", required=True,
        choices=["create-campaign", "create-adgroup", "create-rsa",
                 "create-structure", "validate-rsa"],
        help="Ação a executar"
    )
    parser.add_argument("--account",     default="", help="ID da conta Google Ads")
    parser.add_argument("--campaign-id", default="", help="ID da campanha (para create-adgroup)")
    parser.add_argument("--adgroup-id",  default="", help="ID do ad group (para create-rsa)")
    parser.add_argument("--slug",        default="", help="Slug do cliente (para validação de orçamento)")
    parser.add_argument("--data",        default="", help="JSON com dados do recurso a criar")
    parser.add_argument("--file",        default="", help="Caminho do JSON de estrutura (para create-structure)")

    args = parser.parse_args()

    # Validar RSA não precisa de API
    if args.action == "validate-rsa":
        if not args.data:
            print(json.dumps({"status": "error", "reason": "Informe --data com JSON do RSA"}, ensure_ascii=False))
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(json.dumps({"status": "error", "reason": f"JSON inválido: {e}"}, ensure_ascii=False))
            sys.exit(1)
        errors = validate_rsa_data(data)
        if errors:
            result = {"status": "invalid", "errors": errors, "headlines": len(data.get("headlines", [])),
                      "descriptions": len(data.get("descriptions", []))}
        else:
            result = {"status": "valid", "headlines": len(data.get("headlines", [])),
                      "descriptions": len(data.get("descriptions", [])),
                      "note": "RSA válido — pronto para criação"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # Ações que precisam de API
    client, err, GoogleAdsException = _load_client()
    if err:
        print(json.dumps({"status": "error", "reason": err}, ensure_ascii=False, indent=2))
        sys.exit(1)

    if args.action == "create-campaign":
        if not args.data:
            print(json.dumps({"status": "error", "reason": "Informe --data com JSON da campanha"}, ensure_ascii=False))
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(json.dumps({"status": "error", "reason": f"JSON inválido: {e}"}, ensure_ascii=False))
            sys.exit(1)
        result = create_campaign(client, GoogleAdsException, args.account, data, slug=args.slug)

    elif args.action == "create-adgroup":
        if not args.campaign_id:
            print(json.dumps({"status": "error", "reason": "Informe --campaign-id"}, ensure_ascii=False))
            sys.exit(1)
        try:
            data = json.loads(args.data or "{}")
        except json.JSONDecodeError as e:
            print(json.dumps({"status": "error", "reason": f"JSON inválido: {e}"}, ensure_ascii=False))
            sys.exit(1)
        result = create_adgroup(client, GoogleAdsException, args.account, args.campaign_id, data)

    elif args.action == "create-rsa":
        if not args.adgroup_id:
            print(json.dumps({"status": "error", "reason": "Informe --adgroup-id"}, ensure_ascii=False))
            sys.exit(1)
        try:
            data = json.loads(args.data or "{}")
        except json.JSONDecodeError as e:
            print(json.dumps({"status": "error", "reason": f"JSON inválido: {e}"}, ensure_ascii=False))
            sys.exit(1)
        result = create_rsa(client, GoogleAdsException, args.account, args.adgroup_id, data)

    elif args.action == "create-structure":
        if args.file:
            path = Path(args.file).expanduser()
            if not path.exists():
                print(json.dumps({"status": "error", "reason": f"Arquivo não encontrado: {args.file}"}, ensure_ascii=False))
                sys.exit(1)
            try:
                structure = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                print(json.dumps({"status": "error", "reason": f"JSON inválido: {e}"}, ensure_ascii=False))
                sys.exit(1)
        elif args.data:
            try:
                structure = json.loads(args.data)
            except json.JSONDecodeError as e:
                print(json.dumps({"status": "error", "reason": f"JSON inválido: {e}"}, ensure_ascii=False))
                sys.exit(1)
        else:
            print(json.dumps({"status": "error", "reason": "Informe --file ou --data para create-structure"}, ensure_ascii=False))
            sys.exit(1)
        result = create_structure(client, GoogleAdsException, args.account, structure, slug=args.slug)

    # Log e output
    log_path = _log_result(args.action, args.account, args.data or args.file, result)
    result["log"] = log_path
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
