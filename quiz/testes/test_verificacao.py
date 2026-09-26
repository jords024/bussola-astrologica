# -*- coding: utf-8 -*-
"""Testes dos auditores que rodam depois da geracao."""
import unittest

from unittest import mock

from servicos.verificacao import (_carregar_exemplos, auditar_exemplos,
                                  auditar_expressao, auditar_recitacao,
                                  auditar_registro, _carregar_expressoes)


def carta(*paragrafos, **kw):
    return {"destaque": kw.get("destaque", ""),
            "identificacao": {"abertura": kw.get("abertura", ""),
                              "paragrafos": list(paragrafos)},
            "porta": {"abertura": "", "paragrafos": [], "aproveitar": []}}


class PlagioDosExemplos(unittest.TestCase):
    """O prompt ensina pelo exemplo, e o modelo entendeu como molde.

    Numa carta medida aqui, o exemplo "Voce rele a mensagem procurando o tom, e
    responde para a versao que imaginou" saiu quase inteiro no paragrafo de uma
    pessoa cujo mapa nao falava de mensagem nenhuma. Parecia precisao e era
    decoreba: ela recebeu a cena de outra pessoa com o nome dela em cima.
    """

    def test_o_prompt_tem_exemplos_para_comparar(self):
        """Se a extracao quebrar, o auditor passa a aprovar tudo em silencio."""
        self.assertGreater(len(_carregar_exemplos()), 5)

    def test_pega_a_cena_copiada_mesmo_reescrita(self):
        """Pega um exemplo do prompt DE VERDADE e devolve levemente reescrito.

        Antes este teste trazia a frase copiada na mao, e quando o exemplo saiu
        do prompt o teste passou a reprovar um auditor que estava certo. Agora
        ele le o prompt, entao continua valendo depois de qualquer reescrita.
        """
        frase = _carregar_exemplos()[0][0]
        palavras = frase.split()
        # reescreve: corta o comeco e troca a ordem do fim, como o modelo faz
        disfarce = " ".join(palavras[1:-1] + ["de", "novo"])
        self.assertTrue(auditar_exemplos(carta(disfarce)))

    def test_deixa_passar_a_cena_que_e_dela(self):
        c = carta("Voce adiou a matricula do curso tres vezes e ja perdeu o "
                  "desconto duas, e agora finge que o prazo nao existe.")
        self.assertEqual(auditar_exemplos(c), [])

    def test_frase_curta_nao_e_acusada(self):
        """Pouca palavra nao da para julgar sem acusar falso."""
        self.assertEqual(auditar_exemplos(carta("O prazo chegou.")), [])

    def test_olha_a_carta_inteira_e_nao_so_os_paragrafos(self):
        """O plagio conta tambem quando cai no destaque, que e a frase que a
        pessoa mais relembra e mais compartilha."""
        frase = _carregar_exemplos()[0][0]
        c = carta("Uma frase qualquer que nao copia nada de lugar nenhum hoje.",
                  destaque=frase)
        self.assertTrue(auditar_exemplos(c))

    def test_entrada_invalida_nao_derruba_a_leitura(self):
        self.assertEqual(auditar_exemplos(None), [])
        self.assertEqual(auditar_exemplos({}), [])


def bloco(abertura, *paragrafos):
    return {"titulo": "x", "destaque": "",
            "identificacao": {"abertura": abertura, "paragrafos": list(paragrafos)},
            "porta": {"abertura": "", "paragrafos": [], "aproveitar": []}}


class RecitacaoDaDefinicao(unittest.TestCase):
    """A carta devolvendo em prosa a definicao que recebeu nos FATOS.

    Com Netuno atravessando a casa 3, uma carta real saiu assim: "Uma conversa
    simples esta virando duvida demais. Nas mensagens... Um combinado curto
    vira tres interpretacoes." Tres substantivos de CASA_VIDA[3], em fila, sem
    uma cena. Nao e invencao nem plagio de exemplo: e aritmetica de dicionario,
    e serve para qualquer pessoa com aquela casa ativada.
    """

    def test_pega_a_definicao_recitada(self):
        c = bloco("Uma conversa simples esta virando duvida demais.",
                  "Nas mensagens, voce rele cada frase procurando uma certeza "
                  "que nao aparece. Um combinado curto vira interpretacoes "
                  "demais e no fim voce confirma tudo de novo.")
        self.assertTrue(auditar_recitacao(c))

    def test_ancora_concreta_absolve_o_bloco(self):
        """Varias definicoes sao listas curtas - PLANETA_VIDA['Mercury'] e "a
        cabeca: conversa, mensagem, combinado, decisao". Uma carta legitima
        sobre comunicacao esbarra em quatro daquelas palavras sem estar
        recitando. O que separa recitacao de escrita e a contagem SEM cena."""
        c = bloco("Voce ja releu aquela conversa e continuou sem saber.",
                  "As 23h chega a mensagem e voce monta tres explicacoes "
                  "antes de responder. O combinado continua parado ate "
                  "segunda, e o silencio comeca a parecer resposta.")
        self.assertEqual(auditar_recitacao(c), [])

    def test_entrada_invalida_nao_derruba_a_leitura(self):
        self.assertEqual(auditar_recitacao(None), [])
        self.assertEqual(auditar_recitacao({}), [])


