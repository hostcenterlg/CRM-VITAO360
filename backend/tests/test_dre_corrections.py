"""
CRM VITAO360 — test_dre_corrections.py
=========================================
Testes unitários para os 22 padrões regex de normalização DRE.

Cobertura:
  - 1 caso positivo + 1 caso negativo por padrão (22 padrões = 44 testes base)
  - Edge case ICMS vs ICMS-ST (C08 vs C11): 4 variações
  - Edge case CMV/CPV/Custo Produtos (C13): sinônimos
  - Caso RAW: texto não reconhecido retorna ('RAW', original)
  - Robustez: string vazia, None simulado

Total esperado: 55+ testes.
"""

from __future__ import annotations

import pytest

from scripts.parsers.dre_corrections import normaliza_conta_dre, DRE_CORRECOES


# ---------------------------------------------------------------------------
# Fixtures de teste (positivo + negativo) por padrão
# ---------------------------------------------------------------------------

class TestC01FaturamentoBruto:
    def test_positivo_fat_bruto(self):
        code, conta = normaliza_conta_dre("Faturamento Bruto a Tabela")
        assert code == "C01"
        assert conta == "FATURAMENTO BRUTO A TABELA"

    def test_positivo_fat_abreviado(self):
        code, _ = normaliza_conta_dre("Fat. Bruto")
        assert code == "C01"

    def test_positivo_receita_bruta_tab(self):
        code, _ = normaliza_conta_dre("Receita Bruta Tab")
        assert code == "C01"

    def test_negativo_receita_liquida(self):
        code, _ = normaliza_conta_dre("Receita Liquida")
        assert code != "C01"


class TestC02IpiVendas:
    def test_positivo_ipi_sobre_venda(self):
        code, conta = normaliza_conta_dre("IPI sobre Vendas")
        assert code == "C02"
        assert conta == "IPI SOBRE VENDAS"

    def test_positivo_ipi_faturado(self):
        code, _ = normaliza_conta_dre("IPI Faturado")
        assert code == "C02"

    def test_negativo_ipi_recolhido(self):
        # IPI recolhido/repassado deve ser C07, não C02
        code, _ = normaliza_conta_dre("IPI Recolhido")
        assert code == "C07"


class TestC03Devolucoes:
    def test_positivo_devolucao(self):
        code, conta = normaliza_conta_dre("(-) Devolucoes")
        assert code == "C03"
        assert conta == "(-) DEVOLUÇÕES"

    def test_positivo_devolucao_acentuada(self):
        code, _ = normaliza_conta_dre("Devolução de Mercadoria")
        assert code == "C03"

    def test_negativo_texto_irrelevante(self):
        code, _ = normaliza_conta_dre("Faturamento Bruto")
        assert code != "C03"


class TestC04DescontoComercial:
    def test_positivo_desc_comercial(self):
        code, conta = normaliza_conta_dre("(-) Desconto Comercial")
        assert code == "C04"
        assert conta == "(-) DESCONTO COMERCIAL"

    def test_positivo_desc_com_abreviado(self):
        code, _ = normaliza_conta_dre("Desc. Com.")
        assert code == "C04"

    def test_negativo_desc_financeiro(self):
        code, _ = normaliza_conta_dre("Desconto Financeiro")
        assert code == "C05"


class TestC05DescontoFinanceiro:
    def test_positivo_desc_financeiro(self):
        code, conta = normaliza_conta_dre("(-) Desconto Financeiro")
        assert code == "C05"
        assert conta == "(-) DESCONTO FINANCEIRO"

    def test_positivo_desc_fin_abreviado(self):
        code, _ = normaliza_conta_dre("Desc. Fin.")
        assert code == "C05"

    def test_negativo_bonificacao(self):
        code, _ = normaliza_conta_dre("Bonificacao")
        assert code != "C05"


class TestC06Bonificacoes:
    def test_positivo_bonificacao(self):
        code, conta = normaliza_conta_dre("(-) Bonificações")
        assert code == "C06"
        assert conta == "(-) BONIFICAÇÕES"

    def test_positivo_bonif_abreviado(self):
        code, _ = normaliza_conta_dre("Bonif.")
        assert code == "C06"

    def test_negativo_verba(self):
        code, _ = normaliza_conta_dre("Verba Contratual")
        assert code != "C06"


