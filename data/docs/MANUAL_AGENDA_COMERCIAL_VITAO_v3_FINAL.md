# ══════════════════════════════════════════════════════════════════════════════
# MANUAL OFICIAL - AGENDA COMERCIAL VITAO
# DOCUMENTACAO PADRAO INTOCAVEL - USO SEMANAL
# ══════════════════════════════════════════════════════════════════════════════
# Versao: 3.0 FINAL
# Data: 29/01/2026
# Status: PADRAO OFICIAL DEFINITIVO - NAO ALTERAR SEM AUTORIZACAO
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# SECAO 1: EQUIPE COMERCIAL E TERRITORIOS
# ══════════════════════════════════════════════════════════════════════════════

## 1.1 CONSULTORES E TERRITORIOS

┌─────────────────┬──────────────────┬─────────────────────┬─────────────────────────────┐
│ CONSULTOR       │ TIPO             │ TERRITORIO          │ ESTADOS                     │
├─────────────────┼──────────────────┼─────────────────────┼─────────────────────────────┤
│ MANU DITZEL     │ INTERNO          │ REGIAO SUL          │ SC, PR, RS                  │
│ LARISSA PADILHA │ INTERNO          │ RESTANTE BRASIL     │ Todos EXCETO SC, PR, RS     │
│ JULIO GADRET    │ RCA EXTERNO      │ CONTAS EXCLUSIVAS   │ Base SC + Brasil (redes)    │
│ CENTRAL DAIANE  │ GERENTE + KAM    │ REDES E FRANQUIAS   │ BRASIL INTEIRO              │
└─────────────────┴──────────────────┴─────────────────────┴─────────────────────────────┘

## 1.2 REDES POR RESPONSAVEL

┌─────────────────┬─────────────────────────────────────────────────────────────┐
│ RESPONSAVEL     │ REDES EXCLUSIVAS                                            │
├─────────────────┼─────────────────────────────────────────────────────────────┤
│ DAIANE          │ DIVINA TERRA, BIOMUNDO, MUNDO VERDE, TUDO EM GRAOS,         │
│                 │ VIDA LEVE, ARMAZEM FITSTORE                                 │
├─────────────────┼─────────────────────────────────────────────────────────────┤
│ JULIO           │ CIA DA SAUDE, FITLAND (todas filiais Brasil inteiro)       │
└─────────────────┴─────────────────────────────────────────────────────────────┘

## 1.3 REGRAS DE ROTEAMENTO (ORDEM DE PRIORIDADE)

```
REGRA 1: Cliente CIA DA SAUDE ou FITLAND → JULIO (qualquer estado)
REGRA 2: Cliente com TAG "redes e franquias" → DAIANE
REGRA 3: Cliente DIVINA TERRA, BIOMUNDO, MUNDO VERDE, TUDO EM GRAOS, VIDA LEVE → DAIANE
REGRA 4: Estado SC, PR, RS com vendedor_ultimo_pedido = JULIO → JULIO
REGRA 5: Estado SC, PR, RS → MANU (fallback: LARISSA durante licenca maternidade)
REGRA 6: Qualquer outro estado → LARISSA
```

## 1.4 STATUS 2026

- MANU DITZEL: Licenca maternidade em 2026 (carteira vai para LARISSA)
- LARISSA PADILHA: Ativa
- JULIO GADRET: Ativo
- CENTRAL DAIANE: Ativa (gestora + key account)


# ══════════════════════════════════════════════════════════════════════════════
# SECAO 2: LAYOUT OFICIAL - 20 COLUNAS (INTOCAVEL!)
# ══════════════════════════════════════════════════════════════════════════════

## 2.1 ESTRUTURA DAS COLUNAS

