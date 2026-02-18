#!/usr/bin/env python3
"""
Phase 10 Plan 03 Task 1: Generate Excel real test checklist (VAL-06)
Produces a step-by-step checklist in Portuguese for the user to validate
CRM_VITAO360_V13_FINAL.xlsx in Excel 365.
"""
import os
import json
from datetime import datetime

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'output', 'phase10')
CHECKLIST_PATH = os.path.join(OUTPUT_DIR, 'excel_test_checklist.txt')
V13_FINAL = os.path.join(OUTPUT_DIR, 'CRM_VITAO360_V13_FINAL.xlsx')

def generate_checklist():
    """Generate the Excel test checklist in Portuguese."""

    # Verify V13 FINAL exists
    if not os.path.exists(V13_FINAL):
        raise FileNotFoundError(f"V13 FINAL not found: {V13_FINAL}")

    file_size_mb = os.path.getsize(V13_FINAL) / (1024 * 1024)

    checklist = f"""========================================================
  CHECKLIST DE TESTE NO EXCEL - CRM VITAO360 V13 FINAL
========================================================

ARQUIVO: CRM_VITAO360_V13_FINAL.xlsx
LOCAL: data/output/phase10/
TAMANHO: {file_size_mb:.1f} MB
DATA: {datetime.now().strftime('%d/%m/%Y')}
REQUISITO: VAL-06 (Teste de abertura e recalculo no Excel real)

PRE-REQUISITO: Excel 365 ou Excel 2021+
(Versoes anteriores: tudo funciona EXCETO as 4 abas AGENDA)

========================================================
  COMO ABRIR O ARQUIVO
========================================================

1. Abra o arquivo no Excel (duplo-clique ou Arquivo > Abrir)
2. Se aparecer "Habilitar Edicao" ou "Habilitar Conteudo", clique SIM
3. Aguarde o Excel recalcular (pode levar 30-60 segundos com 154.302 formulas)
4. NAO feche o arquivo durante o recalculo

========================================================
  ITENS DE VERIFICACAO (marque [X] se OK)
========================================================

[ ] 1. ABERTURA: Arquivo abre sem erros de corrupcao
       - Nenhuma mensagem de "arquivo corrompido"
       - Nenhum aviso de "conteudo ilegivel"
       - Excel nao trava nem fecha sozinho

[ ] 2. ABAS (13 no total): Todas visiveis na barra inferior
       Abas principais:
       - PROJECAO, LOG, DASH, REDES_FRANQUIAS_v2, COMITE
       Abas de dados:
       - REGRAS, DRAFT 1, DRAFT 2, CARTEIRA
       Abas de agenda diaria:
       - AGENDA LARISSA, AGENDA DAIANE, AGENDA MANU, AGENDA JULIO

[ ] 3. PROJECAO - Formulas recalculam:
       - Coluna Z (REALIZADO) mostra valores em R$ (nao zero)
       - Colunas AA-AL (meses JAN-DEZ) mostram valores
       - Sinaleiros (emojis) aparecem corretamente nas colunas
       - Scroll ate o final: ~534 linhas de dados

[ ] 4. CARTEIRA - Formulas recalculam:
       - Bloco FATURAMENTO (colunas BZ-JC) mostra valores
       - SCORE RANKING (col JD) mostra numeros de 0 a 100
       - TEMPERATURA (col JE) mostra texto (QUENTE/MORNO/FRIO/GELADO)
       - Cores condicionais aparecem (verde/amarelo/vermelho)
       - 554 linhas de clientes (linhas 4 a 557)

[ ] 5. DASH - KPIs nao-zero:
       - TOTAL CONTATOS mostra numero > 0
       - TAXA CONVERSAO mostra percentual
       - Bloco PRODUTIVIDADE mostra dados por consultor
       - Numeros mudam se alterar o periodo (datas no topo)

[ ] 6. AGENDA (4 abas) - Dynamic arrays funcionam:
       - AGENDA LARISSA mostra lista filtrada de clientes
       - Coluna SCORE mostra numeros ordenados (maior para menor)
       - Dropdown RESULTADO funciona (clique na celula, aparece lista)
       - Dropdown MOTIVO funciona
       - Campo DATA (F1) mostra data de hoje
       NOTA: Se aparecer #NAME? nas AGENDA, seu Excel nao e 365.
             Isso e esperado e NAO invalida o teste (item 6 = PASS_WITH_NOTES)

[ ] 7. REDES_FRANQUIAS_v2 - Sinaleiro de redes:
       - 20 redes listadas com dados (+ 1 linha SEM GRUPO)
       - RANK mostra numeros 1-20
       - META 6M mostra valores em R$
       - Linha TOTAL no final com soma

[ ] 8. COMITE - Filtros interativos:
       - Dropdown VENDEDOR (celula I2) funciona
       - Ao trocar vendedor, numeros mudam automaticamente
       - RATEIO toggle funciona (3 opcoes diferentes)
       - 5 blocos de dados visiveis

[ ] 9. AGRUPAMENTO - Botoes [+] funcionam:
       - Na CARTEIRA, clicar [+] expande sub-grupos de colunas
       - Na PROJECAO, agrupamentos de meses funcionam
       - Clicar [-] recolhe os grupos novamente

[ ] 10. SALVAMENTO: Salvar sem erros
        - Ctrl+S ou Arquivo > Salvar
        - Nenhum erro ao salvar
        - Arquivo salvo mantem todas as funcionalidades
        - Ao reabrir, tudo continua funcionando

========================================================
  RESULTADO
========================================================

Se TODOS os 10 itens estao [X]:
  >> VAL-06 = PASS
  >> Responda: "TODOS OK"

Se itens 1-5 e 7-10 OK mas item 6 falha (#NAME? nas AGENDA):
  >> VAL-06 = PASS_WITH_NOTES
  >> Responda: "AGENDA falhou, resto OK"
  >> (AGENDA requer Excel 365; demais funcionalidades estao OK)

Se qualquer item 1-5 ou 7-10 falha:
  >> VAL-06 = FAIL
  >> Responda: "Item X falhou: [descreva o erro]"
  >> (Anotar qual item falhou e descrever o que apareceu na tela)

========================================================
  DEPOIS DO TESTE
========================================================

Informe o resultado ao Claude para finalizar o projeto.
Respostas aceitas:
  - "TODOS OK" (tudo perfeito)
  - "AGENDA falhou, resto OK" (aceitavel, Excel nao e 365)
  - "Item X falhou: [descricao]" (precisa correcao)

========================================================
  INFORMACOES TECNICAS
========================================================

Total de formulas: 154.302
Total de abas: 13
Total de clientes: 554
Total de registros LOG: 20.830
Consultores: LARISSA, DAIANE, HEMANUELE (MANU), JULIO
Tamanho do arquivo: {file_size_mb:.1f} MB

Gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Fase 10 - Validacao Final - Plano 03 - VAL-06
"""

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Write the checklist file
    with open(CHECKLIST_PATH, 'w', encoding='utf-8') as f:
        f.write(checklist)

    print(f"Checklist gerado com sucesso: {CHECKLIST_PATH}")
    print(f"Tamanho: {os.path.getsize(CHECKLIST_PATH)} bytes")
    print(f"Linhas: {len(checklist.splitlines())}")
    print()
    print("=" * 60)
    print("  CONTEUDO DO CHECKLIST")
    print("=" * 60)
    print()
    print(checklist)

    return CHECKLIST_PATH


