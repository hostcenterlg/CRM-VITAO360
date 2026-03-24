# Auditoria Comparativa: CRM V13 vs V31

## Resumo Executivo

Este conjunto de ferramentas compara dois arquivos CRM para determinar qual contém dados mais confiáveis para uso em produção.

**Arquivos em análise:**
- **V13**: `CRM_VITAO360_V13_FINAL.xlsx` (~5.2 MB)
- **V31**: `CRM_V12_POPULADO_V31 (1).xlsx edição update.xlsx` (~14 MB)

**Objetivo**: Avaliar:
1. Cobertura de CNPJs (quantidade e qualidade)
2. Inconsistências de dados
3. Duplicações
4. Completude de informações
5. Distribuição de consultores

---

## Como Executar a Auditoria

### Método 1: PowerShell (Recomendado)

1. **Abra PowerShell** (não Git Bash)
   - Clique no Windows Search
   - Digite "PowerShell"
   - Clique em "Windows PowerShell"

2. **Navegue para o diretório**:
   ```powershell
   cd "c:\Users\User\OneDrive\Documentos\GitHub\CRM-VITAO360"
   ```

3. **Execute a auditoria**:
   ```powershell
   python scripts/phase10_validacao_final/analisar_xlsx_manual.py
   ```

4. **Aguarde** a conclusão (demora 30-60 segundos)

### Método 2: Duplo Clique (Mais Fácil)

Execute diretamente este arquivo batch:
```
c:\Users\User\OneDrive\Documentos\GitHub\CRM-VITAO360\scripts\phase10_validacao_final\run_confronto.bat
```

---

## Resultado da Auditoria

Após executar qualquer método, você receberá:

1. **Resumo no console** (visível na janela PowerShell)
2. **Arquivo JSON completo**: `confronto_v13_v31.json`

### Exemplo de Saída

```
================================================================================
AUDITORIA DE DADOS V13 vs V31
================================================================================

[1/3] Carregando estrutura...
  V13: 15 abas
  V31: 12 abas

[2/3] Analisando CARTEIRA...
  Processando V13...
    45.320 linhas, 12.480 CNPJs únicos, 340 duplicados
  Processando V31...
    52.100 linhas, 14.250 CNPJs únicos, 520 duplicados

  Resumo CNPJs:
    V13: 12.480 únicos
    V31: 14.250 únicos
    Em comum: 10.850
    Apenas em V13: 1.630
    Apenas em V31: 3.400

[3/3] Gerando recomendações...

================================================================================
RESUMO EXECUTIVO
================================================================================

COBERTURA DE CNPJs:
  V13: 12.480 CNPJs
  V31: 14.250 CNPJs
  Comuns: 10.850

QUALIDADE:
  Duplicados em V13: 340
  Duplicados em V31: 520
  Nomes inconsistentes: 285

RECOMENDAÇÕES:
  1. [ALTA] COBERTURA
     V31 tem 3.400 CNPJs a mais - V31 parece mais completa para cobertura
  2. [ALTA] QUALIDADE
     V13: 340 duplicados | V31: 520 duplicados - Deduplicar antes de usar em produção
  3. [MEDIA] INCONSISTENCIA
     285 CNPJs com nomes diferentes - Revisar e padronizar nomes de clientes

================================================================================
```

---

## Interpretando os Resultados

### Métrica 1: Cobertura de CNPJs

**O que significa:**
- Quantos clientes únicos existem em cada versão
- Qual versão tem mais clientes cadastrados

**Como interpretar:**
- Versão com MAIS CNPJs = melhor cobertura
- Se V31 tem 3.400 CNPJs a mais, V31 é mais completa

### Métrica 2: Duplicações

**O que significa:**
- Mesmos CNPJs aparecem múltiplas vezes na mesma versão
- Indica erros de entrada de dados

**Como interpretar:**
- Menos duplicados = dados mais limpos
- Tanto V13 quanto V31 precisam de limpeza

### Métrica 3: Nomes Inconsistentes

**O que significa:**
- Mesmo CNPJ tem nome de cliente diferente entre versões

**Como interpretar:**
- Indica falta de padronização
- Necessário decidir qual nome é correto

### Métrica 4: Completude

**O que significa:**
- Quantas células têm dados preenchidos vs vazias

**Como interpretar:**
- % maior = dados mais completos
- Melhor para uso em produção

---

## Decisão: Qual Versão Usar?

Considere esta matriz de decisão:

| Critério | Prioridade | Impacto |
|----------|-----------|--------|
| Cobertura de CNPJs | ALTA | Se faltam clientes, agenda incompleta |
| Duplicações | ALTA | Gera registros incorretos na agenda |
| Nomes inconsistentes | MÉDIA | Afeta apresentação, menos crítico |
| Completude de dados | ALTA | Afeta qualidade da agenda |

**Recomendação geral:**
1. A versão com MAIOR cobertura de CNPJs é preferível
2. A versão com MENOS duplicações é preferível
3. Idealmente, você mesclaria as duas versões, removendo duplicatas

---

## Arquivos Relacionados

### Scripts de Análise

1. **analisar_xlsx_manual.py** (Recomendado)
   - Usa apenas bibliotecas padrão Python
   - Não precisa instalar nada extra
   - Mais rápido

2. **confronto_dados.py** (Alternativo)
   - Usa openpyxl (mais detalhado)
   - Requer instalação: `pip install openpyxl`
   - Mais lento mas mais preciso

3. **run_confronto.bat**
   - Wrapper batch
   - Duplo clique para executar

### Documentação

- `INSTRUÇÕES_AUDITORIA.md` - Instruções detalhadas
- `README_AUDITORIA.md` - Este arquivo
- `confronto_v13_v31.json` - Resultado da auditoria (gerado após execução)

---

## Troubleshooting

### Problema: "Python não foi encontrado"

**Solução:**
1. Instale Python de https://www.python.org/downloads/
2. Na instalação, marque: ✓ Add Python to PATH
3. Reinicie o PowerShell
4. Tente novamente

### Problema: "Arquivo não encontrado"

**Solução:**
1. Verifique que os arquivos existem nos caminhos corretos
2. Se os nomes mudaram, edite o script para apontar o novo caminho

### Problema: "Script demora muito"

**Solução:**
- É normal demorar 30-60 segundos (arquivos são grandes)
- Deixe rodar até ver "Resultado salvo:"

### Problema: "JSON vazio ou incompleto"

**Solução:**
1. Verifique se o script executou sem erros
2. Abra PowerShell e rode novamente, observando mensagens de erro
3. Se houver erro, releia a seção "Troubleshooting"

---

## Próximos Passos

Após análise concluída:

1. **Revise** o arquivo `confronto_v13_v31.json`
2. **Analise** as recomendações geradas
3. **Defina** qual versão usar como base
4. **Documente** as decisões
5. **Implemente** correções (deduplicação, padronização de nomes)
6. **Teste** a agenda inteligente com a versão escolhida

---

## Contato e Suporte

Se houver problemas:
1. Verifique este README
2. Revise as instruções em `INSTRUÇÕES_AUDITORIA.md`
3. Analise o arquivo `confronto_v13_v31.json` manualmente
4. Abra um issue no repositório com detalhes do erro

---

**Status**: Pronto para execução
**Última atualização**: 2026-02-17
**Versão**: 1.0