┌─────┬────────────────────┬──────────┬─────────────────┬────────┐
│ COL │ CAMPO              │ TIPO     │ FONTE           │ LARGURA│
├─────┼────────────────────┼──────────┼─────────────────┼────────┤
│  1  │ DATA               │ Data     │ Calculado       │ 12     │
│  2  │ BLOCO              │ Texto    │ Regra situacao  │ 15     │
│  3  │ ESTAGIO FUNIL      │ Texto    │ Regra situacao  │ 18     │
│  4  │ CURVA              │ Texto    │ Valor (A/B/C)   │ 6      │
│  5  │ NOME FANTASIA      │ Texto    │ Carteira Mercos │ 35     │
│  6  │ CNPJ               │ Texto    │ Carteira Mercos │ 20     │
│  7  │ COD SAP            │ Texto    │ Base SAP        │ 12     │
│  8  │ UF                 │ Texto    │ Carteira Mercos │ 4      │
│  9  │ REDE               │ Texto    │ Master Redes    │ 15     │
│ 10  │ VALOR ULT PEDIDO   │ Numero   │ Carteira Mercos │ 14     │
│ 11  │ DATA ULT PEDIDO    │ Data     │ Carteira Mercos │ 12     │
│ 12  │ DIAS S/COMPRA      │ Numero   │ Carteira Mercos │ 12     │
│ 13  │ CICLO MEDIO        │ Numero   │ Carteira Mercos │ 10     │
│ 14  │ SITUACAO           │ Texto    │ Carteira Mercos │ 15     │
│ 15  │ DATA CADASTRO      │ Data     │ Carteira Mercos │ 12     │
│ 16  │ NO COMPRA          │ Texto    │ Calculado       │ 12     │
│ 17  │ TIPO VENDA         │ Texto    │ Regra situacao  │ 12     │
│ 18  │ ACAO               │ Texto    │ Regra situacao  │ 35     │
│ 19  │ TELEFONE           │ Texto    │ Carteira Mercos │ 15     │
│ 20  │ VENDEDOR ORIGINAL  │ Texto    │ Carteira Mercos │ 18     │
└─────┴────────────────────┴──────────┴─────────────────┴────────┘

## 2.2 ESTRUTURA DO ARQUIVO

```
LINHA 1: TITULO - "AGENDA COMERCIAL - [NOME CONSULTOR]"
LINHA 2: RESUMO - "CARTEIRA: X | ATIVOS: Y | INAT.REC: Z | INAT.ANT: W | REDES: R"
LINHA 3: CABECALHOS (20 colunas)
LINHA 4+: DADOS
```

## 2.3 ABAS DO ARQUIVO

```
1. Central_Daiane    - Carteira completa da Daiane (redes + carteira interna)
2. Manu_Ditzel       - Carteira completa SC/PR/RS
3. Julio_Gadret      - Carteira completa (Cia Saude + Fitland + clientes presenciais)
4. Larissa_Padilha   - Carteira completa restante Brasil
5. REDES_FRANQUIAS   - Consolidado de TODOS clientes de rede (referencia)
6. OUTROS            - Clientes sem vendedor definido
```


# ══════════════════════════════════════════════════════════════════════════════
# SECAO 3: REGRAS DE NEGOCIO (CRITICO - NAO ALTERAR!)
# ══════════════════════════════════════════════════════════════════════════════

## 3.1 SITUACAO → BLOCO / ESTAGIO / ACAO / COR

┌─────────────────┬─────────────────┬───────────────────┬────────────────────────────────┬─────────────┐
│ SITUACAO        │ BLOCO           │ ESTAGIO FUNIL     │ ACAO                           │ COR (HEX)   │
├─────────────────┼─────────────────┼───────────────────┼────────────────────────────────┼─────────────┤
│ ATIVO           │ LIGACAO MANHA   │ CS / RECOMPRA     │ LIGACAO - OFERECER REPOSICAO   │ #00B050 🟢  │
│ INATIVO RECENTE │ LIGACAO MANHA   │ ATENCAO / SALVAR  │ LIGACAO - REATIVAR             │ #ED7D31 🟠  │
│ INATIVO ANTIGO  │ LIGACAO TARDE   │ PERDA / NUTRICAO  │ LIGACAO - REATIVACAO           │ #C00000 🔴  │
│ PROSPECT        │ PROSPECCAO      │ LEADS / PROSPECTS │ 1O CONTATO - APRESENTAR VITAO  │ #F2F2F2 ⚪  │
└─────────────────┴─────────────────┴───────────────────┴────────────────────────────────┴─────────────┘

** IMPORTANTE: "INATIVO RECENTE" = "ATENCAO / SALVAR" (momento de salvar, NAO de perder!)

## 3.2 TIPO VENDA

