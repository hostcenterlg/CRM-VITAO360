# README — Para o Time Técnico CRM 360

**Análise Crítica do Cliente · Guia de Implementação**
Versão 1.0 · 29/04/2026 · CRM VITAO360

> Este README é a fonte de verdade técnica para implementação do DDE (Demonstração de Desempenho Econômico) e Análise Crítica.
> Importado em 29/Abr/2026 para orquestração das Ondas MIKE/NOVEMBER/OSCAR/PAPA/QUEBEC.

---

## 1. Stack Validado

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| Backend | Python 3.12+ | 3.12.x |
| Excel parser | openpyxl | 3.1+ |
| Data wrangling | pandas | 2.2+ |
| Fuzzy match | rapidfuzz | 3.x |
| XLSX Surgery | zipfile + lxml | stdlib + 5.x |
| DOCX | python-docx | 1.1+ |
| API | FastAPI | 0.115+ |
| ORM | SQLAlchemy 2.0 | 2.0+ |
| Database | PostgreSQL 15+ | 15.x |
| Migration | Alembic | 1.13+ |
| Frontend | Next.js 14 + TS + Tailwind | atual |
| Charts | Recharts | 2.x |

---

## 2. Schema PostgreSQL — 4 Tabelas Novas + ALTERs

### T1 — `cliente_frete_mensal` (L14)
```sql
CREATE TABLE cliente_frete_mensal (
  id SERIAL PRIMARY KEY,
  cnpj VARCHAR(14) NOT NULL,
  ano INT NOT NULL,
  mes INT NOT NULL,
  qtd_ctes INT,
  valor_brl NUMERIC(14,2) NOT NULL,
  fonte VARCHAR(20) NOT NULL DEFAULT 'LOG_UPLOAD',
  classificacao VARCHAR(10) NOT NULL DEFAULT 'REAL',
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(cnpj, ano, mes, fonte)
);
CREATE INDEX idx_frete_cnpj ON cliente_frete_mensal(cnpj, ano);
```

### T2 — `cliente_verba_anual` (L16)
```sql
CREATE TABLE cliente_verba_anual (
  id SERIAL PRIMARY KEY,
  cnpj VARCHAR(14) NOT NULL,
  ano INT NOT NULL,
  tipo VARCHAR(20) NOT NULL,  -- 'CONTRATO' | 'EFETIVADA'
  valor_brl NUMERIC(14,2) NOT NULL,
  desc_total_pct NUMERIC(5,2),
  inicio_vigencia DATE,
  fim_vigencia DATE,
  fonte VARCHAR(20) NOT NULL,
  classificacao VARCHAR(10) NOT NULL DEFAULT 'REAL',
  observacao TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(cnpj, ano, tipo, fonte)
);
```

### T3 — `cliente_promotor_mensal` (L17)
```sql
CREATE TABLE cliente_promotor_mensal (
  id SERIAL PRIMARY KEY,
  cnpj VARCHAR(14) NOT NULL,
  agencia VARCHAR(80),
  ano INT NOT NULL,
  mes INT NOT NULL,
  valor_brl NUMERIC(14,2) NOT NULL,
  fonte VARCHAR(20) NOT NULL DEFAULT 'LOG_UPLOAD',
  classificacao VARCHAR(10) NOT NULL DEFAULT 'REAL',
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(cnpj, agencia, ano, mes)
);
```

### T4 — `cliente_dre_periodo` (cache cascata)
```sql
CREATE TABLE cliente_dre_periodo (
  id SERIAL PRIMARY KEY,
  cnpj VARCHAR(14) NOT NULL,
  ano INT NOT NULL,
  mes INT,
  linha VARCHAR(10) NOT NULL,  -- L1, L4, L11, I2...
  conta VARCHAR(80) NOT NULL,
  valor_brl NUMERIC(14,2),     -- nullable: PENDENTE = NULL
  pct_sobre_receita NUMERIC(6,3),
  fonte VARCHAR(20),
  classificacao VARCHAR(10),   -- REAL|SINTETICO|PENDENTE|NULL
  fase VARCHAR(2),             -- 'A'|'B'|'C'
  observacao TEXT,
  calculado_em TIMESTAMP DEFAULT NOW(),
  UNIQUE(cnpj, ano, mes, linha)
);
CREATE INDEX idx_dre_cnpj_ano ON cliente_dre_periodo(cnpj, ano);
```

### ALTERs (Decisão D1)
```sql
ALTER TABLE clientes
  ADD COLUMN desc_comercial_pct NUMERIC(5,2),
  ADD COLUMN desc_financeiro_pct NUMERIC(5,2),
  ADD COLUMN total_bonificacao NUMERIC(14,2),
  ADD COLUMN ipi_total NUMERIC(14,2);

ALTER TABLE vendas
  ADD COLUMN ipi_total NUMERIC(12,2),
  ADD COLUMN desconto_comercial NUMERIC(12,2),
  ADD COLUMN desconto_financeiro NUMERIC(12,2),
  ADD COLUMN bonificacao NUMERIC(12,2);
```

---

