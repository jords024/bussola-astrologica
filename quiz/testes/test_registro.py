# -*- coding: utf-8 -*-
"""O registro da carta: portugues falado, nao verso.

O modelo ECOA o registro do que recebe. Enquanto o vocabulario de traducao
dizia que Netuno era "o que dissolve contorno", a carta devolvia "o que voce
sente esta pedindo contorno, mas nao aceita pressa" - uma frase que nenhum
brasileiro diz em voz alta, e muito menos o Crassus, que e papo reto.

O vocabulario foi reescrito; estes testes guardam a reincidencia nas tres
frases que aparecem grandes na tela.
"""
import unittest

from servicos.nomes import ASPECTO_HUMANO, PLANETA_VIDA
from servicos.verificacao import auditar_registro


class Guarda(unittest.TestCase):
    def test_titulo_abstrato_e_reprovado(self):
        self.assertTrue(auditar_registro({"titulo": "dar nome ao que pesa"}))

    def test_titulo_concreto_passa(self):
        self.assertEqual(
            auditar_registro({"titulo": "cobrar pelo trabalho que você entrega"}), [])

    def test_abertura_em_tom_de_verso_e_reprovada(self):
        c = {"identificacao": {"abertura":
             "O que você sente está pedindo contorno, mas não aceita pressa."}}
        self.assertTrue(auditar_registro(c))

    def test_abertura_falada_passa(self):
        c = {"identificacao": {"abertura":
             "Você está cansado de uma coisa que nem consegue explicar direito."}}
        self.assertEqual(auditar_registro(c), [])

    def test_a_porta_tambem_e_vigiada(self):
        c = {"porta": {"abertura": "Aquilo que circula pede revisão."}}
        self.assertTrue(auditar_registro(c))

    def test_carta_inteira_em_ordem_passa(self):
        c = {"titulo": "acertar o dinheiro dividido",
             "identificacao": {"abertura": "Você cansou de cuidar de todo mundo."},
             "porta": {"abertura": "Seu trabalho está ganhando espaço."}}
        self.assertEqual(auditar_registro(c), [])

    def test_carta_vazia_nao_quebra(self):
        self.assertEqual(auditar_registro({}), [])
        self.assertEqual(auditar_registro(None), [])


class VocabularioDeDestino(unittest.TestCase):
    """O que alimenta o modelo tem que estar no registro que se quer de volta."""

    POETICO = ("dissolve", "contorno", "abrigo", "em fluxo", "em atrito",
               "aquilo que", "brilho")

    def test_planetas_sem_palavra_de_verso(self):
        for planeta, texto in PLANETA_VIDA.items():
            for p in self.POETICO:
                self.assertNotIn(p, texto.lower(),
                                 f"{planeta} voltou ao registro literario")

    def test_aspectos_sem_palavra_de_verso(self):
        for aspecto, texto in ASPECTO_HUMANO.items():
            for p in self.POETICO:
                self.assertNotIn(p, texto.lower(),
                                 f"{aspecto} voltou ao registro literario")


class DestaqueUnico(unittest.TestCase):
    """A frase em destaque nao pode servir para mais ninguem.

    Item roubado do checklist do Mapa da Alma: "a frase-sintese e unica, nao
    poderia ser de nenhum outro mapa". Sem trava o modelo volta ao proverbio,
    que e o caminho mais curto para uma frase bonita.
    """

    def setUp(self):
        from servicos import verificacao
        verificacao._DESTAQUES_RECENTES.clear()

    def d(self, frase, lembrar=True):
        from servicos.verificacao import auditar_destaque
        return auditar_destaque({"destaque": frase}, lembrar=lembrar)

    def test_primeira_carta_sempre_passa(self):
        self.assertEqual(
            self.d("A conta dos outros não pode ser paga com o seu corpo."), [])

    def test_mesma_frase_com_outras_palavras_reprova(self):
        self.d("O combinado precisa sair da cabeça e virar conversa marcada.")
        r = self.d("O combinado tem que sair da cabeça e virar conversa marcada.")
        self.assertTrue(r)

    def test_mesma_formula_com_assunto_trocado_reprova(self):
        """A repeticao que mais apareceu nos testes: muda o assunto, mantem a
        formula. A sobreposicao de palavras e baixa; o que denuncia e o
        comeco identico."""
        self.d("Reciprocidade começa quando aquilo que pesa ganha nome.")
        r = self.d("Reciprocidade começa quando o que você entrega deixa de ser suposto.")
        self.assertTrue(r)

    def test_frases_realmente_diferentes_passam(self):
        self.d("A conta dos outros não pode ser paga com o seu corpo.")
        self.d("Seu trabalho precisa de prazo e conversa, não de adivinhação.")
        r = self.d("A mudança ganha corpo quando o que ficou sem nome entra na mesa.")
        self.assertEqual(r, [])

    def test_lembrar_falso_nao_suja_a_memoria(self):
        self.d("O combinado precisa sair da cabeça e virar conversa marcada.",
               lembrar=False)
        self.assertEqual(
            self.d("O combinado precisa sair da cabeça e virar conversa marcada."),
            [])

    def test_carta_vazia_ou_sem_destaque_nao_quebra(self):
        from servicos.verificacao import auditar_destaque
        self.assertEqual(auditar_destaque({}), [])
        self.assertEqual(auditar_destaque(None), [])
        self.assertEqual(auditar_destaque({"destaque": ""}), [])
        self.assertEqual(auditar_destaque({"destaque": "Vai dar certo."}), [])