┌─────────────────┬──────────────┐
│ SITUACAO        │ TIPO VENDA   │
├─────────────────┼──────────────┤
│ ATIVO           │ RECOMPRA     │
│ INATIVO RECENTE │ RESGATE      │
│ INATIVO ANTIGO  │ REATIVACAO   │
│ PROSPECT        │ 1A COMPRA    │
└─────────────────┴──────────────┘

## 3.3 CURVA ABC

┌───────┬────────────────────┐
│ CURVA │ CRITERIO           │
├───────┼────────────────────┤
│ A     │ Valor >= R$ 2.000  │
│ B     │ Valor >= R$ 500    │
│ C     │ Valor < R$ 500     │
└───────┴────────────────────┘

## 3.4 PRIORIDADE DE ATENDIMENTO

```
1º ATIVO (verde)         - Cliente comprando, manter relacionamento
2º INATIVO RECENTE (laranja) - URGENTE! Salvar antes de virar perda
3º INATIVO ANTIGO (vermelho) - Tentar recuperar
```

## 3.5 LIMITE DE ATENDIMENTOS

```
MAXIMO: 40 atendimentos por consultor por dia
DISTRIBUICAO: Priorizar ATIVO > INATIVO RECENTE > INATIVO ANTIGO
```


# ══════════════════════════════════════════════════════════════════════════════
# SECAO 4: CORES E FORMATACAO (INTOCAVEL!)
# ══════════════════════════════════════════════════════════════════════════════

## 4.1 CORES DA COLUNA SITUACAO (COLUNA 14)

```
ATIVO           → #00B050 (verde)      + texto branco
INATIVO RECENTE → #ED7D31 (laranja)    + texto branco  
INATIVO ANTIGO  → #C00000 (vermelho)   + texto branco
PROSPECT        → sem cor (cinza)
```

** IMPORTANTE: Cor aplica APENAS na coluna SITUACAO (col 14), NAO na linha inteira!

## 4.2 CABECALHO (LINHA 3)

```
Fundo: #2F5496 (azul escuro)
Texto: #FFFFFF (branco)
Fonte: Bold, tamanho 11
Altura linha: 30
```

## 4.3 LINHAS DE DADOS (LINHA 4+)

```
Fundo alternado: #FFFFFF (branco) / #F2F2F2 (cinza claro)
Bordas: thin em todas celulas
```

## 4.4 CONGELAR

```
Congelar em: A4 (cabecalhos sempre visiveis ao rolar)
```


# ══════════════════════════════════════════════════════════════════════════════
# SECAO 5: NORMALIZACAO DE DADOS
# ══════════════════════════════════════════════════════════════════════════════

## 5.1 TEXTOS

```
- MAIUSCULO
- SEM ACENTOS (usar unicodedata NFKD)
- Trim espacos

Exemplos:
  "Bella Vita - Café" → "BELLA VITA - CAFE"
  "São Paulo" → "SAO PAULO"
```

## 5.2 CNPJ

```
- Apenas digitos
- 14 caracteres com zeros a esquerda
- Sem pontuacao

Exemplos:
  "07.621.230/0001-17" → "07621230000117"
  "7621230000117" → "07621230000117"
```

## 5.3 TELEFONE

```
- Formato: 55 + DDD + NUMERO
- 13 digitos (celular) ou 12 digitos (fixo)
- Adicionar 9 em celular antigo

Exemplos:
  "(41) 99117-8234" → "5541991178234"
  "3019-9221" + UF=PR → "554130199221"
```

## 5.4 NOMES DE REDE (MAPA PADRAO)

```
FIT LAND       → FITLAND
FITLAND        → FITLAND
CIA DA SAUDE   → CIA DA SAUDE
CIA SAUDE      → CIA DA SAUDE
BIO MUNDO      → BIOMUNDO
BIOMUNDO       → BIOMUNDO
VIDA LEVE      → VIDA LEVE
DIVINA TERRA   → DIVINA TERRA
MUNDO VERDE    → MUNDO VERDE
TUDO EM GRAOS  → TUDO EM GRAOS
TUDO EM GRÃOS  → TUDO EM GRAOS
ARMAZEM FITSTORE → ARMAZEM FITSTORE
```

## 5.5 NOMES DE VENDEDOR (MAPA PADRAO)

