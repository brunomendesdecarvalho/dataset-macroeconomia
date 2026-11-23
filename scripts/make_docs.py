"""Gera os documentos com tabelas a partir dos dados processados."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from macrodata import settings  # noqa: E402


def md(df: pd.DataFrame, cols: list[str] | None = None, max_rows: int | None = None) -> str:
    if cols:
        df = df[cols]
    if max_rows:
        df = df.head(max_rows)
    df = df.fillna("")
    out = ["| " + " | ".join(map(str, df.columns)) + " |",
           "|" + "|".join(["---"] * len(df.columns)) + "|"]
    for _, row in df.iterrows():
        vals = [str(v).replace("|", "\\|").replace("\n", " ") for v in row.tolist()]
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def codebook() -> None:
    v = settings.VARIABLES.copy()
    ann_df = pd.read_parquet(settings.PROCESSED / "macro_annual_long.parquet")
    qtr_df = pd.read_parquet(settings.PROCESSED / "macro_quarterly_long.parquet")
    long_df = pd.read_parquet(settings.PROCESSED / "macro_long.parquet")
    reg_a = pd.read_csv(settings.PROCESSED / "regime_matrix_annual.csv")
    reg_q = pd.read_csv(settings.PROCESSED / "regime_matrix_quarterly.csv")
    ext = ann_df.extraction_date.iloc[0]
    n_a, n_q, n_long = len(ann_df), len(qtr_df), len(long_df)
    n_ra, n_ca = reg_a.shape[0], reg_a.shape[1] - 2
    n_rq, n_cq = reg_q.shape[0], reg_q.shape[1] - 2
    cov = pd.read_csv(settings.PROCESSED / "coverage.csv")
    agg = cov.groupby(["freq", "variable"]).agg(
        n_paises=("iso3", "nunique"), cobertura_min=("coverage_pct", "min"),
        cobertura_mediana=("coverage_pct", "median")).reset_index()
    v = v.merge(agg, left_on=["id", "freq"], right_on=["variable", "freq"], how="left")
    lines = [
        "# Codebook — dataset macroeconômico cross-country (v1.0.0)",
        "",
        f"Extração: **{ext}**. Âncora: **Brasil**. "
        f"Anual {settings.ANNUAL_START}–{settings.ANNUAL_END}; trimestral 1995T1–2026T4.",
        "",
        "## 1. Arquivos e grão",
        "",
        "| Arquivo | Grão | Linhas | Uso |",
        "|---|---|---|---|",
        f"| `data/processed/macro_long.parquet` | país × data × variável | {n_long:,} | dataset longo completo (anual + trimestral) |",
        f"| `data/processed/macro_annual_long.parquet` | país × ano × variável | {n_a:,} | painel anual |",
        f"| `data/processed/macro_quarterly_long.parquet` | país × trimestre × variável | {n_q:,} | subamostra trimestral |",
        "| `data/processed/wide/annual/{ISO3}.csv` | data × variável | 22+2 países | série wide por país |",
        "| `data/processed/wide/quarterly/{ISO3}.csv` | data × variável | 16 países | série wide trimestral |",
        f"| `data/processed/regime_matrix_annual.csv` | país × ano × dummy | {n_ra:,} × {n_ca} | matriz 0/1 de regimes |",
        f"| `data/processed/regime_matrix_quarterly.csv` | país × trimestre × dummy | {n_rq:,} × {n_cq} | matriz 0/1 trimestral |",
        "| `data/processed/coverage_matrix_annual.csv` | variável × país | 89 × 24 | % de cobertura |",
        "| `data/processed/coverage_panel_annual.csv` | país × variável × ano | 131.186 | matriz 0/1 de presença |",
        "",
        "## 2. Dicionário de campos",
        "",
        md(pd.DataFrame([
            ["iso3", "string", "Código ISO3 do país; `WLD` = mundo (agregado); `EU` = União Europeia (agregado, excluído de somas)."],
            ["country", "string", "Nome em português."],
            ["date", "date", "Fim do período: 31/12 do ano (anual) ou último dia do trimestre (trimestral)."],
            ["year", "int", "Ano do período (facilita merges anuais)."],
            ["variable", "string", "Identificador canônico (ver seção 5)."],
            ["value", "float", "Valor na unidade declarada; nunca em log (a transformação recomendada está em `transformation`)."],
            ["unit", "string", "Unidade nativa (%, % do PIB, milhões de LC, índice etc.)."],
            ["freq", "string", "`A` (anual) ou `Q` (trimestral)."],
            ["source", "string", "Fonte efetiva da linha (GMD, WDI, WEO, PWT, FRED, BCB, IBGE, BCB_FOCUS, derived, hardcoded)."],
            ["source_code", "string", "Código original (coluna GMD, indicador WDI/WEO, ID FRED, código SGS/SIDRA)."],
            ["source_detail", "string", "Descrição legível da série original."],
            ["source_url", "string", "URL da fonte."],
            ["vintage", "string", "Versão/vintage da fonte (quando disponível)."],
            ["transformation", "string", "Transformação recomendada para estimação: level, log, yoy, diff, hp_gap, hp_trend, fisher, pct_gdp, index, dummy, derived."],
            ["transform_applied", "string", "Sempre `none` neste arquivo: o valor é bruto/construído, não transformado. A pipeline DSGE aplica as transformações."],
            ["role", "string", "endogenous, exogenous, latent, shock, regime, validation."],
            ["model", "string", "Modelos em que a variável entra: ISLM, MF, ADAS, PC, TR, SOLOW, DSGE_S, DSGE_M."],
            ["dsge_var", "string", "Nome da variável no DSGE (quando aplicável)."],
            ["measurement_equation", "string", "Equação de medida do DSGE (quando observável)."],
            ["shock", "string", "Choque associado (quando a variável identifica um choque)."],
            ["coverage_note", "string", "Nota de cobertura temporal."],
            ["notes", "string", "Definição, ressalvas e decisões."],
            ["is_forecast", "bool", "True para projeções (GMD/WEO > 2025) ou anos preliminares."],
            ["quality_flag", "string", "ok, preliminary, forecast, derived, proxy, hp_filter, survey, policy, validation."],
            ["seasonal_adjustment", "string", "SA, NSA ou n/a."],
            ["imputation", "string", "none (não há imputação no dataset final; lacunas são preservadas)."],
            ["extraction_date", "string", "Timestamp UTC da extração."],
            ["regime_dummy", "string", "Lista separada por `|` das dummies ativas naquele país-data."],
        ], columns=["campo", "tipo", "descrição"])),
        "",
        "## 3. Convenções",
        "",
        "- **Sinal fiscal**: resultado primário e balanço fiscal positivos = superávit; negativos = déficit.",
        "- **Câmbio nominal**: unidades de moeda local por 1 USD (aumento = depreciação). Para EUR/GBP/AUD, a série do FRED (USD por LC) foi invertida.",
        "- **Deflator**: `gdp_deflator` tem base igual ao ano-base do PIB real do país (identidade nominal = real × deflator/100). `gdp_deflator_2010` é a versão 2010=100 para comparação.",
        "- **Juros**: % a.a. no anual; % a.a. no trimestral (média do período). A taxa trimestral usada no DSGE é i/4.",
        "- **Inflação**: % a.a. (variação 12 meses). No Brasil, `inflation` anual e trimestral vem do IPCA (BCB/IBGE), não do GMD; nos demais países, do GMD/OECD-MEI.",
        "- **Spread de crédito**: não há série trimestral harmonizada; a variável foi removida do dataset e a lacuna está registrada na auditoria.",
        "- **PIB real**: milhões de LC a preços constantes; a base varia por país. Não comparar níveis entre países sem `gdp_real_usd`.",
        "- **PPPs**: `gdp_ppp_usd` em milhões de int$ (WEO PPPGDP × 1000).",
        "- **Forecast**: 2026 é ano em curso (preliminary); 2027+ não entra. Projeções WEO/GMD para 2026 são marcadas.",
        "",
        "## 4. Registro de fontes",
        "",
        md(pd.DataFrame([
            [k, v.get("name", ""), v.get("version", ""), v.get("coverage", ""), v.get("role", "")]
            for k, v in settings.SOURCES_YML["sources"].items()
        ], columns=["id", "fonte", "versão", "cobertura", "papel"])),
        "",
        "## 5. Dicionário de variáveis",
        "",
        md(v[["id", "freq", "label", "unit", "source", "code", "transform", "role", "models",
              "n_paises", "cobertura_mediana", "coverage_note"]]
           .rename(columns={"id": "variável", "freq": "freq", "label": "rótulo", "unit": "unidade",
                            "source": "fonte", "code": "código", "transform": "transformação",
                            "role": "papel", "models": "modelos", "n_paises": "n_países",
                            "cobertura_mediana": "cobertura_mediana_%", "coverage_note": "cobertura"})),
        "",
        "## 6. Lacunas explícitas por país",
        "",
        "- **Brasil**: IPCA começa em 1980 (cobertura anual de inflação ~67%); PNAD Contínua trimestral começa em 2012; crédito/spread trimestral não têm série harmonizada; salário real trimestral não é usado.",
        "- **Argentina**: PIB trimestral começa em 2004; inflação oficial tem quebras metodológicas (INDEC 2007–2015); câmbio paralelo não é usado.",
        "- **Alemanha**: PIB trimestral do FRED começa em 1991 (pré-reunificação não coberto).",
        "- **Japão**: CPI trimestral do OECD-MEI termina em 2021T2; usar fontes nacionais para o período recente.",
        "- **China/Índia/Chile/Colômbia/Peru/Rússia**: sem PIB trimestral estável no FRED/OECD-MEI; entram apenas no painel anual.",
        "- **Arábia Saudita**: PIB trimestral começa em 2010.",
        "- **União Europeia**: agregado presente no G20, mas sem cobertura anual harmonizada para todas as variáveis; não entra em somas cross-country.",
        "- **Capital/PTF**: PWT termina em 2019; não extrapolamos.",
        "",
        "## 7. Reprodutibilidade",
        "",
        "Ver `README.md` e `Makefile`. O manifesto `data/processed/manifest.json` registra URL, timestamp, tamanho e SHA-256 de cada download. O cache fica em `data/raw/`.",
    ]
    (ROOT / "docs" / "01_codebook.md").write_text("\n".join(lines), encoding="utf-8")


def dsge_doc() -> None:
    meas = pd.read_csv(settings.CONFIG / "dsge_measurement.psv", sep="|")
    lat = pd.read_csv(settings.CONFIG / "dsge_latent_shocks.psv", sep="|")
    post = pd.read_csv(settings.PROCESSED / "dsge_small_posterior_bra.csv")
    svd = pd.read_csv(settings.PROCESSED / "dsge_small_identification_svd_bra.csv")
    imp = pd.read_csv(settings.PROCESSED / "dsge_small_identification_params_bra.csv")
    mom = pd.read_csv(settings.PROCESSED / "dsge_small_moments_bra.csv")
    fevd = pd.read_csv(settings.PROCESSED / "dsge_small_fevd_bra.csv")
    calib = pd.DataFrame([
        ["sigma", 1.0, "Curvatura da IS (EIS inversa)", "Calibrado", "Literatura NK (Galí, 2015)"],
        ["kappa", 0.08, "Inclinação da Curva de Phillips", "Calibrado", "Literatura NK; 0,08/trim."],
        ["phi_pi", 1.50, "Resposta da Taylor à inflação", "Calibrado", "Princípio de Taylor"],
        ["phi_x", 0.125, "Resposta da Taylor ao hiato", "Calibrado", "Regra de Taylor original (1993)"],
        ["rho", 0.80, "Suavização da taxa de juros", "Calibrado", "Literatura de regras monetárias"],
        ["beta", 0.9925, "Desconto trimestral", "Calibrado", "Taxa real anual ~3%"],
    ], columns=["parâmetro", "valor", "descrição", "status", "justificativa"])
    lines = [
        "# DSGE — observáveis, variáveis latentes, choques e identificação",
        "",
        "Dois modelos: **DSGE_S** (NK de 3 equações, estimado para Brasil e EUA) e "
        "**DSGE_M** (SW-lite calibrado, 12 variáveis, 9 choques).",
        "",
        "## 1. Tabela observável → modelo",
        "",
        md(meas),
        "",
        "### 1.1 Choques e observáveis que os identificam",
        "",
        md(pd.DataFrame([
            ["Demanda", "output_gap", "inflação, juros", "choque na IS; sem restrição de sinal", "confunde-se com markup e política"],
            ["Markup", "inflation", "hiato, juros", "choque na NKPC; residual de custo", "absorve commodities e câmbio"],
            ["Monetário", "policy_rate", "hiato, inflação", "residual da regra de Taylor", "absorve mudanças de regime da Selic"],
            ["Fiscal", "gov_exp_real", "hiato, dívida", "AR(1) do gasto; sem regra fiscal explícita", "gasto total vs consumo do governo"],
            ["Externo", "foreign_output", "exportações, câmbio", "AR(1) do PIB dos EUA", "proxy imperfeita de demanda externa"],
            ["Risco", "credit_spread (anual)", "câmbio, juros", "prêmio de risco AR(1)", "sem spread trimestral harmonizado"],
            ["Tecnologia", "tfp (anual)", "PIB, investimento", "AR(1) da PTF", "sem proxy trimestral"],
            ["Oferta de trabalho", "emprego/horas (anual)", "salário, inflação", "AR(1) do salário", "sem horas trimestrais"],
        ], columns=["choque", "observável primário", "outros observáveis", "identificação", "risco"])),
        "",
        "**Regra de não dupla contagem:** cada observável tem um choque **primário**; os demais choques afetam todos os observáveis por propagação, mas não usamos a mesma série como instrumento de dois choques. A tabela acima é a única atribuição primária.",
        "",
        "### 1.2 Expectativas: racionais, híbridas ou survey",
        "",
        "| Tipo | Como entra | Onde |",
        "|---|---|---|",
        "| Inflação | **Híbrida** (π_{t-1} + E_t π_{t+1}) na NKPC; expectativa racional model-consistent | DSGE_S, DSGE_M |",
        "| Inflação (survey) | Focus/Michigan usados no juro real ex ante e na validação; **não** substituem E_t π_{t+1} | `real_rate_ex_ante`, `inflation_expectations` |",
        "| Juros | Racional, via regra de Taylor; sem survey de juros no modelo | DSGE_S, DSGE_M |",
        "| Câmbio | Não há UIP explícita; câmbio não entra no DSGE_S e entra apenas via prêmio de risco no DSGE_M | DSGE_M |",
        "",
        "### 1.3 Balanced growth path (BGP)",
        "",
        "- **DSGE_S:** estado estacionário com inflação zero, hiato zero e juro real r = 1/β − 1 = 0,76% a.a. (β=0,9925). As variáveis são desvios log-lineares; não há crescimento tendencial. A amostra é demovida em média (π e i), o que absorve o nível de inflação/juro.",
        "- **DSGE_M:** trajetória balanceada com crescimento g = 1,6% a.a., inflação zero, juro real r = 1/β − 1, razão capital-produto k/y = i_y/(g+δ) ≈ 6,9, participações c_y=0,60, i_y=0,20, g_y=0,20. O modelo é linearizado em torno do BGP; x, π, i, c, inv e g são desvios.",
        "- **Calibração do BGP:** β=0,9925 (3% a.a.), δ=0,025/trim., g=0,004/trim. (1,6% a.a.), markup de 20% (ε=6), participação do trabalho consistente com PWT.",
        "",
        "### 1.4 Dummies de regime no DSGE",
        "",
        md(pd.DataFrame([
            ["br_it", "parameter_break", "φπ, ρ, σ_π", "Mudança do regime monetário em 1999; a regra de Taylor e a persistência da inflação mudam."],
            ["br_lrf / br_ceiling / br_new_framework", "parameter_break", "resposta fiscal, gasto", "Regras fiscais alteram a função de reação do gasto e a dinâmica da dívida."],
            ["g_gfc_2008 / g_pandemic_2020", "observed_shock", "demanda, risco", "Choques grandes e datados; entram como dummies de choque observável."],
            ["g_commodity_supercycle", "observed_shock", "termos de troca", "Período de preços de commodities; desloca o prêmio de risco/termos de troca no DSGE_M."],
            ["us_zlb_2008 / eu_zlb", "parameter_break", "ρ, φπ", "ZLB restringe a regra de Taylor; quebra de parâmetro."],
            ["ar_default_2001", "observed_shock", "prêmio de risco", "Default e pesificação; choque de risco soberano."],
            ["ar_indec_2007 / br_ipca_rebase_2012 / br_gdp_rebase_2010", "parameter_break", "nível/viés de medida", "Mudanças metodológicas; dummies de nível, não de ciclo."],
        ], columns=["dummy", "papel", "parâmetro/canal", "justificativa"])),
        "",
        "## 2. Variáveis latentes e choques",
        "",
        md(lat),
        "",
        "## 3. Calibração vs estimação",
        "",
        "O núcleo estrutural do DSGE_S é **calibrado**; apenas hábitos, indexação, "
        "persistência e escala dos choques são estimados. A tentativa de estimar livremente "
        "sigma, kappa, phi_pi e rho convergiu para a fronteira do espaço paramétrico "
        "(sigma≈10, kappa≈1, phi_pi≈5, rho≈0,06), sinal de identificação fraca e "
        "misspecification; por isso o núcleo foi fixado e o fato está registrado no relatório de auditoria.",
        "",
        md(calib),
        "",
        "### 3.1 Prior vs posterior (Brasil, 1999T3–2025T4, 106 obs)",
        "",
        md(post.round(3)),
        "",
        "## 4. Identificação",
        "",
        "Matriz jacobiana de momentos teóricos (variâncias, autocorrelações e correlações "
        "cruzadas) em relação aos parâmetros estimados, normalizada e decomposta em SVD. "
        "Valores singulares pequenos indicam direções fracamente identificadas.",
        "",
        md(svd.round(4)),
        "",
        "Importância de cada parâmetro (norma da coluna do jacobiano normalizado):",
        "",
        md(imp.round(3)),
        "",
        "**Leitura**: a última direção tem valor singular ~0 (razão < 0,001), indicando "
        "combinação linear de parâmetros não identificada pelos momentos escolhidos. "
        "As correlações cruzadas hiato–juro e hiato–inflação são as dimensões mais informativas.",
        "",
        "## 5. Momentos: dados vs modelo",
        "",
        md(mom.round(3)),
        "",
        "O modelo **não reproduz** a volatilidade da Selic (4,95% vs ~1,0%) nem o sinal da "
        "correlação hiato–juro (dados ≈ -0,09; modelo ≈ -0,79). Isso é consistente com a "
        "ausência de mudanças de regime e de um choque financeiro explícito no modelo pequeno.",
        "",
        "## 6. Decomposição de variância",
        "",
        md(fevd.round(3)),
        "",
        "A decomposição atribui à política monetária ~74% da variância do hiato e ~56% da "
        "inflação — resultado não crível e que reforça o diagnóstico de identificação fraca. "
        "Não usar para inferência causal sem restrições de sinal ou mais observáveis.",
        "",
        "## 7. Riscos de identificação (resumo)",
        "",
        "1. **Hiato HP** é construído e impõe tendência suave; erros de medida contaminam a IS.",
        "2. **Três choques e três observáveis** deixam a decomposição exatamente identificada e sensível à especificação.",
        "3. **Selic** tem quebras de regime (1999, 2015–16, 2020–21) não modeladas; o choque monetário absorve a política.",
        "4. **Expectativas** Focus são de 12 meses, não do horizonte de 1 trimestre do modelo.",
        "5. **DSGE_M** é calibrado, não estimado; os momentos não devem ser lidos como teste formal.",
        "6. **Parâmetros estruturais** fora do núcleo calibrado não são identificados com a amostra disponível.",
    ]
    (ROOT / "docs" / "02_dsge_observables.md").write_text("\n".join(lines), encoding="utf-8")


def regime_doc() -> None:
    meta = pd.read_csv(settings.PROCESSED / "regime_metadata.csv")
    ann = pd.read_csv(settings.PROCESSED / "regime_matrix_annual.csv")
    q = pd.read_csv(settings.PROCESSED / "regime_matrix_quarterly.csv")
    by_kind = meta.groupby("tipo").size().rename("n").reset_index()
    by_role = meta.groupby("papel_dsge").size().rename("n").reset_index()
    lines = [
        "# Dummies de regime — metadados, matriz e papel no DSGE",
        "",
        f"**{len(meta)} dummies**, codificadas em `config/regimes.yml` e materializadas em "
        f"`regime_matrix_annual.csv` ({ann.shape[0]} país-ano) e `regime_matrix_quarterly.csv` "
        f"({q.shape[0]} país-trimestre).",
        "",
        "## 1. Cobertura por tipo",
        "",
        md(by_kind),
        "",
        "## 2. Papel no DSGE",
        "",
        md(by_role),
        "",
        "- `observed_shock`: entra como regressor exógeno/choque observável (ex.: GFC, pandemia, commodity).",
        "- `parameter_break`: quebra de parâmetro (ex.: metas de inflação, teto de gastos, ZLB).",
        "- `control`: controle em modelos reduzidos, sem papel estrutural.",
        "- `sample_split`: define amostra (hiperinflação, câmbio fixo).",
        "",
        "## 3. Matriz país × dummy — Brasil (recorte)",
        "",
        "A matriz completa (0/1 para todos os 22 países e 1960–2026) está em "
        "`data/processed/regime_matrix_annual.csv`. O recorte abaixo mostra as dummies "
        "brasileiras mais relevantes e os anos de ativação.",
        "",
        md(meta[meta.paises.str.contains("BRA")][["dummy", "nome", "tipo", "inicio", "fim", "papel_dsge"]]
           .sort_values("inicio")),
        "",
        "## 4. Como usar",
        "",
        "- Em modelos reduzidos: incluir a dummy como controle ou quebra de intercepto/slope; a coluna `regime_dummy` do dataset longo lista as dummies ativas.",
        "- No DSGE_S: `br_it`, `us_zlb_2008`, `g_gfc_2008`, `g_pandemic_2020` entram como quebras de parâmetro ou choques observáveis; ver `docs/02_dsge_observables.md`.",
        "- No DSGE_M: `br_ceiling`, `br_new_framework`, `br_lrf` deslocam a regra fiscal; `g_commodity_supercycle` desloca o prêmio de risco/termos de troca.",
        "",
        "## 5. Metadados completos",
        "",
        "Arquivo: `data/processed/regime_metadata.csv` (colunas: dummy, nome, tipo, escopo, "
        "países, início, fim, frequências, fonte, URL, variáveis afetadas, modelos, papel no DSGE, justificativa).",
        "",
        md(meta[["dummy", "nome", "tipo", "inicio", "fim", "fonte", "papel_dsge"]].head(30)),
        "",
        "*(tabela completa no CSV; aqui listamos as 30 primeiras para legibilidade)*",
    ]
    (ROOT / "docs" / "03_regime_dummies.md").write_text("\n".join(lines), encoding="utf-8")


def groups_doc() -> None:
    rows = []
    for g, meta in settings.GROUP_META.items():
        rows.append([g, meta["name"], ", ".join(meta["members"]), len(meta["members"]), meta["justification"]])
    lines = [
        "# Grupos de países — listas fechadas e justificativa",
        "",
        "A lista de países é **fechada**: 22 países + agregado UE. Grupos se sobrepõem de "
        "propósito; a UE é agregado e é excluída de somas/médias para evitar dupla contagem.",
        "",
        md(pd.DataFrame(rows, columns=["grupo", "nome", "membros", "n", "justificativa"])),
        "",
        "## Uso nos modelos",
        "",
        "- **Painel anual**: todos os 22 países; a UE entra apenas onde há série (WEO), sem uso em somas.",
        "- **Painel trimestral**: 16 países com PIB trimestral estável (BRA, USA, DEU, GBR, JPN, CAN, MEX, AUS, FRA, ITA, KOR, ZAF, TUR, IDN, ARG, SAU); CHN, IND, CHL, COL, PER e RUS ficam no anual.",
        "- **DSGE**: Brasil (âncora) e EUA (validação); demais países entram nos modelos reduzidos e na comparação de momentos.",
        "",
        "## Checagem de dupla contagem",
        "",
        "- `EU` tem `iso3=EU`, `role=exogenous` e é marcada como agregado em `config/countries.yml`.",
        "- Nenhuma soma cross-country inclui `EU` ou `WLD`; `WLD` só aparece em `world_gdp_real`/`world_gdp_growth`.",
    ]
    (ROOT / "docs" / "05_country_groups.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    codebook()
    dsge_doc()
    regime_doc()
    groups_doc()
    print("docs gerados")
