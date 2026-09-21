# -*- coding: utf-8 -*-
"""Testes da Parte 2: qual porta esta aberta.

O ponto sensivel e o desempate. Sem regra fixa, a casa eleita passaria a
depender da ordem em que os planetas chegam na lista - e a mesma pessoa
receberia portas diferentes em duas chamadas seguidas.
"""
import unittest

from servicos.aspectos import PresencaNorm
from servicos.porta import eleger_porta


def pres(planeta, casa):
    return PresencaNorm(planeta=planeta, casa=casa)


class Contagem(unittest.TestCase):
    def test_casa_mais_populosa_vence(self):
        r = eleger_porta([pres("Sun", 1), pres("Mercury", 1), pres("Venus", 1),
                          pres("Mars", 3)])
        self.assertEqual(r.casa, 1)
        self.assertEqual(r.planetas, ("Sun", "Mercury", "Venus"))
        self.assertFalse(r.empate)

    def test_planetas_saem_em_ordem_fixa(self):
        """Ordem estavel: o texto cita sempre na mesma sequencia."""
        r = eleger_porta([pres("Mars", 5), pres("Venus", 5), pres("Sun", 5)])
        self.assertEqual(r.planetas, ("Sun", "Venus", "Mars"))

    def test_ignora_planeta_lento(self):
        r = eleger_porta([pres("Pluto", 9), pres("Saturn", 9), pres("Sun", 2)])
        self.assertEqual(r.casa, 2)

    def test_ignora_casa_invalida(self):
        r = eleger_porta([pres("Mercury", 0), pres("Venus", 13), pres("Sun", 7)])
        self.assertEqual(r.casa, 7)


class Desempate(unittest.TestCase):
    def test_dois_a_dois_resolve_pelo_sol(self):
        r = eleger_porta([pres("Sun", 1), pres("Mercury", 1),
                          pres("Venus", 3), pres("Mars", 3)])
        self.assertEqual(r.casa, 1)
        self.assertTrue(r.empate)
        self.assertTrue(r.por_desempate)

    def test_dois_a_dois_do_outro_lado_tambem(self):
        """Nao pode ser a menor casa por acaso: aqui o Sol esta na casa maior."""
        r = eleger_porta([pres("Mercury", 2), pres("Venus", 2),
                          pres("Sun", 11), pres("Mars", 11)])
        self.assertEqual(r.casa, 11)
        self.assertTrue(r.por_desempate)

    def test_um_a_um_a_um_a_um_resolve_pelo_sol(self):
        r = eleger_porta([pres("Sun", 6), pres("Mercury", 7),
                          pres("Venus", 8), pres("Mars", 9)])
        self.assertEqual(r.casa, 6)
        self.assertTrue(r.empate)

    def test_empate_sem_o_sol_e_estavel(self):
        """Fallback reproduzivel: duas chamadas nao podem divergir."""
        a = eleger_porta([pres("Mercury", 4), pres("Venus", 10)])
        b = eleger_porta([pres("Venus", 10), pres("Mercury", 4)])
        self.assertEqual(a.casa, b.casa)
        self.assertFalse(a.por_desempate)


class SemCasa(unittest.TestCase):
    def test_sem_rapidos_devolve_none(self):
        self.assertIsNone(eleger_porta([]))

    def test_so_lentos_devolve_none(self):
        self.assertIsNone(eleger_porta([pres("Neptune", 5)]))


if __name__ == "__main__":
    unittest.main()


class PortaEOportunidade(unittest.TestCase):
    """A porta e a MELHOR noticia da carta, e o texto tem que soar assim.

    O calculo elege a casa onde os rapidos se acumulam, ou seja, onde existe
    energia sobrando. Descrever isso com verbo de concessao inverte o sentido
    do que foi calculado e entrega como consolo o melhor achado da leitura.
    """

    def test_abertura_com_verbo_de_concessao_e_reprovada(self):
        from servicos.verificacao import auditar_porta
        ruim = "Para mexer na carreira agora, o que cede e o que voce divide."
        self.assertTrue(auditar_porta({"porta": {"abertura": ruim}}))

    def test_abertura_que_anuncia_oportunidade_passa(self):
        from servicos.verificacao import auditar_porta
        boa = "As conversas e os combinados estao destravando agora."
        self.assertEqual(auditar_porta({"porta": {"abertura": boa}}), [])

    def test_a_guarda_nao_alcanca_o_cuidado(self):
        # "ceder demais para manter a paz" e um cuidado legitimo da casa 7
        from servicos.verificacao import auditar_porta
        carta = {"porta": {"abertura": "Os vinculos estao mais faceis agora.",
                           "cuidado": "Cuidado em ceder demais para manter a paz."}}
        self.assertEqual(auditar_porta(carta), [])

    def test_fatos_da_porta_trazem_o_que_cada_rapido_oferece(self):
        from servicos.fatos import bloco_porta
        from servicos.porta import Porta
        b = bloco_porta(Porta(casa=10, planetas=("Mars",), empate=False,
                              por_desempate=False))
        self.assertIn("por que ela esta aberta agora", b)
        self.assertIn("forca", b)
        # Marte sozinho pede acao, nao espera
        self.assertIn("MODO EMPURRAR", b)

    def test_venus_pede_o_modo_oposto_ao_de_marte(self):
        from servicos.fatos import bloco_porta
        from servicos.porta import Porta
        b = bloco_porta(Porta(casa=7, planetas=("Venus",), empate=False,
                              por_desempate=False))
        self.assertIn("MODO ATRAIR", b)

    def test_porta_em_outra_area_proibe_concessao_nos_fatos(self):
        from servicos.fatos import bloco_porta
        from servicos.porta import Porta
        b = bloco_porta(Porta(casa=3, planetas=("Sun",), empate=False,
                              por_desempate=False),
                        casa_do_tema=10, tema="a carreira")
        self.assertIn("BOA NOTICIA", b)
        self.assertIn("PROIBIDO verbo de concessao", b)
