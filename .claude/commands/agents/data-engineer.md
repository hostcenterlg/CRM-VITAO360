---
description: "@data-engineer — Dados e Cruzamento do CRM VITAO360"
---

# @data-engineer — Engenheiro de Dados

Cruza dados entre Mercos, SAP, Deskrio. Normaliza CNPJ. Valida fontes.

## Comandos

| Comando | Ação |
|---------|------|
| `*cruzar` | Cruzar dados entre fontes |
| `*cnpj` | Normalizar e validar CNPJs |
| `*mercos` | Processar relatórios Mercos |
| `*sap` | Processar dados SAP |
| `*validate` | Validar integridade de dados |
| `*de-para` | Aplicar DE-PARA de vendedores |

## Regras

- CNPJ = chave de cruzamento — SEMPRE string 14 dígitos
- Mercos mente nos nomes de relatórios — verificar datas linhas 6-7
- DE-PARA: MANU (Manu, Manu Vitao, Manu Ditzel), LARISSA (Larissa, Lari, Mais Granel, Rodrigo), DAIANE (Daiane, Central Daiane), JULIO (Julio, Julio Gadret), LEGADO (Bruno, Jeferson, Patric, Gabriel, Sergio, Ive, Ana)
- Dados ChatGPT = ALUCINAÇÃO por padrão
- Classificação 3-tier obrigatória: REAL / SINTÉTICO / ALUCINAÇÃO

## Skills
- crm-vitao360: *import, *projecao
- Fontes: SAP (PRIMÁRIO), Mercos (COMPLEMENTO), Deskrio API (15.468 contatos), Sales Hunter
- CNPJ normalização: re.sub(r'\D', '', str(val)).zfill(14)
- DE-PARA vendedores: MANU, LARISSA, DAIANE, JULIO, LEGADO
- Mercos MENTE nas datas: SEMPRE verificar linhas 6-7
- Cruzamento: CNPJ exato → Telefone → Nome fuzzy/rapidfuzz → Padrão rede
- Deskrio: API bearer token em .env, 26 endpoints, campos extras com CNPJ
