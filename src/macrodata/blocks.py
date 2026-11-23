"""Mapa variável -> bloco temático para codebook e exportação."""
from __future__ import annotations

BLOCK_MAP: dict[str, str] = {
    # distribuição e classe
    "profit_share": "distribuicao",
    "gini_index": "distribuicao",
    "income_share_top10": "distribuicao",
    "income_share_bottom20": "distribuicao",
    "vulnerable_employment_pct": "distribuicao",
    "wage_bill_gdp": "distribuicao",
    # restrição externa e hierarquia monetária
    "terms_of_trade_index": "restricao_externa",
    "intl_reserves_usd": "restricao_externa",
    "intl_reserves_months_imports": "restricao_externa",
    "external_debt_gni": "restricao_externa",
    "debt_service_exports": "restricao_externa",
    "fdi_net_inflows_gdp": "restricao_externa",
    # financiarização e crédito
    "lending_rate": "financeiro",
    "interest_rate_spread": "financeiro",
    "bank_capital_to_assets": "financeiro",
    "bank_npl_pct": "financeiro",
    "market_cap_gdp": "financeiro",
    # ecologia e estrutura produtiva
    "co2_per_capita": "ecologia_estrutura",
    "co2_per_gdp": "ecologia_estrutura",
    "renewable_electricity_pct": "ecologia_estrutura",
    "energy_intensity_gdp": "ecologia_estrutura",
    "manufacturing_gdp": "ecologia_estrutura",
    "agriculture_gdp": "ecologia_estrutura",
    "manufactures_exports_pct": "ecologia_estrutura",
    "fuel_ores_exports_pct": "ecologia_estrutura",
}

BLOCK_LABELS = {
    "macro_core": "Macro core (ortodoxo)",
    "distribuicao": "Distribuição e classe",
    "restricao_externa": "Restrição externa e hierarquia monetária",
    "financeiro": "Financiarização e crédito",
    "ecologia_estrutura": "Ecologia e estrutura produtiva",
}


def block_of(variable: str) -> str:
    return BLOCK_MAP.get(variable, "macro_core")
