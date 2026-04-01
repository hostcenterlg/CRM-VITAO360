# Sales Hunter — Dados Extraídos

Pasta de dados extraídos automaticamente do Sales Hunter (SAP Web).
URL: saleshunter.vitao.com.br

## Estrutura

```
sales_hunter/
├── YYYY-MM-DD/
│   ├── morning/     (extração 08:00)
│   └── night/       (extração 20:00)
└── weekly/          (relatórios P2, segundas-feiras)
```

## Naming Convention

`{tipo}_{empresa}_{vendedor}_{YYYY-MM-DD}_{HHmm}.csv`

| Campo | Valores |
|-------|---------|
| tipo | fat_cliente, fat_nf_det, fat_produto, fat_empresa, carteira, debitos, devolucao_cliente, pedidos_produto |
| empresa | cwb, vv, all |
| vendedor | MANU, LARISSA, DAIANE, JULIO, all |
| data | YYYY-MM-DD |
| hora | 0800, 2000 |

## Classificação: REAL

Todos os dados desta pasta são Tier REAL (fonte SAP direta).
NUNCA misturar com dados SINTÉTICOS ou ALUCINAÇÃO.

## Consumo

VSCode roda `backend/scripts/ingest_sales_hunter.py` para popular PostgreSQL.