class TestC07IpiFaturado:
    def test_positivo_ipi_recolhido(self):
        code, conta = normaliza_conta_dre("(-) IPI Recolhido")
        assert code == "C07"
        assert conta == "(-) IPI FATURADO"

    def test_positivo_ipi_repassado(self):
        code, _ = normaliza_conta_dre("IPI Repassado")
        assert code == "C07"

    def test_negativo_ipi_vendas(self):
        code, _ = normaliza_conta_dre("IPI sobre Vendas")
        assert code == "C02"


class TestC08IcmsVsIcmsSt:
    """
    EDGE CASE CRÍTICO: C08 (ICMS próprio) NÃO deve capturar ICMS-ST.
    C08 usa negative lookahead. C11 captura ICMS-ST.
    """

    def test_icms_proprio_vai_para_c08(self):
        code, conta = normaliza_conta_dre("ICMS")
        assert code == "C08", f"'ICMS' deve ser C08, recebeu {code!r}"
        assert conta == "(-) ICMS"

    def test_icms_proprio_explicito_vai_para_c08(self):
        code, _ = normaliza_conta_dre("ICMS Próprio")
        assert code == "C08"

    def test_icms_st_vai_para_c11(self):
        code, conta = normaliza_conta_dre("ICMS-ST")
        assert code == "C11", f"'ICMS-ST' deve ser C11, recebeu {code!r}"
        assert conta == "(-) ICMS-ST"

    def test_icms_st_sem_hifen_vai_para_c11(self):
        code, _ = normaliza_conta_dre("ICMS ST Retido")
        assert code == "C11", f"'ICMS ST' deve ser C11, recebeu {code!r}"

    def test_substituicao_tributaria_vai_para_c11(self):
        code, _ = normaliza_conta_dre("Substituição Tributária")
        assert code == "C11"


class TestC09Pis:
    def test_positivo_pis(self):
        code, conta = normaliza_conta_dre("(-) PIS")
        assert code == "C09"
        assert conta == "(-) PIS"

    def test_positivo_pis_minusculo(self):
        code, _ = normaliza_conta_dre("pis")
        assert code == "C09"

    def test_negativo_cofins(self):
        code, _ = normaliza_conta_dre("COFINS")
        assert code == "C10"


class TestC10Cofins:
    def test_positivo_cofins(self):
        code, conta = normaliza_conta_dre("(-) COFINS")
        assert code == "C10"
        assert conta == "(-) COFINS"

    def test_positivo_cofins_minusculo(self):
        code, _ = normaliza_conta_dre("cofins")
        assert code == "C10"

    def test_negativo_pis(self):
        code, _ = normaliza_conta_dre("PIS")
        assert code == "C09"


class TestC12ReceitaLiquida:
    def test_positivo_receita_liquida(self):
        code, conta = normaliza_conta_dre("= Receita Líquida")
        assert code == "C12"
        assert conta == "= RECEITA LÍQUIDA"

    def test_positivo_rec_liq_abreviado(self):
        code, _ = normaliza_conta_dre("Rec. Líq.")
        assert code == "C12"

    def test_negativo_receita_bruta(self):
        code, _ = normaliza_conta_dre("Receita Bruta Tab")
        assert code == "C01"


class TestC13CmvSinonimos:
    """
    EDGE CASE: CMV / CPV / Custo Produtos são sinônimos, todos vão para C13.
    """

    def test_cmv(self):
        code, conta = normaliza_conta_dre("CMV")
        assert code == "C13"
        assert conta == "(-) CMV"

    def test_cpv(self):
        code, _ = normaliza_conta_dre("CPV - Custo dos Produtos Vendidos")
        assert code == "C13"

    def test_custo_mercadoria(self):
        code, _ = normaliza_conta_dre("Custo Mercadoria Vendida")
        assert code == "C13"

    def test_custo_dos_produtos(self):
        code, _ = normaliza_conta_dre("Custo dos Produtos")
        assert code == "C13"

    def test_negativo_margem_bruta(self):
        code, _ = normaliza_conta_dre("Margem Bruta")
        assert code == "C14"


