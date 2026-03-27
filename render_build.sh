#!/bin/bash
set -e

echo "=== [1/4] Instalando dependencias ==="
pip install -r backend/requirements.txt

echo "=== [2/4] Criando banco ==="
python -c "
from backend.app.database import engine, Base
from backend.app.models import cliente, log_interacao, venda, regra_motor, usuario, meta, rede, rnc, score_historico, agenda, import_job, audit_log
Base.metadata.create_all(bind=engine)
print('OK: tabelas criadas')
"

echo "=== [3/4] Seed motor + usuarios ==="
python -c "
from backend.app.database import SessionLocal
from backend.app.services.seed_auth import seed_usuarios, seed_regras_motor
db = SessionLocal()
n_u = seed_usuarios(db)
n_r = seed_regras_motor(db)
db.close()
print(f'OK: {n_u} usuarios, {n_r} regras')
"

echo "=== [4/4] Populando dados do JSON seed ==="
python -c "
import json
from pathlib import Path
from backend.app.database import SessionLocal
from backend.app.models.cliente import Cliente
from backend.app.models.venda import Venda
from backend.app.models.meta import Meta
from backend.app.models.log_interacao import LogInteracao
from backend.app.models.rede import Rede

seed_path = Path('data/seed_data.json')
if not seed_path.exists():
    print('WARN: seed_data.json nao encontrado, pulando')
    exit(0)

data = json.loads(seed_path.read_text(encoding='utf-8'))
db = SessionLocal()

# Clientes
if db.query(Cliente).count() == 0:
    for r in data.get('clientes', []):
        r.pop('id', None)
        r.pop('created_at', None)
        r.pop('updated_at', None)
        db.add(Cliente(**r))
    db.commit()
    print(f'OK: {len(data.get(\"clientes\",[]))} clientes')

# Vendas
if db.query(Venda).count() == 0:
    for r in data.get('vendas', []):
        r.pop('id', None)
        db.add(Venda(**r))
    db.commit()
    print(f'OK: {len(data.get(\"vendas\",[]))} vendas')

# Metas
if db.query(Meta).count() == 0:
    for r in data.get('metas', []):
        r.pop('id', None)
        db.add(Meta(**r))
    db.commit()
    print(f'OK: {len(data.get(\"metas\",[]))} metas')

# Logs
if db.query(LogInteracao).count() == 0:
    for r in data.get('log_interacoes', []):
        r.pop('id', None)
        r.pop('created_at', None)
        db.add(LogInteracao(**r))
    db.commit()
    print(f'OK: {len(data.get(\"log_interacoes\",[]))} logs')

# Redes
if db.query(Rede).count() == 0:
    for r in data.get('redes', []):
        r.pop('id', None)
        r.pop('updated_at', None)
        db.add(Rede(**r))
    db.commit()
    print(f'OK: {len(data.get(\"redes\",[]))} redes')

db.close()
print('=== Seed completo ===')
"

echo "=== BUILD COMPLETO ==="