```
Contendo "JULIO"              → JULIO GADRET
Contendo "CENTRAL" ou "DAIANE"→ CENTRAL DAIANE
Contendo "MANU"               → MANU DITZEL
Contendo "LARISSA"            → LARISSA PADILHA
Outros                        → OUTROS
```


# ══════════════════════════════════════════════════════════════════════════════
# SECAO 6: FONTES DE DADOS
# ══════════════════════════════════════════════════════════════════════════════

## 6.1 ARQUIVOS NECESSARIOS (EXTRAIR SEMANALMENTE)

```
1. CARTEIRA MERCOS (obrigatorio)
   Arquivo: Carteira_detalhada_de_clientes_DD_MM_YYYY.xlsx
   Fonte: Mercos > Relatorios > Carteira detalhada
   
2. MASTER REDES (no projeto)
   Arquivo: /mnt/project/MASTER_REDES_NORMALIZADO.xlsx
   Conteudo: 657 CNPJs de franquias/redes
```

## 6.2 COLUNAS DA CARTEIRA MERCOS USADAS

```
- Razao Social
- Nome fantasia
- CNPJ/CPF
- Telefone
- Estado
- Data do ultimo pedido
- Vendedor do ultimo pedido
- Valor do ultimo pedido
- Dias sem comprar
- Ciclo medio de compra
- Situacao (Ativo, Inativo recente, Inativo antigo)
- Data de cadastro
- Tags de cliente
```

## 6.3 IDENTIFICACAO DE REDE (PRIORIDADE)

```
1º CNPJ existe no MASTER_REDES → usa rede do master
2º TAG na carteira Mercos → usa tag normalizada
3º Nenhum match → cliente sem rede
```


# ══════════════════════════════════════════════════════════════════════════════
# SECAO 7: PROCESSO SEMANAL
# ══════════════════════════════════════════════════════════════════════════════

## 7.1 SEXTA-FEIRA (ATUALIZACAO)

```
1. Exportar Carteira Mercos (filtro: Ativos + Inativos recentes + Inativos antigos)
2. Fazer upload no projeto Claude
3. Executar prompt padrao (secao 8)
4. Validar totais (checklist secao 9)
5. Baixar arquivo gerado
6. Distribuir para consultores
```

## 7.2 SEGUNDA A QUINTA (EXECUCAO)

```
- Consultor executa agenda do dia
- Registra contatos no Mercos
- Reporta conversoes
- Gestor acompanha execucao
```

## 7.3 FLUXO VISUAL

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   SEXTA      │    │   CLAUDE     │    │   ARQUIVO    │    │  CONSULTORES │
│  Exportar    │ → │  Processar   │ → │   Gerado     │ → │   Executam   │
│   Mercos     │    │   Agenda     │    │   .xlsx      │    │   Agenda     │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```


# ══════════════════════════════════════════════════════════════════════════════
# SECAO 8: PROMPT PADRAO (COPIAR E COLAR)
# ══════════════════════════════════════════════════════════════════════════════

## 8.1 PROMPT PARA NOVA CONVERSA

```
Gerar agenda comercial VITAO para [MES/ANO].

ARQUIVOS ENVIADOS:
- Carteira detalhada de clientes (Mercos)

REGRAS OBRIGATORIAS (NAO ALTERAR):

1. LAYOUT: 20 colunas fixas
   DATA | BLOCO | ESTAGIO FUNIL | CURVA | NOME FANTASIA | CNPJ | COD SAP | UF | REDE | 
   VALOR ULT PEDIDO | DATA ULT PEDIDO | DIAS S/COMPRA | CICLO MEDIO | SITUACAO | 
   DATA CADASTRO | NO COMPRA | TIPO VENDA | ACAO | TELEFONE | VENDEDOR ORIGINAL

2. REGRAS POR SITUACAO:
   - ATIVO → BLOCO: LIGACAO MANHA | ESTAGIO: CS / RECOMPRA | COR: #00B050 (verde)
   - INATIVO RECENTE → BLOCO: LIGACAO MANHA | ESTAGIO: ATENCAO / SALVAR | COR: #ED7D31 (laranja)
   - INATIVO ANTIGO → BLOCO: LIGACAO TARDE | ESTAGIO: PERDA / NUTRICAO | COR: #C00000 (vermelho)