def verify_checklist(path):
    """Verify the generated checklist meets plan requirements."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.splitlines()

    checks = {
        'file_exists': os.path.exists(path),
        'min_30_lines': len(lines) >= 30,
        'has_10_items': content.count('[ ] ') >= 10,
        'in_portuguese': 'VERIFICACAO' in content and 'RESULTADO' in content,
        'references_v13_final': 'CRM_VITAO360_V13_FINAL' in content,
        'has_pass_criteria': 'VAL-06 = PASS' in content,
        'has_fail_criteria': 'VAL-06 = FAIL' in content,
        'has_pass_with_notes': 'PASS_WITH_NOTES' in content,
        'has_pre_requisite': 'Excel 365' in content,
        'has_instructions': 'COMO ABRIR' in content or 'INSTRUCOES' in content,
    }

    print("\n" + "=" * 60)
    print("  VERIFICACAO DO CHECKLIST")
    print("=" * 60)

    all_pass = True
    for check, result in checks.items():
        status = "PASS" if result else "FAIL"
        if not result:
            all_pass = False
        print(f"  [{status}] {check}")

    print(f"\n  Total linhas: {len(lines)}")
    print(f"  Total itens [ ]: {content.count('[ ] ')}")
    print(f"  Resultado geral: {'PASS' if all_pass else 'FAIL'}")

    return all_pass


if __name__ == '__main__':
    path = generate_checklist()
    verify_checklist(path)