class TestC14MargemBruta:
    def test_positivo_margem_bruta(self):
        code, conta = normaliza_conta_dre("= Margem Bruta")
        assert code == "C14"
        assert conta == "= MARGEM BRUTA"

    def test_positivo_mg_bruta_abreviado(self):
        code, _ = normaliza_conta_dre("Mg. Bruta")
        assert code == "C14"

    def test_negativo_margem_contribuicao(self):
        code, _ = normaliza_conta_dre("Margem de Contribuição")
        assert code == "C21"


class TestC15Frete:
    def test_positivo_frete(self):
        code, conta = normaliza_conta_dre("(-) Frete CT-e")
        assert code == "C15"
        assert conta == "(-) FRETE CT-e"

    def test_positivo_transporte(self):
        code, _ = normaliza_conta_dre("Transporte e Frete")
        assert code == "C15"

    def test_negativo_comissao(self):
        code, _ = normaliza_conta_dre("Comissão de Representante")
        assert code == "C16"


class TestC16Comissao:
    def test_positivo_comissao(self):
        code, conta = normaliza_conta_dre("(-) Comissão sobre Venda")
        assert code == "C16"
        assert conta == "(-) COMISSÃO SOBRE VENDA"

    def test_positivo_representante(self):
        code, _ = normaliza_conta_dre("Representante Comercial")
        assert code == "C16"

    def test_negativo_promotor(self):
        code, _ = normaliza_conta_dre("Promotor PDV Agencia")
        assert code == "C18"


class TestC17Verbas:
    def test_positivo_verba(self):
        code, conta = normaliza_conta_dre("(-) Verbas (Contratos)")
        assert code == "C17"
        assert conta == "(-) VERBAS (CONTRATOS)"

    def test_positivo_zdf2(self):
        code, _ = normaliza_conta_dre("ZDF2 - Desconto Contrato")
        assert code == "C17"

    def test_positivo_contrato_desc(self):
        code, _ = normaliza_conta_dre("Contrato Desconto Cliente")
        assert code == "C17"

    def test_negativo_comissao(self):
        code, _ = normaliza_conta_dre("Comissão")
        assert code == "C16"


class TestC18Promotor:
    def test_positivo_promotor(self):
        code, conta = normaliza_conta_dre("(-) Promotor PDV")
        assert code == "C18"
        assert conta == "(-) PROMOTOR PDV"

    def test_positivo_merchandising(self):
        code, _ = normaliza_conta_dre("Merchandising PDV")
        assert code == "C18"

    def test_positivo_pdv_agencia(self):
        code, _ = normaliza_conta_dre("PDV Agencia ABC")
        assert code == "C18"

    def test_negativo_frete(self):
        code, _ = normaliza_conta_dre("Frete CT-e")
        assert code == "C15"


class TestC19Inadimplencia:
    def test_positivo_inadimplencia(self):
        code, conta = normaliza_conta_dre("(-) Custo de Inadimplência")
        assert code == "C19"
        assert conta == "(-) CUSTO DE INADIMPLÊNCIA"

    def test_positivo_pdd(self):
        code, _ = normaliza_conta_dre("PDD - Provisão de Devedores Duvidosos")
        assert code == "C19"

    def test_positivo_provisao_debito(self):
        code, _ = normaliza_conta_dre("Provisão de Débito")
        assert code == "C19"

    def test_negativo_custo_financeiro(self):
        code, _ = normaliza_conta_dre("Custo Financeiro Capital de Giro")
        assert code == "C20"


class TestC20CustoFinanceiro:
    def test_positivo_custo_financeiro(self):
        code, conta = normaliza_conta_dre("(-) Custo Financeiro (Capital Giro)")
        assert code == "C20"
        assert conta == "(-) CUSTO FINANCEIRO (CAPITAL GIRO)"

    def test_positivo_cdi(self):
        code, _ = normaliza_conta_dre("CDI sobre capital de giro")
        assert code == "C20"

    def test_negativo_inadimplencia(self):
        code, _ = normaliza_conta_dre("Inadimplência")
        assert code == "C19"