3. CORES: Aplicar APENAS na coluna SITUACAO (col 14), NAO na linha inteira
   CABECALHO: Azul #2F5496

4. TERRITORIOS:
   - MANU DITZEL: SC, PR, RS
   - LARISSA PADILHA: Todos estados EXCETO SC, PR, RS
   - JULIO GADRET: CIA DA SAUDE e FITLAND (Brasil inteiro) + clientes presenciais SC
   - CENTRAL DAIANE: Redes (Divina Terra, Biomundo, Mundo Verde, Tudo em Graos, Vida Leve)

5. ABAS: Central_Daiane, Manu_Ditzel, Julio_Gadret, Larissa_Padilha, REDES_FRANQUIAS, OUTROS

6. LIMITE: Maximo 40 atendimentos/dia por consultor

7. NORMALIZACAO: MAIUSCULO sem acentos, CNPJ 14 digitos, TEL 55+DDD+NUM

8. PRIORIDADE: ATIVO > INATIVO RECENTE > INATIVO ANTIGO

Gerar arquivo AGENDA_COMERCIAL_[MES][ANO].xlsx
```

## 8.2 COMANDO RAPIDO (CONVERSA EXISTENTE)

```
Atualizar agenda comercial para [MES/ANO] com a carteira enviada.
Seguir layout padrao 20 colunas e regras documentadas.
```


# ══════════════════════════════════════════════════════════════════════════════
# SECAO 9: CHECKLIST DE VALIDACAO
# ══════════════════════════════════════════════════════════════════════════════

## 9.1 ANTES DE ENTREGAR - OBRIGATORIO

```
[ ] Total registros = Total carteira Mercos
[ ] CNPJs com 14 digitos
[ ] Telefones formato 55+DDD+NUM
[ ] Textos em MAIUSCULO sem acentos
[ ] Cores aplicadas na coluna SITUACAO (col 14)
[ ] Cabecalho azul #2F5496
[ ] Maximo 40 atendimentos/dia por consultor
[ ] Prioridade: ATIVO primeiro, depois INATIVO RECENTE, depois INATIVO ANTIGO
```

## 9.2 VERIFICAR REGRAS DE NEGOCIO

```
[ ] ATIVO → BLOCO: LIGACAO MANHA
[ ] ATIVO → ESTAGIO: CS / RECOMPRA
[ ] ATIVO → COR: #00B050 (verde)

[ ] INATIVO RECENTE → BLOCO: LIGACAO MANHA
[ ] INATIVO RECENTE → ESTAGIO: ATENCAO / SALVAR (NAO "FOLLOW UP"!)
[ ] INATIVO RECENTE → COR: #ED7D31 (laranja)

[ ] INATIVO ANTIGO → BLOCO: LIGACAO TARDE
[ ] INATIVO ANTIGO → ESTAGIO: PERDA / NUTRICAO
[ ] INATIVO ANTIGO → COR: #C00000 (vermelho)
```

## 9.3 VERIFICAR TERRITORIOS

```
[ ] Clientes SC/PR/RS sem rede → MANU DITZEL
[ ] Clientes outros estados sem rede → LARISSA PADILHA
[ ] CIA DA SAUDE e FITLAND → JULIO GADRET
[ ] Outras redes → CENTRAL DAIANE
```


# ══════════════════════════════════════════════════════════════════════════════
# SECAO 10: ERROS PROIBIDOS
# ══════════════════════════════════════════════════════════════════════════════

```
❌ NAO mudar cores sem autorizacao
❌ NAO mudar layout de colunas
❌ NAO mudar ordem das colunas
❌ NAO usar "FOLLOW UP" para INATIVO RECENTE (correto: ATENCAO / SALVAR)
❌ NAO colorir linha inteira (so coluna SITUACAO)
❌ NAO exceder 40 atendimentos/dia
❌ NAO esquecer de aplicar cor na coluna SITUACAO
❌ NAO fabricar dados
❌ NAO ignorar regras de territorio
```


# ══════════════════════════════════════════════════════════════════════════════
# SECAO 11: CODIGO PYTHON DE REFERENCIA
# ══════════════════════════════════════════════════════════════════════════════

```python
# CONSTANTES
COLUNAS = [
    'DATA', 'BLOCO', 'ESTAGIO FUNIL', 'CURVA', 'NOME FANTASIA',
    'CNPJ', 'COD SAP', 'UF', 'REDE', 'VALOR ULT PEDIDO',
    'DATA ULT PEDIDO', 'DIAS S/COMPRA', 'CICLO MEDIO', 'SITUACAO',
    'DATA CADASTRO', 'NO COMPRA', 'TIPO VENDA', 'ACAO', 'TELEFONE', 
    'VENDEDOR ORIGINAL'
]

