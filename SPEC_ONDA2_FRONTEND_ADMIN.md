# SPEC ONDA 2 — Seletor de Canal + Admin + Scoping Restante

> Sem seletor de canal, o usuário não escolhe o que ver. Sem admin, ninguém gerencia.
> Gerado: 26/Abr/2026 | Autor: Cowork (professor/revisor)

---

## TASK 1: Seletor de Canal no Header (Frontend)

### UX Definida (DECISÃO L3 Leandro)
- Cada usuário seleciona qual canal quer ver
- Admin vê TODOS ou seleciona um específico
- Consultor vê apenas os canais que o admin liberou
- Gerente vê os canais que gerencia (Daiane: INTERNO + FOOD_SERVICE)
- Seleção persiste na sessão (não no localStorage — usar React state + cookie httpOnly)

### Componente: `<CanalSelector />`

```tsx
// frontend/src/components/CanalSelector.tsx
// Localização: Header, ao lado do nome do usuário

// 1. Ao logar, buscar canais permitidos:
//    GET /api/canais/meus → [{id: 1, nome: "INTERNO", status: "ATIVO"}, ...]

// 2. Se usuário tem apenas 1 canal → não mostrar seletor (fixo)
//    Se admin → mostrar "Todos" + lista de canais
//    Se gerente → mostrar canais que gerencia
//    Se consultor → mostrar canais liberados

// 3. Ao trocar canal:
//    - Atualizar header "Canal: INTERNO" (badge verde)
//    - Enviar canal_id como query param ou header em todas requisições
//    - Recarregar dados da página atual

// 4. Visual:
//    - Dropdown compacto no header (não modal)
//    - Cor do badge = cor do canal (ATIVO=#00B050, EM_BREVE=#FFC000)
//    - Texto: nome do canal (ex: "INTERNO", "FOOD SERVICE", "DIRETO")
```

### Backend: GET /api/canais/meus (já existe parcialmente)

```python
# Endpoint retorna canais do usuário logado
# Admin: todos canais
# Outros: apenas os da tabela usuario_canal

@router.get("/meus")
def canais_do_usuario(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CanalSchema]:
    if user.role == "admin":
        return db.scalars(select(Canal).order_by(Canal.nome)).all()
    canal_ids = [uc.canal_id for uc in user.usuario_canais]
    return db.scalars(
        select(Canal).where(Canal.id.in_(canal_ids)).order_by(Canal.nome)
    ).all()
```

### Propagação do Canal Selecionado

```typescript
// Opção A (RECOMENDADA): Context + query param
// CanalContext fornece canal_id selecionado para toda a app
// Cada fetch inclui ?canal_id=X (ou header X-Canal-Id)

// Opção B: Cookie httpOnly
// Menos intrusivo mas requer middleware no backend

// Backend: deps.py já tem get_user_canal_ids
// Adicionar: se query param canal_id presente E está nos canais do user,
// filtrar APENAS por aquele canal (não todos permitidos)
```

---

## TASK 2: Admin Gestão de Canais por Usuário

### Endpoint: /api/usuarios/{id}/canais

```python
# PUT /api/usuarios/{id}/canais
# Body: {"canal_ids": [1, 2]}
# Requer: role=admin
# Efeito: substitui ACL do usuário (delete all + insert new)

@router.put("/{usuario_id}/canais")
@require_admin
def atualizar_canais_usuario(
    usuario_id: int,
    body: CanalIdsRequest,  # {"canal_ids": [1, 2]}
    db: Session = Depends(get_db),
) -> dict:
    # 1. Verificar que usuario existe
    # 2. Verificar que todos canal_ids existem na tabela canais
    # 3. Deletar todos UsuarioCanal do usuario
    # 4. Insertar novos UsuarioCanal
    # 5. Retornar {"usuario_id": X, "canais": [...]}
```

### Frontend: Tela de Admin (existente em /usuarios)

```
Adicionar na tela de edição de usuário:
- Seção "Canais de Acesso"
- Checkboxes com todos os canais disponíveis
- Canais ATIVO em verde, EM_BREVE em amarelo, BLOQUEADO em cinza
- Botão "Salvar Permissões"
```

---

## TASK 3: Scoping nos 4 Routers Restantes

### routes_relatorios.py

```python
# DECISÃO: exportação filtrada pelo canal selecionado + cabeçalho
# Header do Excel: "CRM VITAO360 | Canal: {nome_canal} | Período: {periodo}"
# Se admin sem canal selecionado: "Todos os Canais"

# Aplicar mesmo padrão:
user_canal_ids = Depends(get_user_canal_ids)
# + filtro por canal_id do query param (se seletor ativo)
```

### routes_whatsapp.py

```python
# Consulta Deskrio por CNPJ — precisa verificar que CNPJ pertence
# a cliente de canal permitido do usuário.
# Se CNPJ não está no canal do user → 403
```

### routes_pipeline.py

```python
# Notificações podem conter CNPJ — filtrar por canal
# Pipeline cards do Deskrio kanban → filtrar por canal do cliente
```

### routes_ia.py

```python
# Recebe CNPJ como input para briefing/análise
# Verificar que CNPJ pertence a canal permitido antes de gerar resposta
# Se não pertence → 403 "Cliente fora do seu escopo de canais"
```

---

## TASK 4: Dashboard Endpoints Restantes (16)

### Padrão rápido (copiar dos já feitos)

```python
# Todos seguem o mesmo padrão de /kpis e /top10:
# 1. Adicionar get_user_canal_ids dependency
# 2. Aplicar cliente_canal_filter ou cnpjs_permitidos_subquery
# 3. Adicionar filtro consultor para role consultor/consultor_externo
# 4. Testar com 3 perfis (admin, gerente, consultor)
```

### Endpoints pendentes (por prioridade)
1. /api/dashboard/distribuicao — mapa de clientes por UF
2. /api/dashboard/projecao — agregado mensal
3. /api/dashboard/indicadores — KPIs secundários
4. /api/dashboard/funil — estágios do funil
5. /api/dashboard/evolucao — série temporal
6. /api/dashboard/atividade — log de atividades
7-16. Demais (menor prioridade, uso futuro)

---

## VALIDAÇÃO

### Nível 1 — Existência
- [ ] CanalSelector.tsx criado e renderiza no header
- [ ] PUT /api/usuarios/{id}/canais funciona
- [ ] 4 routers com scoping aplicado

### Nível 2 — Substância
- [ ] Admin vê seletor com "Todos" + lista
- [ ] Consultor vê apenas canais liberados
- [ ] Troca de canal recarrega dados da página
- [ ] Excel exportado tem cabeçalho com canal

### Nível 3 — Conexão
- [ ] Seletor persiste durante sessão
- [ ] Todos endpoints respeitam canal selecionado
- [ ] 403 quando acessa CNPJ fora do canal
- [ ] Admin consegue gerenciar canais de outros usuários

---

*Spec revisada. VSCode implementa na ordem: Task 1 (seletor) → Task 3 (scoping) → Task 2 (admin) → Task 4 (dashboard).*