class FormulaPoetica(unittest.TestCase):
    """"X esta virando Y": substantivo abstrato, verbo de transformacao,
    substantivo abstrato. Foi a construcao que mais se repetiu nas aberturas
    reprovadas, e nenhuma delas descrevia coisa nenhuma."""

    def test_pega_a_formula_na_abertura(self):
        c = bloco("Uma conversa simples esta virando duvida demais.")
        self.assertTrue(auditar_registro(c))

    def test_pega_a_variante_anda_virando(self):
        c = bloco("O prazer anda virando cobranca.")
        self.assertTrue(auditar_registro(c))

    def test_cena_concreta_passa(self):
        c = bloco("Voce confere a mesma frase tres vezes, e ninguem percebe.")
        self.assertEqual(auditar_registro(c), [])


class QuandoAReservaEntra(unittest.IsolatedAsyncioTestCase):
    """A reserva e o ULTIMO recurso, nao o segundo.

    Ela e montada por codigo e por isso recita as definicoes inteiras - e foi
    ela que um leitor recebeu, com "as conversas do dia a dia, as mensagens,
    os combinados curtos" copiado do dicionario, porque duas geracoes tinham
    sido reprovadas no ESTILO. Trocar uma carta escrita com um defeito de tom
    por um formulario sem nenhum acerto e piorar a leitura para melhorar a
    metrica.
    """

    def _fatos(self):
        return {"permitido": {"planetas": set(), "signos": set(), "casas": set()},
                "bloco_identificacao": "", "bloco_porta": "",
                "bloco_quiz": "", "notas": []}

    async def _rodar(self, carta_falsa):
        from servicos import llm
        with mock.patch.object(llm, "OPENAI_API_KEY", "sk-teste"), \
             mock.patch.object(llm, "_sistema", return_value="x"), \
             mock.patch.object(llm, "_chamar",
                               mock.AsyncMock(return_value=carta_falsa)), \
             mock.patch.object(llm.reserva, "montar",
                               return_value={"RESERVA": True}):
            return await llm.escrever(self._fatos(), None, {}, {})

    async def test_problema_so_de_estilo_mantem_a_carta_escrita(self):
        ruim = bloco("O prazer anda virando cobranca.",
                     "Um paragrafo qualquer, sem astrologia nenhuma dentro.")
        ruim["destaque"] = "Uma frase de destaque que serve para esta pessoa."
        r = await self._rodar(ruim)
        self.assertNotIn("RESERVA", r["carta"])
        self.assertEqual(r["meta"]["validacao"], "estilo")

    async def test_astrologia_inventada_cai_para_a_reserva(self):
        """Aqui a reserva esta certa: citar um planeta que o calculo nao
        encontrou e assinar uma astrologia que nao existe."""
        invencao = bloco("Voce sentiu a semana virar de um jeito estranho.",
                         "Plutao em Escorpiao na casa 7 explica o seu cansaco "
                         "de agora, e Venus confirma isso.")
        invencao["destaque"] = "Uma frase de destaque que serve para esta pessoa."
        r = await self._rodar(invencao)
        self.assertIn("RESERVA", r["carta"])
        self.assertEqual(r["meta"]["validacao"], "reserva")