LARGURAS = [12, 15, 18, 6, 35, 20, 12, 4, 15, 14, 12, 12, 10, 15, 12, 12, 12, 35, 15, 18]

# CORES
COR_ATIVO = PatternFill('solid', fgColor='00B050')
COR_INATIVO_RECENTE = PatternFill('solid', fgColor='ED7D31')
COR_INATIVO_ANTIGO = PatternFill('solid', fgColor='C00000')
COR_CABECALHO = PatternFill('solid', fgColor='2F5496')
FONT_BRANCO = Font(color='FFFFFF', bold=True)

# REGRAS
def definir_bloco(situacao):
    if situacao == 'ATIVO': return 'LIGACAO MANHA'
    if situacao == 'INATIVO RECENTE': return 'LIGACAO MANHA'
    if situacao == 'INATIVO ANTIGO': return 'LIGACAO TARDE'
    return 'PROSPECCAO'

def definir_estagio_funil(situacao):
    if situacao == 'ATIVO': return 'CS / RECOMPRA'
    if situacao == 'INATIVO RECENTE': return 'ATENCAO / SALVAR'
    if situacao == 'INATIVO ANTIGO': return 'PERDA / NUTRICAO'
    return 'LEADS / PROSPECTS'

def definir_acao(situacao):
    if situacao == 'ATIVO': return 'LIGACAO - OFERECER REPOSICAO'
    if situacao == 'INATIVO RECENTE': return 'LIGACAO - REATIVAR'
    if situacao == 'INATIVO ANTIGO': return 'LIGACAO - REATIVACAO'
    return '1O CONTATO - APRESENTAR VITAO'

# ROTEAMENTO
def definir_vendedor(row, cnpjs_redes):
    nome = row['NOME'].upper()
    uf = row['UF']
    vendedor_ultimo = row['VENDEDOR_ULTIMO']
    cnpj = row['CNPJ_NORM']
    rede = cnpjs_redes.get(cnpj, '')
    
    # REGRA 1: CIA DA SAUDE ou FITLAND → JULIO
    if 'CIA DA SAUDE' in nome or 'CIA SAUDE' in nome or 'FITLAND' in nome:
        return 'JULIO GADRET'
    if rede in ['CIA DA SAUDE', 'FITLAND']:
        return 'JULIO GADRET'
    
    # REGRA 2: Outras redes → DAIANE
    if rede in ['DIVINA TERRA', 'BIOMUNDO', 'MUNDO VERDE', 'TUDO EM GRAOS', 'VIDA LEVE', 'ARMAZEM FITSTORE']:
        return 'CENTRAL DAIANE'
    
    # REGRA 3: Sul com Julio → JULIO
    if uf in ['SC', 'PR', 'RS'] and 'JULIO' in vendedor_ultimo.upper():
        return 'JULIO GADRET'
    
    # REGRA 4: Sul → MANU
    if uf in ['SC', 'PR', 'RS']:
        return 'MANU DITZEL'
    
    # REGRA 5: Restante → LARISSA
    return 'LARISSA PADILHA'
```


# ══════════════════════════════════════════════════════════════════════════════
# SECAO 12: HISTORICO DE VERSOES
# ══════════════════════════════════════════════════════════════════════════════

| VERSAO | DATA       | ALTERACAO                                           |
|--------|------------|-----------------------------------------------------|
| 1.0    | 28/01/2026 | Versao inicial                                      |
| 2.0    | 28/01/2026 | Correcao cores e ATENCAO/SALVAR                     |
| 3.0    | 29/01/2026 | Adicao territorios, roteamento, processo semanal    |


# ══════════════════════════════════════════════════════════════════════════════
# FIM DO MANUAL - NAO ALTERAR SEM AUTORIZACAO
# ══════════════════════════════════════════════════════════════════════════════
