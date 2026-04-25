# Sales Hunter — Spec de Extração Automatizada

> Gerado: 2026-04-25 | Status: VALIDADO (13/16 relatórios baixados com sucesso)

---

## Autenticação (RESOLVIDO)

### Endpoint de Login
```
POST http://saleshunter.vitao.com.br/login
Content-Type: application/x-www-form-urlencoded

_token={CSRF_TOKEN}&email=leandro%40maisgranel.com.br&password=Inicial123
```

### Fluxo Completo
1. `GET /login` → Salvar cookies + extrair `_token` do HTML
2. `POST /login` → Com `_token`, email, password (mesmos cookies)
3. `GET /` → Follow redirect (valida session)
4. `GET /relatorios` → Pegar novo `_token` para download
5. `POST /relatorios/gerar/excel` → Download Excel

### CSRF Token
- Campo: `<input name="_token" value="...">`
- OBRIGATÓRIO: Usar mesmo cookie jar em TODOS os requests
- Token é consumido a cada POST — precisa pegar novo para cada download

---

## Endpoints de Download

### Geração de Relatório (Excel)
```
POST http://saleshunter.vitao.com.br/relatorios/gerar/excel
Content-Type: application/x-www-form-urlencoded

_token={CSRF}&tipo_relatorio={TIPO}&empresa_faturamento[]={EMP_ID}&data_inicial={YYYY-MM-DD}&data_final={YYYY-MM-DD}
```

### Geração de Relatório (HTML Preview)
```
POST http://saleshunter.vitao.com.br/relatorios/gerar
```
(Mesmos campos)

---

## IMPORTANTE: Formato de Data

**CORRETO**: `data_inicial=2026-04-01&data_final=2026-04-25` (YYYY-MM-DD)
**ERRADO**: `data_inicial=01/04/2026` (DD/MM/YYYY) ← CAUSA REDIRECT 302

O campo HTML é `<input type="date">` que usa formato ISO nativo.

---

## Tipos de Relatório (valores para `tipo_relatorio`)

### P1 — Diário (8 tipos)
| Valor | Nome | Colunas |
|-------|------|---------|
| `RelatorioDeFaturamentoPorCliente` | Faturamento por cliente | 30 (CÓD, Cliente, CNPJ, Grupo, Canal, Estado, Venda, Devolução, Bonificação, Faturado...) |
| `RelatorioDeFaturamentoPorNotaFiscalDetalhada` | NF detalhada | ~25 |
| `RelatorioDeFaturamentoPorProduto` | Fat. por produto | ~15 |
| `RelatorioDeFaturamentoPorEmpresa` | Fat. por empresa | ~10 |
| `RelatorioDeCarteiraPorCliente` | Carteira clientes | ~20 (NOTA: retorna 500, pode requerer filtros especiais) |
| `RelatorioDeDebitos` | Débitos | ~20 |
| `RelatorioDeDevolucaoPorCliente` | Devoluções | ~20 |
| `RelatorioDePedidos` | Pedidos por produto | ~25 (NOTA: só funciona para empresa 12/CWB) |

### P2 — Semanal
| Valor | Nome |
|-------|------|
| `RelatorioDeFaturamentoPorEstado` | Fat. por UF |
| `RelatorioDeFaturamentoPorGrupoMateriais` | Fat. por grupo materiais |
| `RelatorioDeMixAtivoPorCliente` | Mix ativo |
| `RelatorioDeMixPorProduto` | Mix faturamento |
| `RelatorioDeMargemPorProduto` | Margem por produto |
| `RelatorioDeDevolucaoPorProduto` | Devolução por produto |

### P3 — Mensal
| Valor | Nome |
|-------|------|
| `RelatorioDeFaturamentoPorHierarquia` | Hierarquia |
| `RelatorioDeFaturamentoPorListaPreco` | Lista preço |
| `RelatorioDeFaturamentoPorDescontoFinanceiro` | Desconto financeiro |
| `RelatorioDeGrupoDeCliente` | Grupo clientes |
| `RelatorioDeFaturamentoPorCondPagamento` | Tempo recebimento |
| `RelatorioDeFaturamentoPorProdutoKg` | Produto KG |
| `RelatorioDeFaturamentoPorGrupoMateriaisKg` | Grupo materiais KG |
| `RelatorioDeProdutos` | Produtos |

---

## Empresas

| ID | Nome | Código |
|----|------|--------|
| 12 | VITAO - Curitiba | cwb |
| 13 | VITAO - Vila Velha | vv |

---

## Colunas do Relatório Principal (fat_cliente)

