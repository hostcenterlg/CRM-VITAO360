# SPEC ONDA 1A — Deploy Canal Scoping + Classificação + Canal DIGITAL

> Spec para VSCode executar. Prioridade MÁXIMA — sem isso o CRM não funciona.
> Gerado: 26/Abr/2026 | Autor: Cowork (professor/revisor)
> DECISÃO L3: Leandro aprovou multi-canal em 25/Abr/2026

---

## CONTEXTO

O VSCode criou 30 commits locais de canal scoping (master ahead of origin).
PROD Neon ainda está na versão antiga. Este spec cobre o deploy completo.

### Estado Atual
- 30 commits locais (canal scoping + Sales Hunter ingest)
- PROD Neon: sem migrations de canal, sem tabelas canal/usuario_canal
- PROD Vercel: frontend com hotfix null-checks (PR #1 mergeado)
- 2.736 clientes com canal_id = NULL (legado Mercos)
- 4.848 clientes com canal "DIGITAL" (origem desconhecida no SAP)
- verify.py 10/10 PASS local

---

## TASK 1: Resolver Canal DIGITAL (ANTES de deploy)

### Problema
O Sales Hunter trouxe `canal_venda` do SAP que inclui "DIGITAL" — não mapeado nos 6 canais originais.

### Canais Conhecidos (DECISÃO L3)
| # | Canal | Status CRM | Quem usa |
|---|-------|-----------|----------|
| 1 | INTERNO | ATIVO | Daiane (gerente) |
| 2 | FOOD_SERVICE | ATIVO | Daiane (gerente) |
| 3 | DIRETO | VISÍVEL | Manu, Larissa, Julio |
| 4 | INDIRETO | EM_BREVE | — |
| 5 | FARMA | EM_BREVE | — |
| 6 | BODY | EM_BREVE | — |

### Solução para DIGITAL

**HIPÓTESE MAIS PROVÁVEL:** "DIGITAL" = E-commerce/marketplace da VITAO. Verificar no SAP:
- O campo `canal_venda` no fat_cliente tem formato "31 - IN - DISTR. VAREJO"
- "DIGITAL" provavelmente é algo como "11 - E-COMMERCE" ou "12 - MARKETPLACE"
- Clientes DIGITAL provavelmente NÃO têm vendedor atribuído (venda direta online)

**AÇÃO DO VSCOODE:**

```python
# scripts/audit_canal_digital.py
# 1. Consultar quantos clientes têm canal DIGITAL
# 2. Listar os top 20 por faturamento
# 3. Verificar se têm consultor atribuído
# 4. Verificar se existem no Mercos/Deskrio

SELECT canal, COUNT(*) as qt, SUM(faturamento_total) as fat
FROM clientes
WHERE canal IS NOT NULL
GROUP BY canal
ORDER BY fat DESC;

-- Detalhe do DIGITAL:
SELECT cnpj, nome_fantasia, consultor, faturamento_total, tipo_cliente
FROM clientes
WHERE canal = 'DIGITAL'
ORDER BY faturamento_total DESC
LIMIT 20;
```

**DECISÃO PENDENTE (Leandro):** Se DIGITAL = E-commerce:
- Opção A: Criar canal 7 "DIGITAL" com status EM_BREVE
- Opção B: Mapear DIGITAL → DIRETO (se são vendas diretas ao consumidor)
- Opção C: Ignorar por enquanto (manter no banco mas sem canal_id no CRM)

**RECOMENDAÇÃO:** Opção A — criar como EM_BREVE. Dados ficam no banco, filtrados do CRM ativo, mas prontos pra quando quiser ativar. O script de seed já cria canais, basta adicionar uma linha.

---

## TASK 2: Classificar 2.736 Clientes NULL Canal

### Script existente: `scripts/classificar_clientes_legado.py`
O VSCode já criou este script. Lógica:
- MANU/LARISSA/JULIO → canal DIRETO (id=3)
- DAIANE → NÃO reclassifica automaticamente (pode ser INTERNO ou FOOD)
- WHERE canal_id IS NULL (idempotente)

### O que falta:
1. **Dry-run primeiro** — conferir os números antes de persistir
2. **Clientes da DAIANE** — precisam de lógica adicional:

```python
# Heurística para Daiane:
# Se tipo_cliente contém "FOOD" ou "ALIMENT" → FOOD_SERVICE (id=2)
# Se tipo_cliente contém "INTERN" ou rede_regional em lista interna → INTERNO (id=1)
# Se nenhum match → INTERNO (default, Daiane gerencia INTERNO primariamente)

DAIANE_FOOD_KEYWORDS = ['FOOD', 'RESTAUR', 'BUFFET', 'LANCHE', 'PADARIA']
DAIANE_INTERNO_DEFAULT = True  # fallback
```

3. **Clientes sem consultor** — não tem DE-PARA possível:

```python
# Sem consultor E sem canal → classificar como "NÃO_CLASSIFICADO"
# Criar registro em tabela de auditoria para review manual
# NÃO atribuir canal aleatoriamente (R8 — não inventar)
```

### Validação pós-classificação

```sql
-- DEVE retornar 0 (nenhum NULL restante entre clientes com consultor)
SELECT COUNT(*) FROM clientes
WHERE canal_id IS NULL AND consultor IS NOT NULL;

-- Distribuição esperada (verificar sanidade)
SELECT c.nome as canal, COUNT(*) as qt
FROM clientes cl JOIN canais c ON cl.canal_id = c.id
GROUP BY c.nome ORDER BY qt DESC;

-- Cross-check: faturamento DIRETO ≈ R$ 2.091.000 (baseline)
SELECT SUM(faturamento_total) FROM clientes
WHERE canal_id = 3;  -- DIRETO
-- Tolerância: ±0.5% do baseline
```

---

## TASK 3: Rebase + Deploy PROD Neon

### Pré-requisitos (TODOS devem ser TRUE)
- [ ] Canal DIGITAL resolvido (Task 1)
- [ ] Clientes NULL classificados (Task 2)
- [ ] verify.py 10/10 PASS
- [ ] Leandro aprovou deploy

### Sequência de Deploy

```bash
# PASSO 1: Alinhar com origin (PR #1 merge criou divergência)
git fetch origin master
git rebase origin/master
# Git deve skipar o cherry-pick duplicado (008e96b ≡ 1000a38)
# Se conflito: resolver mantendo a versão local (mais completa)

# PASSO 2: Verificar integridade pós-rebase
python scripts/verify.py --all
# 10/10 PASS obrigatório

# PASSO 3: Push para origin (REQUER APROVAÇÃO LEANDRO)
git push origin master

# PASSO 4: Migrations no Neon (3 migrations pendentes)
# Configurar DATABASE_URL para Neon PROD
export DATABASE_URL="postgresql://..."
alembic upgrade head
# Verificar que tabelas canais, usuario_canal, debitos_clientes existem

# PASSO 5: Seed canais (7 canais + DIGITAL se aprovado)
# NOTA: NÃO existe seed_canais.py separado.
# Os canais são seedados via migration Alembic (INSERT na migration de canal)
# OU via seed_usuario_canal.py que cria canais + ACLs juntos.
# Verificar: SELECT * FROM canais; — deve retornar 6-7 registros
python scripts/seed_usuario_canal.py  # cria ACLs (canais já existem via migration)

# PASSO 6: Ingest Sales Hunter em PROD
python scripts/ingest_sales_hunter.py
# Esperar ~5 min (processa 13 XLSX, ~10MB)
# Verificar output: X clientes, Y vendas, Z produtos

# PASSO 7: Classificar legado em PROD
python scripts/classificar_clientes_legado.py --dry-run
# Conferir números
python scripts/classificar_clientes_legado.py
# Persistir

# PASSO 8: Seed usuario_canal em PROD
python scripts/seed_usuario_canal.py

# PASSO 9: Validação final PROD
python scripts/verify.py --all
# Testar endpoints via curl:
curl -H "Authorization: Bearer $TOKEN" https://api.../api/dashboard/kpis
# Confirmar: faturamento DIRETO ≈ R$ 2.091.000
```

### Rollback Plan
Se algo der errado no Neon:
1. `alembic downgrade -1` (desfaz última migration)
2. Frontend continua funcionando (null-checks já aplicados)
3. Backend API retorna dados sem filtro de canal (fallback seguro)

---

## TASK 4: Scoping Restante (5 routers)

### Prioridade por risco de vazamento

| Router | Risco | Motivo |
|--------|-------|--------|
| routes_relatorios | ALTO | Exporta Excel com dados consolidados |
| routes_whatsapp | MÉDIO | Consulta Deskrio por CNPJ |
| routes_pipeline | MÉDIO | Notificações com CNPJ |
| routes_ia | BAIXO | Recebe CNPJ como input |
| 16 dashboard endpoints | BAIXO | Maioria são agregados globais |

### Padrão a aplicar (mesmo dos routers já feitos)

```python
# Em cada router:
# 1. Import deps
from backend.app.api.deps import (
    cliente_canal_filter,
    cnpjs_permitidos_subquery,
    get_current_user,
    get_user_canal_ids,
)

# 2. Adicionar dependency na função
user_canal_ids: list[int] | None = Depends(get_user_canal_ids),

# 3. Aplicar filtro
cnpjs_sub = cnpjs_permitidos_subquery(user_canal_ids)
if cnpjs_sub is not None:
    query = query.filter(Model.cnpj.in_(cnpjs_sub))

# 4. Carteira consultor
if user.role in ("consultor", "consultor_externo") and user.consultor_nome:
    query = query.filter(Model.consultor == user.consultor_nome.upper())
```

### DECISÃO PENDENTE — routes_relatorios

**Pergunta para Leandro:** Quando gerente exporta Excel:
- (a) Filtrado pelo canal selecionado? (recomendado)
- (b) Todos os canais que ela tem acesso?
- (c) Cabeçalho indica qual canal?

**Recomendação:** (a) + (c) — exporta filtrado pelo canal ativo, com cabeçalho "Canal: INTERNO | Período: Abr/2026".

---

## VALIDAÇÃO FINAL (Detector de Mentira)

### Nível 1 — Existência
- [ ] Tabelas canais e usuario_canal existem no Neon
- [ ] Seed canais populou 7 registros
- [ ] Seed usuario_canal populou ACLs corretas

### Nível 2 — Substância
- [ ] 0 clientes com canal_id NULL (exceto sem consultor)
- [ ] Faturamento canal DIRETO ≈ R$ 2.091.000 (±0.5%)
- [ ] Two-Base respeitada em todos dados importados
- [ ] CNPJ 14 dígitos string em todos registros

### Nível 3 — Conexão
- [ ] /api/clientes retorna dados filtrados por canal
- [ ] /api/vendas respeita canal scoping
- [ ] /api/dashboard/kpis mostra faturamento do canal do usuário
- [ ] Admin vê tudo, consultor vê só seus dados
- [ ] 403 quando consultor tenta acessar canal não-autorizado

---

*Spec revisada e aprovada pelo Cowork. VSCode executa na ordem: Task 1 → 2 → 3 → 4.*
