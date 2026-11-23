# DSGE — observáveis, variáveis latentes, choques e identificação

Dois modelos: **DSGE_S** (NK de 3 equações, estimado para Brasil e EUA) e **DSGE_M** (SW-lite calibrado, 12 variáveis, 9 choques).

## 1. Tabela observável → modelo

| model | observable | source | transformation | model_variable | measurement_equation | shock | notes |
|---|---|---|---|---|---|---|---|
| DSGE_S | output_gap | IBGE/FRED PIB trimestral SA -> HP(1600) | 100*(log y_t - log y*_t) | x_t | x_obs,t = 100*x_t + e_x,t | demanda | Hiato HP bicaudal; robustez com hiato unicaudal e funcao de producao no relatorio. |
| DSGE_S | inflation | BCB IPCA mensal -> indice trimestral -> X-13 -> qoq SAAR | 400*dlog(CPI_SA,t) | pi_t | pi_obs,t = 400*pi_t + e_pi,t | markup | Inflacao cheia; nucleo usado em robustez. |
| DSGE_S | policy_rate | BCB Selic meta (media trimestral) | taxa anual % | i_t | i_obs,t = 400*i_t + e_i,t | monetario | Taxa trimestral simples; erro de medida 0,10 p.p. |
| DSGE_S | inflation_expectations | BCB Focus (IPCA 12m) | media trimestral | E_t pi_{t+1} | usada em r_t = i_t - E_t pi_{t+1} | - | Nao entra como observavel na estimacao basica; usada no juro real ex ante. |
| DSGE_M | output_gap | IBGE/FRED PIB trimestral SA -> HP(1600) | 100*(log y_t - log y*_t) | x_t | x_obs,t = 100*x_t | demanda | Mesmo hiato do modelo pequeno. |
| DSGE_M | inflation | BCB IPCA -> X-13 -> qoq SAAR | 400*dlog(CPI_SA,t) | pi_t | pi_obs,t = 400*pi_t | markup | Curva de Phillips hibrida. |
| DSGE_M | policy_rate | BCB Selic meta | taxa anual % | i_t | i_obs,t = 400*i_t | monetario | Regra de Taylor com suavizacao. |
| DSGE_M | consumption_real | IBGE CNT 6612 (consumo das familias) | 100*HP(log C_t) | c_t | c_obs,t = 100*c_t | preferencia | Componente da demanda. |
| DSGE_M | investment_real | IBGE CNT 6612 (FBCF) | 100*HP(log I_t) | inv_t | inv_obs,t = 100*inv_t | investimento | Demanda de investimento reduzida. |
| DSGE_M | gov_exp_real | IBGE CNT 6612 (consumo do governo) | 100*HP(log G_t) | g_t | g_obs,t = 100*g_t | fiscal | Gasto publico real. |
| DSGE_M | foreign_output | FRED GDPC1 (PIB EUA) | 100*HP(log Y*_t) | ystar_t | y*_obs,t = 100*ystar_t | externo | Proxy de demanda externa. |

### 1.1 Choques e observáveis que os identificam

| choque | observável primário | outros observáveis | identificação | risco |
|---|---|---|---|---|
| Demanda | output_gap | inflação, juros | choque na IS; sem restrição de sinal | confunde-se com markup e política |
| Markup | inflation | hiato, juros | choque na NKPC; residual de custo | absorve commodities e câmbio |
| Monetário | policy_rate | hiato, inflação | residual da regra de Taylor | absorve mudanças de regime da Selic |
| Fiscal | gov_exp_real | hiato, dívida | AR(1) do gasto; sem regra fiscal explícita | gasto total vs consumo do governo |
| Externo | foreign_output | exportações, câmbio | AR(1) do PIB dos EUA | proxy imperfeita de demanda externa |
| Risco | credit_spread (anual) | câmbio, juros | prêmio de risco AR(1) | sem spread trimestral harmonizado |
| Tecnologia | tfp (anual) | PIB, investimento | AR(1) da PTF | sem proxy trimestral |
| Oferta de trabalho | emprego/horas (anual) | salário, inflação | AR(1) do salário | sem horas trimestrais |

