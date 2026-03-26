---
name: saas-deploy-checklist
type: checklist
squad: crm-saas
description: "Checklist de deploy para features SaaS do CRM VITAO360"
---

# SaaS Deploy Checklist

## Blocking (DEVE passar)

- [ ] Two-Base Architecture respeitada (VENDA=R$, LOG=R$0.00)
- [ ] CNPJ = string 14 dígitos em todo o código
- [ ] Faturamento baseline R$ 2.091.000 (±0.5%)
- [ ] 0 dados ALUCINAÇÃO integrados
- [ ] pytest PASS (0 failures)
- [ ] API endpoints respondem HTTP 200
- [ ] JWT auth funcional (login, token refresh)
- [ ] Frontend renderiza sem erros de console
- [ ] Detector de Mentira N1+N2+N3 PASS

## Advisory (deveria passar)

- [ ] Coverage > 80% nos services
- [ ] Lighthouse score > 90
- [ ] Sem TODO/FIXME em código commitado
- [ ] OpenAPI spec atualizada
- [ ] README atualizado com novas features
