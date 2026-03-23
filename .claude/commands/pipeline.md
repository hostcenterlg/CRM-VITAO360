---
description: "Pipeline Completo do CRM"
---

Pipeline de build do CRM VITAO360:
1. @data-engineer: Cruzar fontes (Mercos/SAP/Deskrio)
2. @dev: Build Excel com openpyxl
3. @qa: Validação (Two-Base, CNPJ, fórmulas, faturamento)
4. @ux: Formatação e dashboard
5. @devops: Commit e deploy