**Regra de não dupla contagem:** cada observável tem um choque **primário**; os demais choques afetam todos os observáveis por propagação, mas não usamos a mesma série como instrumento de dois choques. A tabela acima é a única atribuição primária.

### 1.2 Expectativas: racionais, híbridas ou survey

| Tipo | Como entra | Onde |
|---|---|---|
| Inflação | **Híbrida** (π_{t-1} + E_t π_{t+1}) na NKPC; expectativa racional model-consistent | DSGE_S, DSGE_M |
| Inflação (survey) | Focus/Michigan usados no juro real ex ante e na validação; **não** substituem E_t π_{t+1} | `real_rate_ex_ante`, `inflation_expectations` |
| Juros | Racional, via regra de Taylor; sem survey de juros no modelo | DSGE_S, DSGE_M |
| Câmbio | Não há UIP explícita; câmbio não entra no DSGE_S e entra apenas via prêmio de risco no DSGE_M | DSGE_M |

### 1.3 Balanced growth path (BGP)

- **DSGE_S:** estado estacionário com inflação zero, hiato zero e juro real r = 1/β − 1 = 0,76% a.a. (β=0,9925). As variáveis são desvios log-lineares; não há crescimento tendencial. A amostra é demovida em média (π e i), o que absorve o nível de inflação/juro.
- **DSGE_M:** trajetória balanceada com crescimento g = 1,6% a.a., inflação zero, juro real r = 1/β − 1, razão capital-produto k/y = i_y/(g+δ) ≈ 6,9, participações c_y=0,60, i_y=0,20, g_y=0,20. O modelo é linearizado em torno do BGP; x, π, i, c, inv e g são desvios.
- **Calibração do BGP:** β=0,9925 (3% a.a.), δ=0,025/trim., g=0,004/trim. (1,6% a.a.), markup de 20% (ε=6), participação do trabalho consistente com PWT.

### 1.4 Dummies de regime no DSGE

| dummy | papel | parâmetro/canal | justificativa |
|---|---|---|---|
| br_it | parameter_break | φπ, ρ, σ_π | Mudança do regime monetário em 1999; a regra de Taylor e a persistência da inflação mudam. |
| br_lrf / br_ceiling / br_new_framework | parameter_break | resposta fiscal, gasto | Regras fiscais alteram a função de reação do gasto e a dinâmica da dívida. |
| g_gfc_2008 / g_pandemic_2020 | observed_shock | demanda, risco | Choques grandes e datados; entram como dummies de choque observável. |
| g_commodity_supercycle | observed_shock | termos de troca | Período de preços de commodities; desloca o prêmio de risco/termos de troca no DSGE_M. |
| us_zlb_2008 / eu_zlb | parameter_break | ρ, φπ | ZLB restringe a regra de Taylor; quebra de parâmetro. |
| ar_default_2001 | observed_shock | prêmio de risco | Default e pesificação; choque de risco soberano. |
| ar_indec_2007 / br_ipca_rebase_2012 / br_gdp_rebase_2010 | parameter_break | nível/viés de medida | Mudanças metodológicas; dummies de nível, não de ciclo. |

## 2. Variáveis latentes e choques

