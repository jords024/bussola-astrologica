# -*- coding: utf-8 -*-
"""Testes da Parte 1: o transito que gera identificacao.

Cada teste aqui corresponde a um jeito concreto de a cascata eleger errado.
"""
import unittest

from servicos.aspectos import AspectoNorm, PresencaNorm
from servicos.lentos import (ANGULOS, GRAUS_DE_ENTRADA, Perfil, alvos_de,
                             dias_para_exato, eleger_identificacao,
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


class Iminencia(unittest.TestCase):
    """O placar mede TEMPO, nao grau. Orbe sozinho mente sobre o momento."""

    def test_dias_para_exato_usa_a_velocidade(self):
        # 0,4 grau a 0,05 grau/dia sao oito dias
        self.assertAlmostEqual(
            dias_para_exato(asp("Saturn", "Sun", "square", 0.4, velocidade=0.05)),
            8.0, places=6)

    def test_sem_velocidade_nao_inventa_prazo(self):
        self.assertIsNone(
            dias_para_exato(asp("Saturn", "Sun", "square", 0.4, velocidade=0.0)))

    def test_exato_hoje_vence_orbe_menor_que_demora_meses(self):
        """O caso real que quebrava a leitura.

        Saturno a 0,03 grau andando 0,077 grau/dia fica exato HOJE. Urano a
        0,28 grau andando 0,012 fica exato so dali a 23 dias. Com a Lua valendo
        1,2 por ser regente, o placar antigo - que so olhava orbe - elegia
        Urano, e a carta falava de um movimento que ainda nao tinha chegado.
        """
        perfil = Perfil(regentes=frozenset({"Moon"}), peso_sol=1.0, peso_lua=1.2)
        r = eleger_identificacao([
            asp("Uranus", "Moon", "square", 0.28, velocidade=0.0123),
            asp("Saturn", "Sun", "square", 0.03, velocidade=0.0769),
        ], perfil=perfil)
        self.assertEqual(r.planeta, "Saturn")
        self.assertEqual(r.aspecto.natal, "Sun")

    def test_o_mais_iminente_vence_no_mesmo_orbe(self):
        a_rapido = asp("Saturn", "Sun", "square", 1.0, velocidade=0.08)
        a_lento = asp("Pluto", "Sun", "square", 1.0, velocidade=0.01)
        self.assertGreater(forca_identificacao(a_rapido),
                           forca_identificacao(a_lento))

    def test_transito_distante_nao_ganha_bonus(self):
        """Alem do horizonte, a iminencia e neutra e nao distorce o placar."""
        longe_1 = asp("Pluto", "Sun", "square", 4.0, velocidade=0.001)
        longe_2 = asp("Neptune", "Sun", "square", 4.0, velocidade=0.002)
        # ambos a mais de 60 dias: quem decide volta a ser o resto do placar
        self.assertAlmostEqual(forca_identificacao(longe_1),
                               forca_identificacao(longe_2), places=6)


class SegundoTransito(unittest.TestCase):
    """Dois lentos apertando juntos explicam a sensacao de ser puxada para
    dois lados. A carta usava um e jogava o outro fora."""

    def test_devolve_o_segundo_quando_existe(self):
        r = eleger_identificacao([
            asp("Saturn", "Sun", "square", 0.5, velocidade=0.07),
            asp("Uranus", "Moon", "square", 1.0, velocidade=0.01),
        ])
        self.assertEqual(r.planeta, "Saturn")
        self.assertIsNotNone(r.segundo)
        self.assertEqual(r.segundo.transito, "Uranus")

    def test_segundo_e_sempre_outro_planeta(self):
        """Dois aspectos do mesmo transitante sao a mesma noticia duas vezes."""
        r = eleger_identificacao([
            asp("Saturn", "Sun", "square", 0.5, velocidade=0.07),
            asp("Saturn", "Moon", "trine", 1.0, velocidade=0.07),
        ])
        self.assertEqual(r.planeta, "Saturn")
        self.assertIsNone(r.segundo)

    def test_o_outro_luminar_tem_preferencia(self):
        """Sol e Lua contam historias diferentes: o que ela quer ser e o que
        ela precisa sentir. Dois transitos no mesmo ponto dizem menos."""
        r = eleger_identificacao([
            asp("Saturn", "Sun", "square", 0.5, velocidade=0.07),
            asp("Pluto", "Sun", "trine", 0.6, velocidade=0.01),
            asp("Uranus", "Moon", "square", 3.0, velocidade=0.01),
        ])
        self.assertEqual(r.planeta, "Saturn")
        self.assertEqual(r.segundo.natal, "Moon")

    def test_transito_sozinho_nao_inventa_segundo(self):
        r = eleger_identificacao([asp("Saturn", "Sun", "square", 0.5)])
        self.assertIsNone(r.segundo)


class EixosDoMapa(unittest.TestCase):
    """Ascendente e Meio do Ceu como pontos que geram identificacao.

    Ficaram de fora por muito tempo sob a justificativa de que dependiam de
    hora exata e "sairiam do ar para boa parte dos leads". Medido nas leituras
    reais: 97% tem hora exata, porque o quiz pede a hora para montar o mapa. E
    o custo era alto - em 40% dos mapas o aspecto MAIS APERTADO era num eixo, e
    era descartado em favor de um mais largo.
    """

    def _perfil(self, angulos_ok=True):
        return Perfil(peso_sol=1.0, peso_lua=1.0, angulos_ok=angulos_ok)

    def test_sem_hora_confiavel_os_eixos_nao_entram(self):
        """Sem hora, o Ascendente pode errar um signo inteiro. Nao da para
        afirmar uma precisao que o calculo nao tem."""
        self.assertEqual(alvos_de(self._perfil(False)), ("Sun", "Moon"))

    def test_com_hora_confiavel_os_eixos_entram(self):
        alvos = alvos_de(self._perfil(True))
        for ponto in ANGULOS:
            self.assertIn(ponto, alvos)

    def test_eixo_apertado_vence_luminar_mais_largo(self):
        """O caso medido no mapa de um leitor: Plutao a 0,13 grau do Meio do
        Ceu perdia para Netuno a 0,51 da Lua, e a carta falava do mais largo."""
        r = eleger_identificacao([
            asp("Neptune", "Moon", "opposition", 0.51, velocidade=0.012),
            asp("Pluto", "Medium_Coeli", "square", 0.13, velocidade=0.009),
        ], perfil=self._perfil(True))
        self.assertEqual(r.aspecto.natal, "Medium_Coeli")

    def test_o_mesmo_mapa_sem_hora_ignora_o_eixo(self):
        r = eleger_identificacao([
            asp("Neptune", "Moon", "opposition", 0.51, velocidade=0.012),
            asp("Pluto", "Medium_Coeli", "square", 0.13, velocidade=0.009),
        ], perfil=self._perfil(False))
        self.assertEqual(r.aspecto.natal, "Moon")

    def test_cada_ponto_usa_o_proprio_peso(self):
        """Antes isto era binario - "peso_sol se for Sol, senao peso_lua" - e
        teria dado ao Meio do Ceu o peso da LUA assim que os eixos entrassem:
        um mapa com a Lua angular empurraria junto todo aspecto no MC, sem que
        o MC daquela pessoa tivesse nada de especial."""
        mc = asp("Pluto", "Medium_Coeli", "square", 0.5, velocidade=0.01)

        # a Lua vale 9, o MC vale 1: a forca do MC nao pode sentir a Lua
        so_lua = Perfil(peso_sol=1.0, peso_lua=9.0, angulos_ok=True)
        neutro = Perfil(peso_sol=1.0, peso_lua=1.0, angulos_ok=True)
        self.assertAlmostEqual(forca_identificacao(mc, so_lua),
                               forca_identificacao(mc, neutro), places=9)

        # e mexer no peso do proprio MC tem que mexer na forca dele
        so_mc = Perfil(peso_sol=1.0, peso_lua=1.0, peso_mc=2.0, angulos_ok=True)
        self.assertAlmostEqual(forca_identificacao(mc, so_mc),
                               forca_identificacao(mc, neutro) * 2.0, places=9)

    def test_eixo_pode_ser_o_segundo_transito(self):
        r = eleger_identificacao([
            asp("Saturn", "Sun", "square", 0.2, velocidade=0.07),
            asp("Pluto", "Ascendant", "square", 0.9, velocidade=0.01),
        ], perfil=self._perfil(True))
        self.assertEqual(r.planeta, "Saturn")
        self.assertIsNotNone(r.segundo)
        self.assertEqual(r.segundo.natal, "Ascendant")

    def test_eixo_salva_quem_nao_tem_nada_em_sol_ou_lua(self):
        """15% dos mapas reais nao tinham aspecto fechado em Sol nem Lua e
        caiam para um criterio mais fraco, mesmo com um eixo exato."""
        aspectos = [asp("Pluto", "Medium_Coeli", "square", 0.3, velocidade=0.01)]
        presencas = [pres("Neptune", 8, 2.0)]
        r = eleger_identificacao(aspectos, presencas, self._perfil(True))
        self.assertEqual(r.criterio, 1)   # o mais forte da cascata
        sem = eleger_identificacao(aspectos, presencas, self._perfil(False))
        self.assertEqual(sem.criterio, 2) # antes caia para "entrou numa casa"
