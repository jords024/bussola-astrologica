# -*- coding: utf-8 -*-
"""Testes do bloco de FATOS que vai para o modelo.

O que o modelo NAO recebe, ele nao pode escrever. Por isso estes testes olham
o conteudo do bloco, e nao a carta: e aqui que se decide se a leitura fala da
vida da pessoa ou so do sentimento dela.
"""
import unittest
from datetime import date


class MaterialConcreto(unittest.TestCase):
    """O bloco da Parte 1 precisa levar ONDE e QUANDO.

    Antes daqui saiam sete linhas abstratas - o que chega, o que e tocado,
    como se encontram, forca, janela - e a casa e a data ficavam calculadas e
    jogadas fora. Sem elas o modelo so tinha material para falar de sentimento,
    e a carta virava horoscopo bonito.
    """

    def _ident(self, **kw):
        from servicos.aspectos import AspectoNorm
        from servicos.lentos import Identificacao
        base = dict(transito="Saturn", natal="Sun", aspecto="square",
                    orbe=0.5, orbe_max=5.0, movimento="Applying",
                    velocidade=0.07, casa_transito=5, casa_natal=8)
        base.update(kw)
        a = AspectoNorm(**base)
        return Identificacao(1, a.transito, aspecto=a, forca=1.0), a

    def test_leva_a_casa_onde_acontece(self):
        from servicos.fatos import bloco_identificacao
        from servicos.nomes import CASA_VIDA
        ident, _ = self._ident()
        texto = bloco_identificacao(ident, date(2026, 9, 25), casas_ok=True)
        self.assertIn("ONDE isso esta acontecendo", texto)
        self.assertIn(CASA_VIDA[5], texto)
        self.assertIn(CASA_VIDA[8], texto)

    def test_sem_casas_confiaveis_nao_cita_casa(self):
        """Fingir precisao e exatamente o que o Crassus combate."""
        from servicos.fatos import bloco_identificacao
        from servicos.nomes import CASA_VIDA
        ident, _ = self._ident()
        texto = bloco_identificacao(ident, date(2026, 9, 25), casas_ok=False)
        self.assertNotIn("ONDE isso esta acontecendo", texto)
        self.assertNotIn(CASA_VIDA[5], texto)

    def test_leva_a_data_aproximada(self):
        from servicos.fatos import bloco_identificacao
        ident, _ = self._ident(orbe=2.1, velocidade=0.07)   # ~30 dias
        texto = bloco_identificacao(ident, date(2026, 9, 25), casas_ok=True)
        self.assertIn("QUANDO:", texto)
        self.assertIn("outubro", texto)

    def test_exato_hoje_e_dito_como_hoje(self):
        from servicos.fatos import bloco_identificacao
        ident, _ = self._ident(orbe=0.02, velocidade=0.07)
        texto = bloco_identificacao(ident, date(2026, 9, 25), casas_ok=True)
        self.assertIn("HOJE", texto)

    def test_leva_o_segundo_transito_e_o_atrito(self):
        from servicos.aspectos import AspectoNorm
        from servicos.fatos import bloco_identificacao
        from servicos.lentos import Identificacao
        from servicos.nomes import CASA_VIDA
        _, a = self._ident()
        s = AspectoNorm(transito="Uranus", natal="Moon", aspecto="square",
                        orbe=1.0, orbe_max=5.0, movimento="Applying",
                        velocidade=0.012, casa_transito=7, casa_natal=4)
        ident = Identificacao(1, a.transito, aspecto=a, forca=1.0, segundo=s)
        texto = bloco_identificacao(ident, date(2026, 9, 25), casas_ok=True)
        self.assertIn("SEGUNDO movimento", texto)
        self.assertIn(CASA_VIDA[7], texto)
        self.assertIn("COMO USAR OS DOIS", texto)

    def test_sem_segundo_nao_fala_de_dois(self):
        from servicos.fatos import bloco_identificacao
        ident, _ = self._ident()
        texto = bloco_identificacao(ident, date(2026, 9, 25), casas_ok=True)
        self.assertNotIn("SEGUNDO movimento", texto)