| tipo | nome | descricao | observaveis_identificadores | papel_no_modelo | risco_identificacao |
|---|---|---|---|---|---|
| latente | PIB potencial | tendencia nao observada do produto | output_gap; inflacao; juros | y*_t | Filtro HP impoe tendencia suave e viés de fim de amostra. |
| latente | Hiato do produto | x_t = 100*(log y - log y*) | output_gap | estado | Construcao por HP gera erro de medida e look-ahead. |
| latente | Taxa neutra r* | juro real de equilibrio | juro real ex ante; juros; inflacao | r*_t | Proxy por HP do juro real ex ante; nao e estimativa estrutural. |
| latente | Desemprego natural u_n | desemprego de equilibrio | desemprego; inflacao | u_n | Sem Curva de Phillips com desemprego na estimacao; usado em modelos reduzidos. |
| latente | Capital | estoque de capital | investimento; PIB | k_t | PWT termina em 2019; extrapolacao nao usada. |
| latente | Salario real | w_t | salario real; inflacao; produtividade | w_t | Dados trimestrais de salario ausentes para o Brasil; calibrado. |
| latente | Markup | margem de precos | inflacao; custo marginal | mc_t | Nao observado diretamente; identificado pelo choque de markup. |
| latente | Expectativas | E_t pi_{t+1} | Focus; inflacao realizada | expectativas | Survey Focus cobre 12m a frente, nao o horizonte de 1 trimestre. |
| choque | Tecnologia | a_t | PIB; investimento; produtividade | a_t | PWT anual; sem proxy trimestral confiavel. |
| choque | Preferencia | demanda | hiato; consumo | ed_t | Choque composto de demanda; nao separa consumo publico/privado. |
| choque | Politica monetaria | ei_t | Selic; hiato; inflacao | ei_t | Regra de Taylor com erro; risco de contaminacao por regime. |
| choque | Politica fiscal | eg_t | gasto; divida; PIB | eg_t | Gasto total vs consumo do governo; perimetro fiscal. |
| choque | Markup | epi_t | inflacao; custo marginal | epi_t | Pode capturar choques de commodities e cambio. |
| choque | Premio de risco | er_t | spread; cambio; juros | rp_t | Spread brasileiro sem serie trimestral harmonizada. |
| choque | Externo | ey_t | PIB mundial; exportacoes | ystar_t | Proxy por PIB dos EUA; nao e demanda externa ponderada. |
| choque | Oferta de trabalho | ew_t | emprego; salario; inflacao | ew_t | Sem horas trimestrais para o Brasil. |

## 3. Calibração vs estimação

O núcleo estrutural do DSGE_S é **calibrado**; apenas hábitos, indexação, persistência e escala dos choques são estimados. A tentativa de estimar livremente sigma, kappa, phi_pi e rho convergiu para a fronteira do espaço paramétrico (sigma≈10, kappa≈1, phi_pi≈5, rho≈0,06), sinal de identificação fraca e misspecification; por isso o núcleo foi fixado e o fato está registrado no relatório de auditoria.

| parâmetro | valor | descrição | status | justificativa |
|---|---|---|---|---|
| sigma | 1.0 | Curvatura da IS (EIS inversa) | Calibrado | Literatura NK (Galí, 2015) |
| kappa | 0.08 | Inclinação da Curva de Phillips | Calibrado | Literatura NK; 0,08/trim. |
| phi_pi | 1.5 | Resposta da Taylor à inflação | Calibrado | Princípio de Taylor |
| phi_x | 0.125 | Resposta da Taylor ao hiato | Calibrado | Regra de Taylor original (1993) |
| rho | 0.8 | Suavização da taxa de juros | Calibrado | Literatura de regras monetárias |
| beta | 0.9925 | Desconto trimestral | Calibrado | Taxa real anual ~3% |

### 3.1 Prior vs posterior (Brasil, 1999T3–2025T4, 106 obs)

| parameter | prior_mean | prior_sd | post_mean | post_sd | q05 | median | q95 | ess |
|---|---|---|---|---|---|---|---|---|
| a | 0.5 | 0.151 | 0.068 | 0.029 | 0.028 | 0.064 | 0.125 | 333.678 |
| b | 0.5 | 0.151 | 0.059 | 0.026 | 0.025 | 0.056 | 0.108 | 342.901 |
| rho_x | 0.5 | 0.151 | 0.048 | 0.021 | 0.018 | 0.045 | 0.086 | 242.163 |
| rho_pi | 0.5 | 0.151 | 0.052 | 0.022 | 0.022 | 0.049 | 0.091 | 462.693 |
| rho_i | 0.5 | 0.151 | 0.449 | 0.14 | 0.221 | 0.446 | 0.694 | 329.462 |
| sd_x | 0.008 | 0.006 | 0.008 | 0.006 | 0.001 | 0.007 | 0.021 | 292.477 |
| sd_pi | 0.004 | 0.003 | 0.004 | 0.003 | 0.0 | 0.003 | 0.01 | 449.946 |
| sd_i | 0.002 | 0.002 | 0.002 | 0.002 | 0.0 | 0.002 | 0.006 | 323.208 |
| me_x | 0.004 | 0.003 | 0.004 | 0.003 | 0.0 | 0.003 | 0.01 | 159.105 |

