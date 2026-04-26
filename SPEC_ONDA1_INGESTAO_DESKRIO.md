# SPEC ONDA 1C — Ingestão Deskrio → Banco (Backfill 24 Dias)

> 15.632 contatos + 445 tickets acumulados em JSON sem entrar no banco.
> Gerado: 26/Abr/2026 | Autor: Cowork (professor/revisor)

---

## CONTEXTO

### O que JÁ existe (não refazer)
- `scripts/sync_deskrio_to_db.py` — script completo de sync (já lê JSONs, já faz upsert)
- `scripts/deskrio_daily_snapshot.py` — extrai dados da API Deskrio diariamente
- `data/deskrio/cnpj_bridge.json` — mapeamento contactId → CNPJ (verificado via API)
- 24 dias de dados em `data/deskrio/YYYY-MM-DD/` (contacts, tickets, kanban)
- Token Deskrio válido até Set/2028

### O que FALTA
1. **Executar sync_deskrio_to_db.py no banco PROD** (Neon) — nunca rodou em PROD
2. **Backfill dos 24 dias acumulados** (não apenas o dia mais recente)
3. **Verificar integridade** pós-sync (Two-Base, CNPJ, duplicatas)

---

## TASK 1: Backfill 24 Dias de Deskrio

### Dados acumulados (verificado 15/Abr/2026)
| Dado | Volume | Onde |
|------|--------|------|
| Contatos WhatsApp | 15.632 | data/deskrio/*/contacts.json |
| Tickets atendimento | 445+ | data/deskrio/*/tickets.json |
| Kanban cards board 20 | ~50 | data/deskrio/*/kanban_cards_20.json |
| Kanban cards board 100 | ~30 | data/deskrio/*/kanban_cards_100.json |
| CNPJ bridge | ~600 mappings | data/deskrio/cnpj_bridge.json |

### Comando de backfill

```bash
# O sync_deskrio_to_db.py já suporta --data-dir para processar dia específico.
# Para backfill completo de todos os 24 dias:

# Opção 1: Rodar para cada dia (mais seguro, logs por dia)
for dir in data/deskrio/2026-04-*/; do
    echo "=== Processando $dir ==="
    python scripts/sync_deskrio_to_db.py --data-dir "$dir"
done

# Opção 2: Rodar sem --data-dir (pega o dia mais recente automaticamente)
# INSUFICIENTE para backfill — usar Opção 1

# Opção 3: Criar script wrapper
python scripts/backfill_deskrio.py  # Já existe! Verificar se faz o backfill completo.
```

### Regras TWO-BASE para Deskrio
- **Contatos** → tabela `clientes` (upsert por CNPJ) — SEM valor R$
- **Tickets** → tabela `log_interacoes` — **NUNCA R$, SEMPRE R$ 0.00**
- **Kanban cards** → campo `estagio_funil` em clientes — SEM valor R$

### CNPJ Bridge
O CNPJ não vem direto no JSON do Deskrio. O mapeamento é:
1. Contact tem `id` e `extrainfo` com campos customizados
2. `cnpj_bridge.json` mapeia `contactId → cnpj`
3. Contatos SEM CNPJ no bridge = **SKIP** (R8 — não inventar)
4. Quantidade esperada com CNPJ: ~600 de 15.632 (~4%)
5. Os outros 15.000 são leads WhatsApp sem empresa (CPF, pessoa física, etc.)

---

## TASK 2: Verificação Pós-Sync

### Queries de validação

```sql
-- 1. Contagem de log_interacoes com fonte Deskrio
SELECT COUNT(*) FROM log_interacoes WHERE fonte = 'DESKRIO';
-- Esperado: > 0 (proporcional aos tickets com CNPJ resolvido)

-- 2. Two-Base: NENHUM log com valor monetário
SELECT COUNT(*) FROM log_interacoes
WHERE valor IS NOT NULL AND valor > 0;
-- DEVE ser 0. Se > 0 → Two-Base VIOLADA → BLOQUEAR

-- 3. CNPJ normalizados (14 dígitos string)
SELECT cnpj, LENGTH(cnpj) FROM clientes
WHERE fonte = 'DESKRIO' AND LENGTH(cnpj) != 14;
-- DEVE ser 0

-- 4. Sem duplicatas de CNPJ
SELECT cnpj, COUNT(*) as qt FROM clientes
GROUP BY cnpj HAVING COUNT(*) > 1;
-- DEVE ser 0 (upsert garante)

-- 5. Classificação 3-tier
SELECT classificacao_3tier, COUNT(*) FROM clientes
WHERE fonte = 'DESKRIO'
GROUP BY classificacao_3tier;
-- Todos devem ser 'REAL' (dados vêm de API verificada)
```

---

## TASK 3: Integrar com Pipeline Diário

O `daily_pipeline.py` já chama `sync_deskrio_to_db.py` como etapa 3 ("ingest").
Após o backfill inicial, o pipeline diário mantém os dados frescos.

### Dependência de ordem no pipeline
```
1. snapshot (extrai Deskrio API → JSON do dia)
2. sales_hunter (processa XLSX SAP → banco)
3. ingest (sync_deskrio_to_db → usa JSONs do snapshot)  ← ESTE
4. recalc (recalcula scores usando dados atualizados)
```

A ordem é importante: Sales Hunter roda ANTES do Deskrio porque o Deskrio
precisa cruzar CNPJ com clientes que já existem no banco (vindos do SAP).

---

## RISCOS E MITIGAÇÕES

| Risco | Mitigação |
|-------|-----------|
| CNPJ bridge incompleto (~4% coverage) | Aceitar — leads WA sem CNPJ são prospects, não clientes ativos |
| Token Deskrio expirar | Já válido até Set/2028 — alertar 30 dias antes |
| Duplicar atendimentos no backfill | sync_deskrio_to_db.py é idempotente (upsert por ticket_id) |
| Two-Base violada por tickets com valor | sync_deskrio_to_db.py já garante R$0.00 em logs |

---

## VALIDAÇÃO FINAL

### Nível 1 — Existência
- [ ] log_interacoes contém registros com fonte='DESKRIO'
- [ ] clientes atualizados com dados Deskrio (telefone WA, email)

### Nível 2 — Substância
- [ ] Two-Base: 0 logs com valor monetário
- [ ] CNPJ: todos 14 dígitos, string, sem duplicatas
- [ ] Classificação 3-tier: todos REAL

### Nível 3 — Conexão
- [ ] /api/atendimentos mostra histórico Deskrio
- [ ] Pipeline diário executa sync sem erro
- [ ] Dados Deskrio aparecem na timeline do cliente no frontend

---

*Spec revisada. VSCode executa: backfill_deskrio.py → validação → testar no frontend.*