class ExpressaoPopular(unittest.TestCase):
    """A carta sem uma expressao que o brasileiro use de verdade.

    "Voce esta empurrando uma coisa que nao anda na carreira" e "Voce esta
    empurrando COM A BARRIGA uma coisa que nao anda" dizem o mesmo. A segunda e
    a que a pessoa fala, e por isso e a que ela reconhece. Pedir isso em prosa
    nao bastou: o modelo leu a regra, reaproveitou a frase do proprio quiz e
    nao usou expressao nenhuma.
    """

    def test_o_banco_do_prompt_e_lido(self):
        """Se a extracao quebrar, o auditor aprova tudo em silencio."""
        self.assertGreater(len(_carregar_expressoes()), 20)

    def test_a_marca_e_o_substantivo_e_nao_o_verbo(self):
        """A primeira versao pegava a palavra mais longa e guardava
        "empurrar" em vez de "barriga" - a metade sem graca, e a que nao
        sobrevive a conjugacao."""
        marcas = _carregar_expressoes()
        self.assertIn("barriga", marcas)
        self.assertIn("balde", marcas)
        self.assertIn("tranco", marcas)
        self.assertNotIn("empurrar", marcas)

    def test_palavra_comum_nao_vale_como_expressao(self):
        """"dinheiro" sai de "o dinheiro nao estica" e faria toda carta sobre
        dinheiro passar de graca. O auditor procura SABOR, nao assunto."""
        self.assertNotIn("dinheiro", _carregar_expressoes())

    def test_carta_morna_reprova(self):
        c = bloco("", "Voce disse que esta empurrando uma coisa que nao anda no "
                      "dinheiro. Isso nao e falta de esforco, e uma decisao da "
                      "carreira que continua sendo mantida.")
        self.assertTrue(auditar_expressao(c))

    def test_carta_com_expressao_passa(self):
        c = bloco("Voce empurra isso com a barriga, e nao comecou ontem.",
                  "Uma decisao da carreira continua de pe sem ninguem revisar.")
        self.assertEqual(auditar_expressao(c), [])

    def test_a_conjugacao_nao_derruba(self):
        """O substantivo sobrevive: empurrar, empurrando, empurrou."""
        for v in ("empurrando com a barriga", "empurrou com a barriga",
                  "empurra com a barriga"):
            self.assertEqual(auditar_expressao(bloco("", "Voce vem " + v + ".")), [])

    def test_entrada_invalida_nao_derruba_a_leitura(self):
        self.assertEqual(auditar_expressao(None), [])
        self.assertEqual(auditar_expressao({}), [])


class ComoFalarComAPessoa(unittest.TestCase):
    """Genero errado derruba a carta inteira.

    Um leitor homem recebeu a leitura toda no feminino, e a primeira coisa que
    ele viu foi que o texto nao fazia ideia de quem ele era. A causa era dupla:
    o sistema nunca perguntou o genero, e o proprio prompt chamava a leitora de
    "ela" 76 vezes contra 17 "ele", entao o modelo espelhava.
    """

    def test_terminacoes_que_decidem(self):
        from servicos.tratamento import genero_do_nome
        for n in ("Jordao", "Bruno", "Rafael", "Heitor", "Vinicius", "Davi"):
            self.assertEqual(genero_do_nome(n), "m", n)
        for n in ("Juliana", "Maria", "Gabriela", "Beatriz", "Yasmin"):
            self.assertEqual(genero_do_nome(n), "f", n)

    def test_excecoes_vencem_a_terminacao(self):
        """Raquel e Ester terminam em consoante e nao sao homens; Luca termina
        em -a e nao e mulher."""
        from servicos.tratamento import genero_do_nome
        self.assertEqual(genero_do_nome("Raquel"), "f")
        self.assertEqual(genero_do_nome("Ester"), "f")
        self.assertEqual(genero_do_nome("Isabel"), "f")
        self.assertEqual(genero_do_nome("Luca"), "m")

    def test_o_acento_nao_atrapalha(self):
        from servicos.tratamento import genero_do_nome
        self.assertEqual(genero_do_nome("Jordão Rodrigues"), "m")
        self.assertEqual(genero_do_nome("Láis"), "f")

    def test_na_duvida_devolve_none_em_vez_de_chutar(self):
        """Chutar concordancia e pior do que escrever sem marcar."""
        from servicos.tratamento import genero_do_nome
        self.assertIsNone(genero_do_nome("Jaci"))
        self.assertIsNone(genero_do_nome(""))
        self.assertIsNone(genero_do_nome("X"))

    def test_o_bloco_manda_a_ordem_certa(self):
        from servicos.tratamento import bloco_tratamento
        m = bloco_tratamento("Jordao")
        self.assertIn("Jordao", m)
        self.assertIn("HOMEM", m)
        f = bloco_tratamento("Juliana")
        self.assertIn("MULHER", f)
        n = bloco_tratamento("Jaci")
        self.assertIn("SEM MARCAR GENERO", n)

    def test_o_bloco_vai_junto_com_os_fatos(self):
        """Sem isto o modelo nao recebe a ordem e volta a chutar."""
        import inspect
        from servicos import fatos
        self.assertIn("bloco_tratamento", inspect.getsource(fatos))
