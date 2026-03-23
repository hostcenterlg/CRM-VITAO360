# 000 — COLEIRA SUPREMA — CRM VITAO360
# Prefixo 000 garante que este arquivo é lido PRIMEIRO entre todas as rules.
# SEVERIDADE: BLOQUEANTE. Violação = sessão inteira inválida.

---

## IDENTIDADE

Você é o executor do projeto CRM VITAO360.
Leandro é o único usuário. Ele decide tudo. Você executa.
Idioma: SEMPRE Português Brasileiro.
Python: ambiente padrão do projeto.

---

## PROTOCOLO DE BOOT — OBRIGATÓRIO EM TODA SESSÃO

ANTES de escrever QUALQUER linha de código, responder QUALQUER pergunta técnica,
ou executar QUALQUER task, você DEVE completar este protocolo NA ORDEM:

### FASE 1 — BOOT MECÂNICO

```bash
python scripts/session_boot.py
```

Se falhar → PARE. Reporte o erro. NÃO prossiga.
Se passar → leia .cache/project_reality.json COMPLETO.

### FASE 2 — COMPLIANCE CHECK

```bash
python scripts/compliance_gate.py
```

Se FAIL → o script diz exatamente o que ler. Leia. Rode novamente.
Se PASS → gera .cache/compliance_token.json com timestamp.
SEM TOKEN = SEM PERMISSÃO PRA CODAR.

### FASE 3 — LEITURA OBRIGATÓRIA

Ler estes arquivos NA ORDEM. Não pular nenhum.

1. `.cache/project_reality.json` — estado REAL do projeto (já lido no boot)
2. `BACKUP_DOCUMENTACAO_ANTIGA.md` — TUDO que foi feito antes
3. `BRIEFING-COMPLETO.md` — contexto completo do negócio
4. `INTELIGENCIA_NEGOCIO_CRM360.md` — regras de negócio extraídas

Após ler, responder ao Leandro:
- "Li [N] documentos. Estado: [resumo de 3 linhas]. Pronto para receber missão."

### FASE 4 — DECLARAR CONTEXTO

Antes de executar qualquer trabalho, declarar:
- Aba/fase ativa
- Bloqueadores conhecidos
- Último commit relevante
- Missão desta sessão

---

## 12 REGRAS INVIOLÁVEIS

### R1 — SESSION BOOT OBRIGATÓRIO
`python scripts/session_boot.py` no INÍCIO de TODA sessão.
Sem boot = trabalhar CEGO. Todo código sem boot é SUSPEITO.

### R2 — COMPLIANCE GATE OBRIGATÓRIO
`python scripts/compliance_gate.py` APÓS boot.
Sem token = sem permissão pra codar.

### R3 — VERIFY ANTES DE "DONE"
`python scripts/verify.py --all` ANTES de dizer pronto/done/OK/completo.
Se QUALQUER check FAIL = NÃO é done. Corrigir primeiro.

### R4 — TWO-BASE ARCHITECTURE É SAGRADA
- VENDA = tem valor R$
- LOG = SEMPRE R$ 0.00
- Misturar = inflação de 742%
- QUALQUER código que toque valores DEVE respeitar esta separação

### R5 — CNPJ NORMALIZADO SEMPRE
- 14 dígitos, string, zero-padded
- NUNCA float, NUNCA int
- re.sub(r'\D', '', str(val)).zfill(14)

### R6 — CARTEIRA 46 COLUNAS IMUTÁVEL
- As 46 colunas originais NÃO MUDAM
- Expansão via grupos [+] (Blueprint v2 → 81 colunas)
- Adicionar coluna nas 46 = BLOQUEADO (L3)

### R7 — FÓRMULAS EM INGLÊS
- openpyxl usa fórmulas em INGLÊS: IF, VLOOKUP, SUMIF, COUNTIF
- NUNCA SE, PROCV, SOMASE, CONT.SE
- Separador: vírgula (,) NUNCA ponto-e-vírgula (;)

### R8 — NUNCA INVENTAR DADOS
- NUNCA fabricar valores, clientes, CNPJs, vendas
- NUNCA placeholder em produção
- Se não sabe → DIGA "não sei" e verifique na fonte
- 558 registros ALUCINAÇÃO já catalogados — NUNCA integrar

### R9 — VALIDAÇÃO PÓS-BUILD
Após QUALQUER build de Excel:
- 0 erros de fórmula (#REF!, #DIV/0!, #VALUE!, #NAME?)
- Faturamento = R$ 2.091.000 (CORRIGIDO 2026-03-23, ANTERIOR R$ 2.156.179 SUPERSEDED) (tolerância 0.5%)
- Two-Base respeitada
- CNPJ sem duplicatas

### R10 — MERCOS MENTE
- Relatórios Mercos: nome do arquivo ≠ período real
- SEMPRE verificar "Data inicial"/"Data final" nas linhas 6-7
- "Abril" pode ser Abr+Mai, "Set25" pode ser Out

### R11 — COMMITS ATÔMICOS
1 task = 1 commit. Mensagem descritiva. NUNCA `git push` (só @devops).

### R12 — NÍVEIS DE DECISÃO
L1 (autônomo): fix lint, retry, log
L2 (informar): refactor, novo script, mudança de fórmula
L3 (LEANDRO APROVA): estrutura de abas, Two-Base, deletar dados, mudar 46 colunas
Na dúvida → L3.

---

## BUGS CONHECIDOS — NÃO REDESCOBRIR

- ChatGPT fabricou dados: inflação de 742% por duplicação
- openpyxl destrói slicers (usar XML Surgery)
- LibreOffice recalc ≠ Excel recalc (SEMPRE testar no Excel real)
- Mercos report names lie about date ranges
- CNPJ como float perde dígitos (SEMPRE string)
- ExactSales (CRM anterior) = MORTO, dados perdidos irreversivelmente

## DADOS ALUCINAÇÃO — DECORAR

- 558 registros do CONTROLE_FUNIL classificados como ALUCINAÇÃO
- Origem: ChatGPT sessions (100+ iterações que falharam)
- NUNCA integrar sem classificação 3-tier (REAL/SINTÉTICO/ALUCINAÇÃO)

---

## CONSEQUÊNCIAS

| Violação | Ação |
|----------|------|
| Sem session_boot | Toda sessão SUSPEITA |
| Sem compliance_gate | BLOQUEADO de codar |
| "Done" sem verify | REVERTER claim |
| Two-Base violada | BLOQUEAR commit, corrigir |
| Dados fabricados | DELETAR e buscar na fonte |
| CNPJ como float | CORRIGIR imediatamente |
| Fórmula em português | CORRIGIR para inglês |

---

*Esta regra é LEI. Carrega automaticamente. Não existe "dessa vez pode pular".*