## 3. Estrutura de Pastas

```
backend/app/models/
  cliente_frete.py, cliente_verba.py,
  cliente_promotor.py, cliente_dre.py
backend/app/api/
  routes_dde.py
backend/app/services/
  dde_engine.py
backend/alembic/versions/
  xxxx_add_dde_tables.py
scripts/parsers/
  base_parser.py, parser_zsdfat.py, parser_verbas.py,
  parser_frete.py, parser_contratos.py, parser_promotores.py
frontend/src/app/gestao/
  dde/page.tsx, analise-critica/page.tsx
```

---

## 4. 22 Padrões Regex DRE

```python
DRE_CORRECOES: list[tuple[str, str, str]] = [
    ("C01", r"(?i)faturamento\s*bruto|fat\.?\s*bruto|receita\s*bruta\s*tab", "FATURAMENTO BRUTO A TABELA"),
    ("C02", r"(?i)ipi\s*(sobre|s/)?\s*venda|ipi\s*faturad", "IPI SOBRE VENDAS"),
    ("C03", r"(?i)devolu[cç][ãa]o|devolu[çc]oes|devolução", "(-) DEVOLUÇÕES"),
    ("C04", r"(?i)desc\.?\s*comercial|desconto\s*comerc|desc\.\s*com\.?", "(-) DESCONTO COMERCIAL"),
    ("C05", r"(?i)desc\.?\s*financ|desconto\s*financ|desc\.\s*fin\.?", "(-) DESCONTO FINANCEIRO"),
    ("C06", r"(?i)bonifica[cç][ãa]o|bonif\.?|bonifica[çc]oes", "(-) BONIFICAÇÕES"),
    ("C07", r"(?i)ipi\s*re(colhido|passado)|ipi\s*deduz", "(-) IPI FATURADO"),
    ("C08", r"(?i)icms(?!\s*-?\s*st)|icms\s*pr[oó]prio", "(-) ICMS"),
    ("C09", r"(?i)pis\b", "(-) PIS"),
    ("C10", r"(?i)cofins\b", "(-) COFINS"),
    ("C11", r"(?i)icms\s*-?\s*st|substitui[cç][ãa]o\s*tribut", "(-) ICMS-ST"),
    ("C12", r"(?i)receita\s*l[ií]quida|rec\.?\s*l[ií]q", "= RECEITA LÍQUIDA"),
    ("C13", r"(?i)cmv|custo\s*(d[oe]s?\s*)?prod|custo\s*mercad|cpv", "(-) CMV"),
    ("C14", r"(?i)margem\s*bruta|mg\.?\s*bruta", "= MARGEM BRUTA"),
    ("C15", r"(?i)frete|transporte|ct-?e", "(-) FRETE CT-e"),
    ("C16", r"(?i)comiss[ãa]o|representante|rep\.?\s*comerc", "(-) COMISSÃO SOBRE VENDA"),
    ("C17", r"(?i)verba|contrato\s*desc|zdf2|zpmh", "(-) VERBAS (CONTRATOS)"),
    ("C18", r"(?i)promotor|merchandis|pdv\s*agenc", "(-) PROMOTOR PDV"),
    ("C19", r"(?i)inadimpl[eê]ncia|provis[ãa]o\s*(de\s*)?d[ée]bito|pdd", "(-) CUSTO DE INADIMPLÊNCIA"),
    ("C20", r"(?i)custo\s*financ|capital\s*giro|cdi\b", "(-) CUSTO FINANCEIRO (CAPITAL GIRO)"),
    ("C21", r"(?i)margem\s*(de\s*)?contribui[cç][ãa]o|mc\b|mg\.?\s*contrib", "= MARGEM DE CONTRIBUIÇÃO"),
    ("C22", r"(?i)estrutura\s*comerc|folha\s*comerc|desp\.?\s*comerc\s*fix", "(-) ESTRUTURA COMERCIAL ALOCADA"),
]

def normaliza_conta_dre(texto_bruto: str) -> tuple[str, str]:
    texto = texto_bruto.strip()
    for code, pattern, canonical in DRE_CORRECOES:
        if re.search(pattern, texto):
            return (code, canonical)
    return ('RAW', texto)
```

**Armadilhas**: C08 antes de C11 (ICMS vs ICMS-ST), CMV ⟷ CPV ⟷ Custo Produtos sinônimos.

---

## 5. API Endpoints (5)

```python
# backend/app/api/routes_dde.py
router = APIRouter(prefix="/api/dde", tags=["DDE"])
CANAIS_DDE = {'DIRETO', 'INDIRETO', 'FOOD_SERVICE'}

@router.get("/cliente/{cnpj}")
def get_dde_cliente(cnpj: str, ano: int = 2025): ...

@router.get("/consultor/{nome}")
def get_dde_consultor(nome: str, ano: int = 2025): ...

@router.get("/canal/{canal_id}")
def get_dde_canal(canal_id: int, ano: int = 2025): ...

@router.get("/comparativo")
def get_dde_comparativo(cnpjs: str, ano: int = 2025): ...  # csv

@router.get("/score/{cnpj}")
def get_dde_score(cnpj: str): ...
```

