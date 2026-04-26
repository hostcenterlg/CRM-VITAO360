# PLANO 12H — CRM VITAO360 SaaS Funcional

> Objetivo: em 12 horas de trabalho VSCode, ter um CRM que a equipe usa de verdade.
> Gerado: 26/Abr/2026 | Autor: Cowork (professor/revisor)
> Estado de entrada: 30 commits canal scoping local, PROD Neon em HOLD, verify 10/10

---

## DEFINIÇÃO DE "FUNCIONAL"

Ao final das 12h, o CRM deve:
1. Mostrar dados reais e atualizados (SAP + Deskrio + Mercos)
2. Cada vendedor vê APENAS seus clientes e canal
3. Admin gerencia quem vê o quê
4. Dados se atualizam sozinhos todo dia
5. Todas as páginas abrem sem erro

NÃO é objetivo das 12h: WhatsApp integrado, Pipeline de Produtos, IA avançada, mobile.

---

## ESTADO DE ENTRADA (26/Abr/2026 — números reais)

| Métrica | Valor |
|---------|-------|
| Commits locais ahead | 30 (canal scoping + Sales Hunter) |
| Clientes no banco | 8.164 |
| Clientes DIRETO | 2.883 |
| Clientes DIGITAL | 4.848 (origem SAP, a resolver) |
| Clientes NULL canal | 278 (legado Mercos, reduzido de 2.736) |
| Clientes INTERNO | 62 |
| Clientes FOOD_SERVICE | 29 |
| Vendas | 6.944 (5.711 SAP + 1.233 Mercos) |
| Atendimentos | 21.345 |
| Routers com scoping | 9 de 13 |
| verify.py | 10/10 PASS |
| PROD Neon | Em HOLD |
| PROD Vercel frontend | Atualizado (PR #1 hotfix) |

---

## 6 BLOCOS DE 2H (sequência obrigatória)

### BLOCO 1 (0h-2h): AUDITORIA + CANAL DIGITAL
> Spec: SPEC_ONDA1_DEPLOY_CANAIS.md — Task 1

**Objetivo:** Entender exatamente o que é DIGITAL e decidir o que fazer.

```
Sessão VSCode:
1. Boot (session_boot + compliance_gate)
2. Rodar audit_canal_digital (query SQL no banco local):
   - SELECT canal, COUNT(*), SUM(faturamento_total) FROM clientes GROUP BY canal
   - Detalhar DIGITAL: top 20 por faturamento, ver se tem consultor
   - Verificar tipo_cliente dos DIGITAL (ecommerce? marketplace?)
3. Reportar para Leandro: "DIGITAL = [X]. Recomendo [A/B/C]."
4. Classificar 278 clientes NULL restantes (script já existe)
   - python scripts/classificar_clientes_legado.py --dry-run
   - Conferir números
   - python scripts/classificar_clientes_legado.py
5. Verificar faturamento DIRETO vs baseline R$ 2.091.000
   - Se R$ 5.26M (como reportado): investigar — período acumulado SAP?
   - Provavelmente DIRETO inclui acumulado de vários meses
   - Baseline é faturamento ANUAL 2025, SAP pode ser lifetime
```

**Entregável:** Relatório canal DIGITAL + decisão + 0 clientes NULL.

**ALERTA FATURAMENTO:** O VSCode reportou DIRETO = R$ 5.26M, mas baseline é R$ 2.091M.
Diferença de R$ 3.17M. Possíveis causas:
- SAP fat_cliente.total_faturado = acumulado 2025+2026 (não só 2025)
- CWB + VV somados duplicaram algum CNPJ
- Período do relatório Sales Hunter ≠ período do baseline

**OBRIGATÓRIO investigar antes de deploy.** Se faturamento DIRETO ≠ baseline ±0.5%, NÃO deployar.

---

### BLOCO 2 (2h-4h): DEPLOY PROD NEON
> Spec: SPEC_ONDA1_DEPLOY_CANAIS.md — Task 3

**Pré-requisitos (TODOS devem ser TRUE):**
- [x] Canal DIGITAL resolvido (Bloco 1)
- [x] Clientes NULL classificados (Bloco 1)
- [ ] Faturamento DIRETO auditado e explicado
- [ ] Leandro aprovou

```
Sessão VSCode:
1. git fetch origin master && git rebase origin/master
   (skipar cherry-pick duplicado do PR #1)
2. python scripts/verify.py --all (10/10 obrigatório pós-rebase)
3. git push origin master (REQUER APROVAÇÃO LEANDRO)
4. Configurar DATABASE_URL para Neon PROD
5. alembic upgrade head (3 migrations: canal, usuario_canal, debitos)
6. Verificar canais seedados: SELECT * FROM canais; (devem existir 6-7 via migration)
7. python scripts/ingest_sales_hunter.py (em PROD)
8. python scripts/classificar_clientes_legado.py (em PROD)
9. python scripts/seed_usuario_canal.py (ACLs)
10. python scripts/verify.py --all (PROD)
11. Testar endpoints PROD com curl (3 perfis: admin, gerente, consultor)
12. Abrir https://intelligent-crm360.vercel.app e testar cada página
```

**Entregável:** PROD Neon funcionando com dados reais e canal scoping.

---

### BLOCO 3 (4h-6h): SCOPING RESTANTE + BACKFILL DESKRIO
> Specs: SPEC_ONDA1_DEPLOY_CANAIS.md Task 4 + SPEC_ONDA1_INGESTAO_DESKRIO.md

```
Sessão VSCode:
1. Scoping nos 4 routers restantes (relatorios, whatsapp, pipeline, ia)
   - 1 commit por router (R11 — atômico)
   - Testar com 3 perfis
2. Scoping nos endpoints de dashboard restantes (priorizar: distribuicao, funil, evolucao)
3. Backfill Deskrio (24 dias de JSONs → banco PROD):
   - Rodar sync_deskrio_to_db.py para cada dia
   - Validar Two-Base (0 logs com R$)
   - Validar CNPJ (14 dígitos, sem duplicatas)
4. Recalc scores: python scripts/recalc_score_batch.py
5. verify.py --all
```

**Entregável:** 100% routers com scoping + atendimentos Deskrio no banco.

---

### BLOCO 4 (6h-8h): SELETOR DE CANAL FRONTEND + ADMIN
> Spec: SPEC_ONDA2_FRONTEND_ADMIN.md

```
Sessão VSCode:
1. Criar CanalSelector.tsx no header
   - GET /api/canais/meus para listar canais do user
   - Dropdown com badge colorido
   - Admin vê "Todos" + lista
   - Consultor vê apenas liberados
2. Criar CanalContext (React context)
   - Propaga canal_id selecionado para todas as pages
   - Cada fetch inclui ?canal_id=X
3. Backend: adaptar get_user_canal_ids para aceitar query param canal_id
   - Se canal_id presente E está nos canais do user → filtrar só por ele
   - Se ausente → filtrar por todos os canais do user (comportamento atual)
4. Testar troca de canal (Daiane: INTERNO ↔ FOOD_SERVICE)
5. PUT /api/usuarios/{id}/canais (admin endpoint)
6. UI admin: checkboxes de canais na tela de edição de usuário
```

**Entregável:** Seletor de canal funcional + admin pode gerenciar permissões.

---

### BLOCO 5 (8h-10h): PIPELINE AUTOMÁTICO + CI/CD
> Spec: SPEC_ONDA1_PIPELINE_AUTOMATICO.md

```
Sessão VSCode:
1. Criar scripts/download_sales_hunter.py
   - Automatiza download dos 13 XLSX via curl
   - Auth Sales Hunter (login → token → download)
   - Salva em data/sales_hunter/{YYYY-MM-DD}/morning/
2. Criar .github/workflows/daily-pipeline.yml
   - Cron: 07:00 BRT (10:00 UTC), Seg-Sex
   - Steps: snapshot → download → ingest → sync → recalc → verify
   - Secrets: DATABASE_URL_NEON, DESKRIO_TOKEN, SALES_HUNTER credentials
3. Configurar secrets no GitHub repo
4. Testar manualmente (workflow_dispatch)
5. Fix CI: adicionar pytest ao requirements.txt do workflow
   - Backend Tests falhando por "No module named pytest"
   - Fix simples: pip install pytest no workflow
```

**Entregável:** Pipeline roda sozinho todo dia. CI não falha mais.

---

### BLOCO 6 (10h-12h): POLISH + TESTE INTEGRADO + DOCUMENTAÇÃO
> Objetivo: garantir que TUDO funciona junto

```
Sessão VSCode:
1. Teste integrado end-to-end:
   - Login como admin → ver Dashboard com todos canais
   - Login como MANU → ver apenas DIRETO
   - Login como DAIANE → ver INTERNO + FOOD, trocar entre eles
   - Cada página: Carteira, Agenda, Sinaleiro, Vendas, Atendimentos, IA
   - Exportar relatório Excel → confirmar cabeçalho com canal
   - Abrir cada página SEM erro

2. Fix de bugs encontrados nos testes (buffer de 1h)

3. Rodar verify.py --all em PROD (deve ser 10/10)

4. Validação de faturamento final:
   - Admin total: R$ 14.5M (todos canais SAP)
   - DIRETO: investigado e explicado no Bloco 1
   - INTERNO + FOOD: ≈ R$ 2.0M (Daiane)
   - Baseline R$ 2.091.000 = canal DIRETO ou INTERNO? Resolver.

5. Atualizar CLAUDE.md e docs:
   - Estado final: % completude atualizado
   - Canais implementados e seedados
   - Pipeline automático configurado
   - Próximos passos (Onda 3: Produtos, WhatsApp, IA)
```

**Entregável:** CRM funcionando em perfeito estado. Equipe pode usar segunda-feira.

---

## CHECKPOINT DE SUCESSO (12h)

| Critério | Target |
|----------|--------|
| Páginas sem erro | 22/22 |
| Routers com scoping | 13/13 |
| verify.py PROD | 10/10 PASS |
| Pipeline automático | Rodando via GitHub Actions |
| Seletor de canal | Funcional no header |
| Admin canais | Funcional |
| Dados Deskrio no banco | 24 dias backfilled |
| CI/CD | Backend Tests PASS |
| Faturamento auditado | Baseline explicado e documentado |

---

## PROMPT PARA INICIAR CADA BLOCO NO VSCODE

### Bloco 1:
```
@aios-master
Lê PLANO_12H_SAAS_FUNCIONAL.md — Bloco 1.
Specs de referência: SPEC_ONDA1_DEPLOY_CANAIS.md
Missão: Auditar canal DIGITAL + classificar NULL + auditar faturamento DIRETO.
Começar com queries SQL no banco local.
```

### Bloco 2:
```
@aios-master
Lê PLANO_12H_SAAS_FUNCIONAL.md — Bloco 2.
Specs de referência: SPEC_ONDA1_DEPLOY_CANAIS.md Task 3
Missão: Deploy PROD Neon. ATENÇÃO: conferir que faturamento foi auditado no Bloco 1.
```

### Bloco 3:
```
@aios-master
Lê PLANO_12H_SAAS_FUNCIONAL.md — Bloco 3.
Specs: SPEC_ONDA1_DEPLOY_CANAIS.md Task 4 + SPEC_ONDA1_INGESTAO_DESKRIO.md
Missão: Scoping 4 routers + backfill Deskrio 24 dias em PROD.
```

### Bloco 4:
```
@aios-master
Lê PLANO_12H_SAAS_FUNCIONAL.md — Bloco 4.
Spec: SPEC_ONDA2_FRONTEND_ADMIN.md
Missão: CanalSelector no header + admin endpoint + testar.
```

### Bloco 5:
```
@aios-master
Lê PLANO_12H_SAAS_FUNCIONAL.md — Bloco 5.
Spec: SPEC_ONDA1_PIPELINE_AUTOMATICO.md
Missão: download_sales_hunter.py + GitHub Actions workflow + fix CI.
```

### Bloco 6:
```
@aios-master
Lê PLANO_12H_SAAS_FUNCIONAL.md — Bloco 6.
Missão: Teste end-to-end + fix bugs + documentar estado final.
verify.py --all PROD obrigatório antes de declarar done.
```

---

## RISCOS CONHECIDOS

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Faturamento DIRETO ≠ baseline | ALTA | BLOQUEIA deploy | Auditar no Bloco 1 ANTES de tudo |
| Rebase com conflito | MÉDIA | Atrasa 30min | Resolver mantendo versão local |
| Neon migration falha | BAIXA | Atrasa 1h | alembic downgrade + corrigir + retry |
| Sales Hunter API muda | BAIXA | Atrasa pipeline | Manter download manual como fallback |
| Token Deskrio expira | MUITO BAIXA | Para sync | Renovar via API (processo documentado) |

---

## NOTA SOBRE FATURAMENTO (ALERTA AMARELO)

O VSCode reportou DIRETO = R$ 5.26M. Baseline = R$ 2.091M. Diferença = R$ 3.17M.

**Hipóteses (investigar no Bloco 1):**
1. fat_cliente.total_faturado = acumulado multi-ano (não só 2025)
2. CWB + VV duplicaram CNPJs presentes em ambas filiais
3. Relatório Sales Hunter cobre período diferente do baseline
4. Canal DIRETO no SAP inclui subcategorias que não estavam no Mercos

**REGRA:** NÃO deployar com faturamento inexplicado. Auditar primeiro.

---

*Plano aprovado pelo Cowork. 12h, 6 blocos, sequência obrigatória. Boa sorte.*