30 colunas:
1. CÓD. Cliente
2. Cliente (razão social)
3. CPF/CNPJ
4. Grupo
5. Canal de venda
6. Lista preço atual
7. Desc. comercial atual
8. Desc. financeiro atual
9. Estado
10. Cidade
11. Bairro
12. Endereço
13. CEP
14. Venda {mês}/{ano}
15. Devolução {mês}/{ano}
16. Bonificação {mês}/{ano}
17. Faturado {mês}/{ano}
18. % devolução {mês}/{ano}
19. % bonificação {mês}/{ano}
20. Total venda
21. Total devolução
22. Total bonificação
23. Total faturado
24. Média faturamento
25. % devolução total
26. % bonificação total
27. CÓD. SAP ZR
28. Razão social ZR
29. CÓD. SAP ZX
30. Razão social ZX

---

## Resultados da Extração (25/Abr/2026)

| Relatório | CWB | VV | Status |
|-----------|-----|-----|--------|
| fat_cliente | 853KB ✅ | 853KB ✅ | OK |
| fat_nf_det | 2.4MB ✅ | 2.4MB ✅ | OK |
| fat_produto | 35KB ✅ | 35KB ✅ | OK |
| fat_empresa | 6.7KB ✅ | 6.7KB ✅ | OK |
| debitos | 388KB ✅ | 388KB ✅ | OK |
| devolucao_cliente | 519KB ✅ | 184KB ✅ | OK |
| pedidos_produto | 2.0MB ✅ | 302 ❌ | VV indisponível |
| carteira | 500 ❌ | 500 ❌ | Requer debug |

**Total**: 13/16 (81%) — 10MB+ de dados REAIS do SAP

---

## Script curl Completo (para scheduled task)

```bash
#!/bin/bash
# Sales Hunter Daily Extraction
# Scheduled: 07:05 (após Deskrio)

OUTDIR="CRM-VITAO360/data/sales_hunter/$(date +%Y-%m-%d)/morning"
mkdir -p "$OUTDIR"
COOKIE_JAR="/tmp/sh_cookies_$(date +%s).txt"

# 1. Login
curl -s -c "$COOKIE_JAR" "http://saleshunter.vitao.com.br/login" -o /tmp/sh_login.html
TOKEN=$(grep -oP 'name="_token"[^>]*value="\K[^"]+' /tmp/sh_login.html | head -1)
curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -d "_token=${TOKEN}&email=leandro%40maisgranel.com.br&password=Inicial123" \
  "http://saleshunter.vitao.com.br/login" -o /dev/null
curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" "http://saleshunter.vitao.com.br" -o /dev/null

# 2. Download each report
REPORTS="RelatorioDeFaturamentoPorCliente:fat_cliente
RelatorioDeFaturamentoPorNotaFiscalDetalhada:fat_nf_det
RelatorioDeFaturamentoPorProduto:fat_produto
RelatorioDeFaturamentoPorEmpresa:fat_empresa
RelatorioDeDebitos:debitos
RelatorioDeDevolucaoPorCliente:devolucao_cliente
RelatorioDePedidos:pedidos_produto"

DATE_START=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date +%Y-%m-01)
DATE_END=$(date +%Y-%m-%d)

for LINE in $REPORTS; do
  TIPO="${LINE%%:*}"
  SHORT="${LINE##*:}"
  for EMP in "12:cwb" "13:vv"; do
    EMP_ID="${EMP%%:*}"
    EMP_SHORT="${EMP##*:}"
    FILE="${SHORT}_${EMP_SHORT}_all_$(date +%Y-%m-%d)_0700.xlsx"
    
    RT=$(curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" "http://saleshunter.vitao.com.br/relatorios" -o - | \
      grep -oP 'name="_token"[^>]*value="\K[^"]+' | head -1)
    
    HTTP=$(curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
      -d "_token=${RT}&tipo_relatorio=${TIPO}&empresa_faturamento%5B%5D=${EMP_ID}&data_inicial=${DATE_START}&data_final=${DATE_END}" \
      "http://saleshunter.vitao.com.br/relatorios/gerar/excel" \
      -o "${OUTDIR}/${FILE}" -w "%{http_code}")
    
    SZ=$(wc -c < "${OUTDIR}/${FILE}" 2>/dev/null || echo 0)
    if [ "$HTTP" != "200" ] || [ "$SZ" -lt 500 ]; then
      rm -f "${OUTDIR}/${FILE}"
      echo "FAIL: ${FILE} (HTTP=${HTTP})"
    else
      echo "OK: ${FILE} (${SZ}b)"
    fi
    sleep 1
  done
done

rm -f "$COOKIE_JAR"
```

---

## Classificação: REAL (Tier 1)

Todos os dados do Sales Hunter são **Tier REAL** — vêm direto do SAP.
NUNCA misturar com dados SINTÉTICOS ou ALUCINAÇÃO.