Canal scoping: HTTP 422 se CNPJ não pertence a DIRETO/INDIRETO/FOOD_SERVICE.
Multi-canal: usa `get_user_canal_ids` (já existente Onda 1 SAP).

---

## 6. Engine DDE — Fase A (Comercial sem CMV)

```python
@dataclass
class LinhaDRE:
    codigo: str
    conta: str
    sinal: str  # '+', '−', '='
    valor: Optional[Decimal] = None  # None = PENDENTE
    pct_receita: Optional[float] = None
    fonte: str = ''  # SH, SAP, LOG, CALC
    classificacao: str = 'PENDENTE'  # REAL|SINTETICO|PENDENTE|NULL
    fase: str = 'A'
    observacao: str = ''

def calcula_dre_comercial(cnpj: str, ano: int, db) -> ResultadoDDE:
    """
    Fase A: cascata sem L9-L10c (impostos, NULL) e sem L12-L13 (CMV/Margem Bruta, PENDENTE).
    Linhas REAL hoje: L1, L4, L19, I7, I8.
    Linhas REAL após D1: L5, L6, L7, L8.
    Linhas REAL após parsers CFO: L14, L16, L17.
    """
```

**Veredito determinístico:**
```python
def _veredito(dre: ResultadoDDE) -> tuple[str, str]:
    mc_pct = dre.indicadores.get('I2')
    if mc_pct is None: return ('SEM_DADOS', '...')
    if mc_pct < 0: return ('SUBSTITUIR', 'Margem negativa')
    if mc_pct < 0.05: return ('RENEGOCIAR', 'Margem < 5%')
    if mc_pct < 0.15: return ('REVISAR', 'Margem 5-15%')
    return ('SAUDAVEL', 'Manter')
```

---

## 7. Parsers (BaseParser + 5 específicos)

| Parser | Fonte | Tabela destino |
|--------|-------|----------------|
| `parser_zsdfat.py` | ZSDFAT_<cli>.xlsx | cliente_dre_periodo (usa 22 regex) |
| `parser_verbas.py` | Verbas xxxx.xlsx | cliente_verba_anual |
| `parser_frete.py` | Frete por Cliente.xlsx | cliente_frete_mensal |
| `parser_contratos.py` | Controle Contratos.xlsx | cliente_verba_anual (tipo=CONTRATO) |
| `parser_promotores.py` | Despesas Clientes V2.xlsx | cliente_promotor_mensal |

```python
class BaseParser(ABC):
    FONTE: str = 'LOG_UPLOAD'

    def validate_file(self, path) -> ValidationResult: ...
    @abstractmethod
    def extract(self, path) -> list[dict]: ...
    @abstractmethod
    def normalize(self, raw) -> list[Any]: ...
    def upsert(self, models, db) -> int: ...
    def run(self, path, db) -> dict:
        v = self.validate_file(path)
        if not v.ok: return {'status':'ERRO', 'errors':v.errors}
        return {'status':'OK', 'registros': self.upsert(self.normalize(self.extract(path)), db)}
```

---

## 8. Decisões Técnicas D1-D6

| # | Decisão | Status | Impacto |
|---|---------|--------|---------|
| D1 | Persistir 4 campos SH no Cliente | GO | Desbloqueia L5-L8 |
| D2 | routes_dde.py com 5 endpoints | GO | Desbloqueia frontend-backend |
| D3 | Impostos NULL honesto vs sintético | GO NULL | Honestidade > inventar |
| D4 | Implementar Fase A agora | GO | Não esperar SAP |
| D5 | comissao_pct: vendedor vs rebate | ABERTO | Afeta L15 vs L18 |
| D6 | RelatorioDeMargemPorProduto | URGENTE | Desbloqueia L12 (CMV) |

---

## 9. Canal Scoping

| Canal | DDE? | Motivo |
|-------|------|--------|
| DIRETO | SIM prioridade | dados completos |
| INDIRETO | SIM prioridade | distribuidores c/ contrato |
| FOOD_SERVICE | SIM (max) | dados parciais |
| INTERNO | NÃO | sem P&L "cliente" |
| FARMA | NÃO | base pequena |
| BODY | NÃO | base pequena |
| DIGITAL | NÃO | e-commerce, modelo diferente |

---

## 10. Ordem de Execução (6 Ondas — fonte de verdade do orquestrador)

```
Onda 1 — Schema + Migration       (MIKE)      ~2-3h
Onda 2 — Parsers + 22 regex       (NOVEMBER)  ~3-4h
Onda 3 — Engine DDE               (OSCAR)     ~3-4h
Onda 4 — API REST 5 endpoints     (PAPA)      ~2-3h
Onda 5 — UI React (DDE + AC)      (QUEBEC)    ~3-4h  [aguarda KILO done]
Onda 6 — LLM + PDF                (ROMEO)     futuro
```

Sequencial por dependência. Notification automática encadeia squads.

---

*Importado pelo @aios-master em 29/Abr/2026.*
