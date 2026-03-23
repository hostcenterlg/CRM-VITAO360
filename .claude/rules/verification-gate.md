# Verification Gate — CRM VITAO360
## SEVERIDADE: NON-NEGOTIABLE

---

## REGRA 1 — SESSION BOOT OBRIGATÓRIO
```bash
python scripts/session_boot.py
```
Se falhar → PARE. NÃO prossiga.

## REGRA 2 — VERIFY ANTES DE "DONE"
```bash
python scripts/verify.py --all
```
Se QUALQUER check FAIL → NÃO é "done". Corrigir primeiro.

## REGRA 3 — TWO-BASE CHECK ANTES DE QUALQUER CÁLCULO
Todo código que toca valores monetários DEVE:
1. Separar VENDA de LOG
2. R$ APENAS em VENDA
3. LOG = R$ 0.00 SEMPRE

## REGRA 4 — CNPJ NORMALIZAÇÃO
Todo código que manipula CNPJ DEVE:
1. Converter para string
2. Remover caracteres não-numéricos
3. Zero-pad para 14 dígitos
4. NUNCA armazenar como float/int

## REGRA 5 — FÓRMULA LANGUAGE CHECK
Antes de commit com fórmulas openpyxl:
- Verificar TODAS são em inglês (IF, VLOOKUP, SUMIF)
- Verificar separador é vírgula (,)
- NENHUMA em português

## REGRA 6 — FATURAMENTO VALIDATION
Após qualquer build que toque valores:
- Somar faturamento total
- Comparar com R$ 2.091.000
- Se divergência > 0.5% → PARAR e investigar

## REGRA 7 — POST-BUILD VALIDATION
Após qualquer build de Excel:
1. 0 erros de fórmula (#REF!, #DIV/0!, #VALUE!, #NAME?)
2. Two-Base respeitada
3. CNPJ sem duplicatas
4. 14 abas presentes
5. Testar no Excel real

## REGRA 8 — NUNCA INTEGRAR ALUCINAÇÃO
- 558 registros classificados como ALUCINAÇÃO
- Classificação 3-tier obrigatória: REAL / SINTÉTICO / ALUCINAÇÃO
- Dados não classificados = SUSPEITOS

---

## CONSEQUÊNCIAS
| Violação | Ação |
|----------|------|
| Sem session_boot | Sessão SUSPEITA |
| "Done" sem verify | REVERTER claim |
| Two-Base violada | BLOQUEAR commit |
| CNPJ como float | CORRIGIR imediatamente |
| Dados fabricados | DELETAR |
| Fórmula em português | CORRIGIR |