class JanelaAplicando(unittest.TestCase):
    """Um aspecto que ainda aplica nao acaba no exato: passa por ele e continua
    pesando ate sair do orbe do outro lado."""

    def test_aplicando_conta_o_orbe_inteiro_depois_do_exato(self):
        from servicos.aspectos import AspectoNorm
        from servicos.fatos import janela_em_palavras
        # exato hoje, mas com 5 graus de orbe a 0,077/dia ainda pesa ~65 dias
        a = AspectoNorm(transito="Saturn", natal="Sun", aspecto="square",
                        orbe=0.03, orbe_max=5.0, movimento="Applying",
                        velocidade=0.077)
        texto = janela_em_palavras(a, date(2026, 9, 25))
        self.assertNotIn("proximos dias", texto)
        self.assertNotIn("próximos dias", texto)

    def test_separando_conta_so_o_que_falta_para_sair(self):
        from servicos.aspectos import AspectoNorm
        from servicos.fatos import janela_em_palavras
        a = AspectoNorm(transito="Saturn", natal="Sun", aspecto="square",
                        orbe=4.8, orbe_max=5.0, movimento="Separating",
                        velocidade=0.077)
        self.assertIn("próximos dias", janela_em_palavras(a, date(2026, 9, 25)))


class _PortaFalsa:
    """Uma porta minima, so com o que bloco_porta le."""
    def __init__(self, casa, planetas=("Sun", "Mercury")):
        self.casa = casa
        self.planetas = planetas
        self.empate = False
        self.forca = 3.0


class EloComOAperto(unittest.TestCase):
    """A porta tem que responder ao aperto, nao anunciar um territorio.

    Antes a Parte 1 diagnosticava e a Parte 2 anunciava, sem nada ligando as
    duas. A pessoa lia sobre a propria confusao num bloco e sobre estudo no
    outro, e saia sem entender por que aquilo era resposta. O elo e calculado
    aqui para o modelo nao ter que inventar.
    """

    def test_o_elo_junta_o_que_o_aperto_pede_com_o_que_a_casa_da(self):
        from servicos.fatos import bloco_porta
        from servicos.lentos import Identificacao
        from servicos.nomes import CASA_PORTA, PLANETA_ALIVIO
        texto = bloco_porta(_PortaFalsa(9), False, 2, "o dinheiro",
                            Identificacao(1, "Neptune"))
        self.assertIn("O ELO COM O APERTO DA PARTE 1", texto)
        # o que Netuno faz a pessoa precisar
        self.assertIn(PLANETA_ALIVIO["Neptune"], texto)
        # o que a casa 9 entrega
        self.assertIn(CASA_PORTA[9][0], texto)

    def test_cada_lento_pede_uma_coisa_diferente(self):
        """Sem isto o elo viraria a mesma frase para todo mundo."""
        from servicos.fatos import bloco_porta
        from servicos.lentos import Identificacao
        vistos = set()
        for planeta in ("Saturn", "Uranus", "Neptune", "Pluto"):
            texto = bloco_porta(_PortaFalsa(9), False, 2, "o dinheiro",
                                Identificacao(1, planeta))
            self.assertIn("O ELO COM O APERTO", texto)
            vistos.add(texto)
        self.assertEqual(len(vistos), 4)

    def test_sem_identificacao_a_porta_nao_inventa_elo(self):
        """Quando nada lento toca Sol ou Lua, nao ha aperto para responder."""
        from servicos.fatos import bloco_porta
        texto = bloco_porta(_PortaFalsa(9), False, 2, "o dinheiro", None)
        self.assertNotIn("O ELO COM O APERTO", texto)

    def test_planeta_rapido_na_parte_1_nao_gera_elo(self):
        """So os quatro lentos tem alivio mapeado; o resto passa em branco."""
        from servicos.fatos import bloco_porta
        from servicos.lentos import Identificacao
        texto = bloco_porta(_PortaFalsa(9), False, 2, "o dinheiro",
                            Identificacao(2, "Jupiter"))
        self.assertNotIn("O ELO COM O APERTO", texto)