## 4. Identificação

Matriz jacobiana de momentos teóricos (variâncias, autocorrelações e correlações cruzadas) em relação aos parâmetros estimados, normalizada e decomposta em SVD. Valores singulares pequenos indicam direções fracamente identificadas.

| singular_value | ratio_to_max | cum_share |
|---|---|---|
| 12.4115 | 1.0 | 0.641 |
| 6.9267 | 0.5581 | 0.8406 |
| 5.0967 | 0.4106 | 0.9487 |
| 3.2561 | 0.2623 | 0.9928 |
| 1.2031 | 0.0969 | 0.9988 |
| 0.4923 | 0.0397 | 0.9999 |
| 0.1666 | 0.0134 | 1.0 |
| 0.085 | 0.0068 | 1.0 |
| 0.0 | 0.0 | 1.0 |

Importância de cada parâmetro (norma da coluna do jacobiano normalizado):

| parameter | importance | max_abs_loading |
|---|---|---|
| a | 0.1 | 0.902 |
| b | 0.063 | 0.895 |
| rho_x | 0.02 | 0.885 |
| rho_pi | 0.029 | 0.874 |
| rho_i | 0.438 | 0.929 |
| sd_x | 0.476 | 0.973 |
| sd_pi | 0.616 | 0.945 |
| sd_i | 1.0 | 0.912 |
| me_x | 0.0 | 1.0 |

**Leitura**: a última direção tem valor singular ~0 (razão < 0,001), indicando combinação linear de parâmetros não identificada pelos momentos escolhidos. As correlações cruzadas hiato–juro e hiato–inflação são as dimensões mais informativas.

## 5. Momentos: dados vs modelo

| moment | data | model |
|---|---|---|
| sd_gap | 1.826 | 1.825 |
| ac1_gap | 0.632 | 0.567 |
| sd_pi | 3.598 | 2.067 |
| ac1_pi | 0.464 | 0.366 |
| sd_i | 4.949 | 1.007 |
| ac1_i | 0.967 | 0.763 |
| corr_gap_pi | 0.133 | 0.573 |
| corr_gap_i | -0.091 | -0.79 |
| corr_pi_i | 0.255 | -0.396 |

O modelo **não reproduz** a volatilidade da Selic (4,95% vs ~1,0%) nem o sinal da correlação hiato–juro (dados ≈ -0,09; modelo ≈ -0,79). Isso é consistente com a ausência de mudanças de regime e de um choque financeiro explícito no modelo pequeno.

## 6. Decomposição de variância

| shock | observable | share |
|---|---|---|
| demanda | output_gap | 0.193 |
| demanda | inflation | 0.013 |
| demanda | policy_rate | 0.038 |
| markup | output_gap | 0.074 |
| markup | inflation | 0.43 |
| markup | policy_rate | 0.235 |
| monetario | output_gap | 0.736 |
| monetario | inflation | 0.556 |
| monetario | policy_rate | 0.736 |

A decomposição atribui à política monetária ~74% da variância do hiato e ~56% da inflação — resultado não crível e que reforça o diagnóstico de identificação fraca. Não usar para inferência causal sem restrições de sinal ou mais observáveis.

## 7. Riscos de identificação (resumo)

1. **Hiato HP** é construído e impõe tendência suave; erros de medida contaminam a IS.
2. **Três choques e três observáveis** deixam a decomposição exatamente identificada e sensível à especificação.
3. **Selic** tem quebras de regime (1999, 2015–16, 2020–21) não modeladas; o choque monetário absorve a política.
4. **Expectativas** Focus são de 12 meses, não do horizonte de 1 trimestre do modelo.
5. **DSGE_M** é calibrado, não estimado; os momentos não devem ser lidos como teste formal.
6. **Parâmetros estruturais** fora do núcleo calibrado não são identificados com a amostra disponível.