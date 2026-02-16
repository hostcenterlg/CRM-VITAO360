# 🔍 EXTRAÇÃO SISTEMÁTICA - PROBLEMAS NOTEBOOKLM (COM COMITÊ)

**Data:** 16 Dezembro 2025  
**Metodologia:** Comitê de Conferência Ativo  
**Objetivo:** Extrair TODOS problemas documentados sem alucinação

---

## 📋 COMITÊ DE CONFERÊNCIA - REGRAS

### ANTES DE CADA RESPOSTA:

#### ✅ VERIFICAÇÃO 1: FONTE
- [ ] Arquivo específico identificado?
- [ ] Linha/seção anotada?
- [ ] Texto copiado LITERAL?

#### ✅ VERIFICAÇÃO 2: DADOS
- [ ] Número extraído diretamente?
- [ ] Data verificada?
- [ ] Nome do cliente correto?

#### ✅ VERIFICAÇÃO 3: INTERPRETAÇÃO
- [ ] É FATO ou OPINIÃO?
- [ ] Base nos dados apresentados?
- [ ] Há contradições?

#### 🚫 PROIBIDO ABSOLUTAMENTE:
- ❌ Inventar números "razoáveis"
- ❌ Criar exemplos fictícios
- ❌ Assumir padrões sem base
- ❌ Arredondar sem avisar

---

## 📁 ARQUIVOS DISPONÍVEIS (VERIFICADO)

### ARQUIVO 1: analise-whatsapp-dados-reais-vitao.txt
- **Tamanho:** 168.7 KB
- **Conteúdo:** Análise geral 77.640 mensagens WhatsApp
- **Dados esperados:** Volumetria, padrões, problemas gerais

### ARQUIVO 2: conversas-daiane-individuais-lote3-4.txt
- **Tamanho:** 8.6 KB
- **Conteúdo:** Conversas Daiane individuais
- **Dados esperados:** Casos específicos clientes

### ARQUIVO 3: analise-conversas-daiane-lote4-problemas-black-friday.txt
- **Tamanho:** 53.6 KB
- **Conteúdo:** PROBLEMAS BLACK FRIDAY
- **Dados esperados:** 26 casos graves documentados ⚠️ CRÍTICO

### ARQUIVO 4: analise-notebooklm-operacao-comercial-vitao.txt
- **Tamanho:** 8.7 KB
- **Conteúdo:** Operação comercial geral
- **Dados esperados:** Gargalos, métricas

### ARQUIVO 5: analise-notebooklm-atendimentos-dezembro-1-2.txt
- **Tamanho:** 13.2 KB
- **Conteúdo:** Atendimentos Dezembro
- **Dados esperados:** Problemas Dezembro

### ARQUIVO 6: analise-notebooklm-atendimento-vitao-interno-central.txt
- **Tamanho:** 11.4 KB
- **Conteúdo:** Atendimento interno
- **Dados esperados:** Conversas internas Daiane

### ARQUIVO 7: analise-notebooklm-daiane-atendimentos-coordenacao-interna.txt
- **Tamanho:** 10.0 KB
- **Conteúdo:** Coordenação interna Daiane
- **Dados esperados:** 3.500+ msgs coordenação

**TOTAL:** 274.2 KB de dados NotebookLM

---

## 🎯 PLANO DE EXTRAÇÃO (FASE A FASE)

### FASE 1: PROBLEMAS BLACK FRIDAY (PRIORIDADE MÁXIMA)
**Arquivo:** analise-conversas-daiane-lote4-problemas-black-friday.txt

**Objetivo:** Extrair LISTA COMPLETA dos 26 casos graves

**Dados a extrair:**
- [ ] Nome cliente (LITERAL do arquivo)
- [ ] Data exata do problema
- [ ] Tipo de problema (classificar depois)
- [ ] Descrição do problema (copiar literal)
- [ ] Resolução (se houver)
- [ ] Status atual (comprou depois? churn?)

**Método:**
1. Ler arquivo linha por linha
2. Identificar cada caso mencionado
3. Copiar informações LITERAIS
4. Não inferir nada
5. Se informação não está no arquivo, marcar como "NÃO DOCUMENTADO"

---

### FASE 2: PROBLEMAS OPERACIONAIS GERAIS
**Arquivos:** 
- analise-whatsapp-dados-reais-vitao.txt
- analise-notebooklm-operacao-comercial-vitao.txt

**Objetivo:** Identificar problemas operacionais recorrentes

**Dados a extrair:**
- [ ] Tipos de problema mencionados
- [ ] Frequência (se mencionada)
- [ ] Impacto (se mencionado)

---

### FASE 3: COORDENAÇÃO INTERNA DAIANE
**Arquivos:**
- analise-notebooklm-atendimento-vitao-interno-central.txt
- analise-notebooklm-daiane-atendimentos-coordenacao-interna.txt

**Objetivo:** Documentar problemas operacionais internos

**Dados a extrair:**
- [ ] Quantidade mensagens coordenação (3.500+?)
- [ ] Tipos de problema que Daiane resolve
- [ ] Tempo gasto em coordenação vs vendas

---

### FASE 4: CASOS INDIVIDUAIS
**Arquivo:** conversas-daiane-individuais-lote3-4.txt

**Objetivo:** Extrair casos específicos clientes

**Dados a extrair:**
- [ ] Lista clientes mencionados
- [ ] Problemas específicos cada um
- [ ] Resultado (continuou/churn)

---

## 📊 TEMPLATE EXTRAÇÃO (USAR PARA CADA CASO)

```
CASO #: [número sequencial]

FONTE:
- Arquivo: [nome exato]
- Seção/Linha: [onde está]

DADOS BRUTOS (LITERAL):
"[copiar texto exato do arquivo]"

DADOS ESTRUTURADOS:
- Cliente: [nome]
- Data: [DD/MM/AAAA]
- Problema: [tipo]
- Descrição: [resumo max 100 chars]
- Gravidade: [CRÍTICA/ALTA/MÉDIA/BAIXA]
- Resolução: [o que foi feito]
- Status: [ATIVO/CHURN/DESCONHECIDO]

VERIFICAÇÃO COMITÊ:
- [X] Cliente existe nos dados de vendas? [SIM/NÃO/A VERIFICAR]
- [X] Data compatível com timeline? [SIM/NÃO/A VERIFICAR]
- [X] Problema é novo ou duplicado? [NOVO/DUPLICADO]

CONFIANÇA: [100% / 80% / 60% / <60%]
```

---

## 🚀 EXECUÇÃO - COMEÇAR AGORA

**STATUS:** AGUARDANDO EXECUÇÃO

**PRÓXIMO PASSO:** 
1. Ler ARQUIVO 3 (Black Friday) linha por linha
2. Extrair cada caso usando template
3. Verificar com comitê
4. Documentar tudo
5. Apresentar resultados

---

**REGRA DE OURO:**
> "Se não está EXPLÍCITO no arquivo, NÃO EXISTE."
> "Melhor dizer 'não sei' que inventar."

---

## 📝 LOG DE EXECUÇÃO

### [TIMESTAMP] - INICIANDO FASE 1
- Arquivo alvo: analise-conversas-daiane-lote4-problemas-black-friday.txt
- Tamanho: 53.6 KB
- Linhas esperadas: ~427

### [PRÓXIMOS PASSOS]
- Ler arquivo completo
- Identificar cada caso
- Extrair dados
- Verificar
- Documentar

---

**Criado:** 16/Dez/2025  
**Status:** PRONTO PARA EXECUÇÃO  
**Aguardando:** Comando para começar