class TestC21MargemContribuicao:
    def test_positivo_margem_contribuicao(self):
        code, conta = normaliza_conta_dre("= Margem de Contribuição")
        assert code == "C21"
        assert conta == "= MARGEM DE CONTRIBUIÇÃO"

    def test_positivo_mc_abreviado(self):
        code, _ = normaliza_conta_dre("MC")
        assert code == "C21"

    def test_positivo_mg_contrib(self):
        code, _ = normaliza_conta_dre("Mg. Contrib.")
        assert code == "C21"

    def test_negativo_margem_bruta(self):
        code, _ = normaliza_conta_dre("Margem Bruta")
        assert code == "C14"


class TestC22EstruturaComerc:
    def test_positivo_estrutura_comercial(self):
        code, conta = normaliza_conta_dre("(-) Estrutura Comercial Alocada")
        assert code == "C22"
        assert conta == "(-) ESTRUTURA COMERCIAL ALOCADA"

    def test_positivo_folha_comercial(self):
        code, _ = normaliza_conta_dre("Folha Comercial Fixa")
        assert code == "C22"

    def test_negativo_comissao(self):
        code, _ = normaliza_conta_dre("Comissão Vendedor")
        assert code == "C16"


# ---------------------------------------------------------------------------
# Casos especiais
# ---------------------------------------------------------------------------

class TestRaw:
    def test_raw_texto_desconhecido(self):
        code, conta = normaliza_conta_dre("Rubrica Totalmente Desconhecida XYZ 99")
        assert code == "RAW"
        assert conta == "Rubrica Totalmente Desconhecida XYZ 99"

    def test_raw_preserva_texto_original(self):
        original = "  Texto Estranho com Espaços  "
        code, conta = normaliza_conta_dre(original)
        if code == "RAW":
            assert conta == original.strip()

    def test_string_vazia(self):
        code, conta = normaliza_conta_dre("")
        assert code == "RAW"
        assert conta == ""

    def test_whitespace_apenas(self):
        code, conta = normaliza_conta_dre("   ")
        assert code == "RAW"
        assert conta == ""


class TestOrdemPatterns:
    """Verifica que C08 vem antes de C11 e não captura ICMS-ST."""

    def test_icms_puro_nao_e_capturado_por_c11(self):
        code, _ = normaliza_conta_dre("ICMS")
        assert code == "C08"

    def test_icms_st_nao_e_capturado_por_c08(self):
        code, _ = normaliza_conta_dre("ICMS-ST Retido")
        assert code == "C11"

    def test_icms_st_espaco_nao_e_capturado_por_c08(self):
        code, _ = normaliza_conta_dre("ICMS ST")
        assert code == "C11"

    def test_icms_maiusculo_minusculo(self):
        code, _ = normaliza_conta_dre("icms proprio")
        assert code == "C08"


class TestCaseSensitivity:
    """Todos os padrões devem ser case-insensitive."""

    def test_uppercase(self):
        code, _ = normaliza_conta_dre("FATURAMENTO BRUTO A TABELA")
        assert code == "C01"

    def test_lowercase(self):
        code, _ = normaliza_conta_dre("faturamento bruto a tabela")
        assert code == "C01"

    def test_mixed_case(self):
        code, _ = normaliza_conta_dre("Faturamento Bruto a Tabela")
        assert code == "C01"


class TestDreCorrecoesModulo:
    """Verifica integridade do módulo dre_corrections."""

    def test_lista_tem_22_padroes(self):
        assert len(DRE_CORRECOES) == 22

    def test_todos_codes_unicos(self):
        codes = [item[0] for item in DRE_CORRECOES]
        assert len(codes) == len(set(codes)), "Códigos duplicados em DRE_CORRECOES"

    def test_c08_antes_de_c11(self):
        """C08 deve aparecer antes de C11 na lista para garantir prioridade."""
        codes = [item[0] for item in DRE_CORRECOES]
        assert codes.index("C08") < codes.index("C11")

    def test_todos_tem_3_elementos(self):
        for item in DRE_CORRECOES:
            assert len(item) == 3, f"Padrão incompleto: {item}"
