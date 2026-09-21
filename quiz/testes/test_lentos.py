# -*- coding: utf-8 -*-
"""Testes da Parte 1: o transito que gera identificacao.

Cada teste aqui corresponde a um jeito concreto de a cascata eleger errado.
"""
import unittest

from servicos.aspectos import AspectoNorm, PresencaNorm
from servicos.lentos import (GRAUS_DE_ENTRADA, Perfil, eleger_identificacao,
                             forca_identificacao)


def asp(transito, natal, aspecto, orbe, movimento="Applying", orbe_max=10.0,
        velocidade=0.05):
    return AspectoNorm(transito=transito, natal=natal, aspecto=aspecto,
                       orbe=orbe, orbe_max=orbe_max, movimento=movimento,
                       velocidade=velocidade)


def pres(planeta, casa, graus):
    return PresencaNorm(planeta=planeta, casa=casa, graus_na_casa=graus)


class Criterio1(unittest.TestCase):
    def test_aspecto_fechado_vence_e_a_cascata_para(self):
        """Com aspecto <=5 graus, o criterio 2 nem e consultado."""
        r = eleger_identificacao(
            [asp("Saturn", "Sun", "square", 2.0)],
            [pres("Pluto", 8, 1.0)],
        )
        self.assertEqual(r.criterio, 1)
        self.assertEqual(r.planeta, "Saturn")
        self.assertIsNone(r.casa)

    def test_nao_ha_ordem_fixa_de_planeta(self):
        """Saturno apertando vence Plutao largo. Uma constante global daria
        Plutao a 61% das pessoas - medido em 60 mapas."""
        r = eleger_identificacao([
            asp("Saturn", "Sun", "square", 1.0),
            asp("Pluto", "Moon", "trine", 4.0),
        ])
        self.assertEqual(r.planeta, "Saturn")

    def test_aspecto_duro_vence_aspecto_suave_no_mesmo_orbe(self):
        """Quadratura e o que se SENTE. Sem o peso do tipo, o trigono passava
        na frente so por tolerar orbe maior."""
        quad = asp("Saturn", "Sun", "square", 2.0)
        trig = asp("Saturn", "Sun", "trine", 2.0)
        self.assertGreater(forca_identificacao(quad), forca_identificacao(trig))

    def test_mesmo_aspecto_mais_exato_vence(self):
        perto = asp("Saturn", "Sun", "square", 0.5)
        longe = asp("Saturn", "Sun", "square", 4.5)
        self.assertGreater(forca_identificacao(perto), forca_identificacao(longe))

    def test_orbe_desempata_entre_iguais(self):
        r = eleger_identificacao([
            asp("Neptune", "Moon", "sextile", 4.9),
            asp("Neptune", "Sun", "opposition", 0.4),
        ])
        self.assertEqual(r.aspecto.natal, "Sun")

    def test_regencia_do_mapa_dela_muda_a_escolha(self):
        """O mesmo par de transitos decide diferente em dois mapas diferentes.
        E isso que impede a leitura de ser igual para todo mundo."""
        par = [asp("Saturn", "Sun", "trine", 3.0),
               asp("Uranus", "Sun", "trine", 2.6)]
        sem = eleger_identificacao(par)
        com = eleger_identificacao(par, perfil=Perfil(regentes=frozenset({"Saturn"})))
        self.assertEqual(sem.planeta, "Uranus")
        self.assertEqual(com.planeta, "Saturn")

    def test_planeta_estacionario_pesa_mais(self):
        """Parar em cima do ponto dela e evento de vida, nao passagem."""
        andando = asp("Pluto", "Sun", "square", 2.0, velocidade=0.04)
        parado = asp("Pluto", "Sun", "square", 2.0, velocidade=0.001)
        self.assertGreater(forca_identificacao(parado), forca_identificacao(andando))

    def test_ponto_angular_pesa_mais_naquele_mapa(self):
        a = asp("Neptune", "Moon", "square", 2.0)
        perto = Perfil(peso_lua=1.6)
        self.assertGreater(forca_identificacao(a, perto), forca_identificacao(a))

    def test_mesma_entrada_da_sempre_a_mesma_saida(self):
        """Sem desempate final, a escolha dependeria da ordem da lista."""
        par = [asp("Uranus", "Sun", "trine", 2.0), asp("Neptune", "Sun", "trine", 2.0)]
        self.assertEqual(eleger_identificacao(par).planeta,
                         eleger_identificacao(list(reversed(par))).planeta)

    def test_saturno_vence_quando_nao_ha_mais_lento(self):
        r = eleger_identificacao([asp("Saturn", "Moon", "conjunction", 4.8)])
        self.assertEqual(r.planeta, "Saturn")

    def test_conjuncao_conta(self):
        """Ficou de fora da lista original; sem ela, o caso mais forte some."""
        r = eleger_identificacao([asp("Pluto", "Sun", "conjunction", 1.1)])
        self.assertEqual(r.criterio, 1)

    def test_orbe_acima_de_cinco_cai_para_criterio_4(self):
        r = eleger_identificacao([asp("Pluto", "Sun", "square", 5.1)])
        self.assertEqual(r.criterio, 4)   # aplicando: esta a caminho

    def test_ignora_planeta_rapido(self):
        self.assertIsNone(eleger_identificacao([asp("Venus", "Sun", "trine", 0.5)]))

    def test_ignora_ponto_natal_que_nao_seja_sol_ou_lua(self):
        self.assertIsNone(eleger_identificacao([asp("Pluto", "Venus", "square", 1.0)]))

    def test_ignora_aspecto_menor(self):
        self.assertIsNone(eleger_identificacao([asp("Pluto", "Sun", "quintile", 0.5)]))


