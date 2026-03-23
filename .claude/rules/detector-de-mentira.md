# DETECTOR DE MENTIRA — CRM VITAO360
# Baseado no verification-patterns do us-county-radar
# SEVERIDADE: BLOQUEANTE. Aplica em TODA verificação.

---

## CONCEITO CENTRAL

"Task completa" NÃO SIGNIFICA "objetivo alcançado".
- Arquivo criado ≠ funcionalidade entregue
- Script rodou ≠ dados corretos
- Fórmula escrita ≠ resultado esperado
- "Done" falado ≠ "Done" verificado

## 3 NÍVEIS DE VERIFICAÇÃO (OBRIGATÓRIOS)

### NÍVEL 1 — EXISTÊNCIA
O artefato existe no caminho esperado?

```python
# Verificar:
- [ ] Arquivo existe no path declarado
- [ ] Arquivo não está vazio (>0 bytes)
- [ ] Formato correto (xlsx, json, py, md)
- [ ] Pode ser aberto sem erro
```

### NÍVEL 2 — SUBSTÂNCIA (Anti-Stub)
O conteúdo é implementação REAL, não placeholder?

**Patterns de MENTIRA a detectar:**

```python
STUBS = [
    # Comentários de placeholder
    "TODO", "FIXME", "XXX", "HACK", "PLACEHOLDER",
    "coming soon", "lorem ipsum", "sample data",

    # Implementações vazias
    "return None", "return {}", "return []", "pass",
    "raise NotImplementedError",

    # Dados fabricados (REGRA R8)
    "teste", "exemplo", "dummy", "fake", "mock",
    "12345678000100",  # CNPJ genérico
    "00000000000000",  # CNPJ zerado

    # Valores hardcoded suspeitos
    "R$ 0,00" em registro tipo VENDA,  # Two-Base violada
    "R$ " em registro tipo LOG,         # Two-Base violada
]

ALUCINACAO = [
    # 558 registros catalogados (ChatGPT)
    # Qualquer dado sem rastreabilidade a Mercos/SAP/Deskrio
    # Valores impossíveis (faturamento > R$ 500K/mês por cliente)
    # CNPJs que não existem em nenhuma fonte
]
```

**Verificações de SUBSTÂNCIA para Excel:**
```
- [ ] Fórmulas retornam valores (não #REF!, #DIV/0!, #VALUE!, #NAME?)
- [ ] Dados vêm de fonte rastreável (Mercos, SAP, Deskrio, CONTROLE_FUNIL)
- [ ] Classificação 3-tier presente: REAL / SINTÉTICO / ALUCINAÇÃO
- [ ] CNPJ = string 14 dígitos (NUNCA float, NUNCA int)
- [ ] Fórmulas em INGLÊS (IF, VLOOKUP, SUMIF — NUNCA português)
- [ ] Two-Base respeitada (VENDA=R$, LOG=R$0.00)
```

**Verificações de SUBSTÂNCIA para Python:**
```
- [ ] Funções fazem o que dizem (não são stubs)
- [ ] Dados processados vêm de arquivo real (não hardcoded)
- [ ] Sem print("teste") ou debug esquecido
- [ ] Tratamento de erro real (não except: pass)
- [ ] Output salvo em path correto
```

### NÍVEL 3 — CONEXÃO (Wired)
O artefato está conectado ao resto do sistema?

```python
# Para Excel:
- [ ] Fórmulas referenciam abas que existem
- [ ] INDEX-MATCH bate com range real (não #REF!)
- [ ] XLOOKUP encontra dados (não "")
- [ ] Named Ranges apontam para células válidas
- [ ] Formatação condicional funciona
- [ ] Dropdowns alimentados por REGRAS

# Para Python:
- [ ] Import de módulos que existem
- [ ] Paths de arquivo que existem
- [ ] Output consumido por próximo script
- [ ] Integração com pipeline testada

# Para API:
- [ ] Endpoint responde (HTTP 200)
- [ ] Token válido (não expirado)
- [ ] Dados retornados batem com schema
- [ ] Parsing correto (JSON → DataFrame)
```

## VALIDAÇÃO DE DADOS — 3 TIERS

| Tier | Significado | Pode usar? |
|------|-------------|------------|
| **REAL** | Rastreável a Mercos, SAP, Deskrio ou PAINEL CEO | SIM |
| **SINTÉTICO** | Derivado de dados reais por fórmula | SIM (com flag) |
| **ALUCINAÇÃO** | ChatGPT fabricou, sem fonte | **NUNCA** |

### Como classificar:
1. Tem CNPJ que existe no Mercos ou SAP? → REAL
2. Foi calculado por fórmula a partir de dados REAL? → SINTÉTICO
3. Apareceu do nada, sem fonte? → ALUCINAÇÃO
4. Veio do CONTROLE_FUNIL ChatGPT? → Verificar nos 558 catalogados

## THRESHOLDS DE QUALIDADE

| Métrica | Mínimo | Ideal | Bloqueante se |
|---------|--------|-------|---------------|
| Fórmulas com erro | 0 | 0 | > 0 |
| Two-Base violações | 0 | 0 | > 0 |
| CNPJ como float | 0 | 0 | > 0 |
| Fórmulas em português | 0 | 0 | > 0 |
| Faturamento vs baseline | ±0.5% | ±0.1% | > 0.5% |
| Dados ALUCINAÇÃO integrados | 0 | 0 | > 0 |
| Abas presentes | 14+ | 14+ | < 14 |
| CNPJ duplicados | 0 | 0 | > 0 |
| Coverage clientes | >90% | 100% | < 80% |
| Coverage faturamento | >95% | 100% | < 90% |

## PROTOCOLO DE VERIFICAÇÃO

ANTES de declarar "done", "pronto", "completo", "OK":

```
1. NÍVEL 1: Verificar existência de TODOS os artefatos prometidos
2. NÍVEL 2: Rodar anti-stub em cada artefato
3. NÍVEL 3: Testar conexões entre artefatos
4. THRESHOLDS: Validar métricas contra limites
5. VERIFY.PY: Rodar python scripts/verify.py --all
6. DECLARAR: "Verificação 3 níveis: N1 OK, N2 OK, N3 OK. Thresholds: X/Y OK."
```

## CONSEQUÊNCIAS

| Violação | Ação |
|----------|------|
| "Done" sem verificação 3 níveis | REVERTER claim |
| Stub detectado como implementação | BLOQUEAR commit |
| Dado ALUCINAÇÃO integrado | DELETAR e alertar |
| Two-Base violada em produção | REVERTER + corrigir |
| Faturamento diverge >0.5% | PARAR e investigar |

---

*Este detector é AUTOMÁTICO. Carrega em toda verificação. Não existe "dessa vez pode pular".*