class Criterio2(unittest.TestCase):
    def test_lento_recem_entrado_na_casa(self):
        r = eleger_identificacao([], [pres("Uranus", 4, 3.2)])
        self.assertEqual(r.criterio, 2)
        self.assertEqual((r.planeta, r.casa), ("Uranus", 4))

    def test_no_limite_entra(self):
        r = eleger_identificacao([], [pres("Saturn", 9, GRAUS_DE_ENTRADA)])
        self.assertEqual(r.criterio, 2)

    def test_passou_do_limite_nao_entra(self):
        """A 11 graus ja e paisagem, nao evento."""
        self.assertIsNone(eleger_identificacao([], [pres("Saturn", 9, 11.0)]))

    def test_sem_hora_confiavel_nao_ha_criterio_2(self):
        """graus_na_casa None e o sinal de que casa nao vale nesta leitura."""
        self.assertIsNone(eleger_identificacao([], [pres("Pluto", 12, None)]))

    def test_mais_recem_entrado_vence(self):
        """Quanto mais perto da cuspide, mais o tema esta comecando agora."""
        r = eleger_identificacao([], [pres("Saturn", 2, 0.5), pres("Neptune", 6, 9.0)])
        self.assertEqual(r.planeta, "Saturn")


class Criterio3(unittest.TestCase):
    def test_aspecto_largo_separando_conta(self):
        r = eleger_identificacao([asp("Pluto", "Sun", "square", 7.0, "Separating")])
        self.assertEqual(r.criterio, 3)

    def test_aplicando_com_orbe_largo_vira_criterio_4(self):
        """Separando e "passou"; aplicando e "esta chegando". Nao se misturam."""
        r = eleger_identificacao([asp("Pluto", "Sun", "square", 7.0, "Applying")])
        self.assertEqual(r.criterio, 4)

    def test_acima_de_dez_graus_nao_conta(self):
        self.assertIsNone(
            eleger_identificacao([asp("Pluto", "Sun", "square", 10.1, "Separating")]))

    def test_separando_tem_prioridade_sobre_aplicando(self):
        r = eleger_identificacao([asp("Pluto", "Sun", "square", 9.0, "Separating"),
                                  asp("Saturn", "Moon", "trine", 6.0, "Applying")])
        self.assertEqual(r.criterio, 3)

    def test_criterio_2_tem_prioridade_sobre_o_3(self):
        r = eleger_identificacao(
            [asp("Pluto", "Sun", "square", 7.0, "Separating")],
            [pres("Saturn", 3, 2.0)],
        )
        self.assertEqual(r.criterio, 2)


class SemNada(unittest.TestCase):
    def test_nada_qualifica_devolve_none(self):
        """None e resultado legitimo. Preencher com qualquer coisa seria inventar."""
        self.assertIsNone(eleger_identificacao([], []))


if __name__ == "__main__":
    unittest.main()
