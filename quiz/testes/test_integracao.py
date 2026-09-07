import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient
import main
from api.leitura import Pedido, _pipeline
from servicos import llm, registro


def pedido():
    return dict(nome_completo='Pessoa de Teste',
        quiz=dict(area='carreira', espelho='Entrego muito e sou pouco reconhecida', quebra='muitas'),
        nascimento=dict(ano=1991, mes=3, dia=14, hora=4, minuto=20),
        cidade=dict(nome='Passo Fundo', lat=-28.2628, lng=-52.4067, tz='America/Sao_Paulo'))


class Integracao(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        for name in ('DIR_CACHE', 'DIR_LEITURAS'):
            path = Path(self.temp.name) / name
            path.mkdir()
            patcher = patch.object(registro, name, path)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_original_preservado(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Uma das suas <em>12 portas</em> está aberta agora.', response.text)
        self.assertIn('Na Astrologia chamamos de casas.', response.text)
        self.assertIn("fetch('/api/leitura'", response.text)
        self.assertNotIn('sk-proj-', response.text)

    def test_dados_invalidos(self):
        for change in ({'mes':2,'dia':31}, {'hora':None}, {'precisao':'periodo','periodo':'invalido'}):
            data = pedido()
            data['nascimento'].update(change)
            self.assertEqual(self.client.post('/api/leitura', json=data).status_code, 422)
        data = pedido()
        data['cidade']['tz'] = 'Inexistente/Fuso'
        self.assertEqual(self.client.post('/api/leitura', json=data).status_code, 422)

    def test_sem_hora_nao_inventa_casas(self):
        data = pedido()
        data['nascimento'].update(precisao='desconhecida', hora=None)
        with patch.object(llm, 'OPENAI_API_KEY', ''):
            response = self.client.post('/api/leitura', json=data)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIsNone(result['bussola']['slot'])
        self.assertIsNone(result['bussola']['casa_fechada'])
        self.assertEqual(result['svg'], '')
        self.assertTrue(result['carta']['ressalva'])

    def test_reserva_e_registro(self):
        with patch.object(llm, 'OPENAI_API_KEY', ''):
            response = self.client.post('/api/leitura', json=pedido())
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['meta']['validacao'], 'reserva')
        self.assertGreaterEqual(len(data['carta']['paragrafos']), 4)
        self.assertIn('<svg', data['svg'])
        self.assertTrue((registro.DIR_LEITURAS / (data['leitura_id']+'.json')).exists())

    def test_falha_calculo_recuperavel(self):
        with patch('api.leitura._pipeline', side_effect=RuntimeError('teste')):
            self.assertEqual(self.client.post('/api/leitura', json=pedido()).status_code, 503)

    def test_cache_varia_com_fatos_e_respostas(self):
        _, _, v, _, quiz, fatos, _ = _pipeline(Pedido(**pedido()), datetime.now(timezone.utc))
        today = datetime.now().date()
        key = registro.chave_cache(v, fatos, quiz, today)
        self.assertNotEqual(key, registro.chave_cache(v, dict(fatos, bloco_fatos=fatos['bloco_fatos']+' diferente'), quiz, today))
        self.assertNotEqual(key, registro.chave_cache(v, fatos, dict(quiz, espelho='Outro recorte'), today))

    def test_mandala_e_fatos_correspondem_ao_nascimento(self):
        instant = datetime(2026,9,5,20,tzinfo=timezone.utc)
        first = pedido()
        second = pedido()
        second['nascimento'].update(ano=1985, mes=7, dia=22, hora=18)
        result_a = _pipeline(Pedido(**first), instant)
        result_b = _pipeline(Pedido(**second), instant)
        self.assertNotEqual(result_a[-1], result_b[-1])
        self.assertNotEqual(result_a[-2]['bloco_fatos'], result_b[-2]['bloco_fatos'])
        self.assertIn('<svg', result_a[-1])

    def test_respostas_entram_no_prompt_sem_mudar_mapa(self):
        instant = datetime(2026,9,5,20,tzinfo=timezone.utc)
        first = pedido()
        second = pedido()
        second['quiz'].update(area='amor', espelho='Quero entender o que atraio e por quê', quebra='nao')
        result_a = _pipeline(Pedido(**first), instant)
        result_b = _pipeline(Pedido(**second), instant)
        self.assertEqual(result_a[0].natal.sun.abs_pos, result_b[0].natal.sun.abs_pos)
        self.assertEqual(result_a[1].casas, result_b[1].casas)
        prompt_a = llm.montar_user(result_a[-2])
        prompt_b = llm.montar_user(result_b[-2])
        self.assertIn(first['quiz']['espelho'], prompt_a)
        self.assertIn(second['quiz']['espelho'], prompt_b)
        self.assertIn('Muitas vezes. É quase um padrão', prompt_a)
        self.assertIn('Não sei dizer', prompt_b)
        self.assertNotEqual(prompt_a, prompt_b)
        self.assertIn(result_a[-2]['bloco_fatos'], prompt_a)

    def test_fuso_transito(self):
        data = pedido()
        p = Pedido(**data)
        instante = datetime(2026,9,5,20,tzinfo=timezone.utc)
        mapa, *_ = _pipeline(p, instante)
        self.assertEqual(mapa.transito.hour, 17)
        self.assertTrue(all(a.natal not in ('Transito',) for a in mapa.aspectos))

    def test_contato_nao_aceita_caminho(self):
        self.assertFalse(registro.anexar_contato('../../config', 'teste'))


    def test_variaveis_css_e_dropdown_cidade(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.text
        import re
        root_vars = set(re.findall(r'--([a-zA-Z0-9_-]+):', html[:2500]))
        used_vars = set(re.findall(r'var\(--([a-zA-Z0-9_-]+)\)', html))
        undefined = used_vars - root_vars
        self.assertEqual(undefined, set(), f"Variáveis CSS não definidas: {undefined}")
        self.assertIn('z-index:100;', html)
        self.assertNotIn('Recomeçar o percurso', html)
        self.assertNotIn('id="again"', html)

    def test_checkout_redirecionamento_hotmart(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.text
        self.assertIn('https://pay.hotmart.com/Q107238351O?checkoutMode=10&bid=1788742865072', html)
        self.assertNotIn('sem checkout conectado', html)
        self.assertIn("A.ev('oferta_clique'", html)

    def test_limite_digitos_inputs_nascimento(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.text
        self.assertIn('id="hh" placeholder="14" maxlength="2"', html)
        self.assertIn('id="mi" placeholder="30" maxlength="2"', html)
        self.assertIn('id="yy" placeholder="ano" maxlength="4"', html)
        self.assertIn("slice(0, 2)", html)
        self.assertIn("slice(0, 4)", html)

    def test_docker_compose_quiz_producao_valido(self):
        import yaml
        compose_path = Path(__file__).resolve().parent.parent.parent / 'docker' / 'docker-compose-quiz-producao.yml'
        self.assertTrue(compose_path.exists(), "Arquivo docker-compose-quiz-producao.yml não encontrado")
        with open(compose_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
        self.assertIn('services', data)
        self.assertIn('quiz_crassus', data['services'])
        svc = data['services']['quiz_crassus']
        self.assertIn('image', svc)
        self.assertIn('network_swarm_public', svc['networks'])
        self.assertIn('quiz_dados:/app/dados', svc['volumes'])
        labels = svc['deploy']['labels']
        self.assertTrue(any('server.port=8765' in lbl for lbl in labels))
        self.assertTrue(any('traefik.enable=true' in lbl for lbl in labels))

    def test_docker_compose_producao_unificado_valido(self):
        import yaml
        compose_path = Path(__file__).resolve().parent.parent.parent / 'docker' / 'docker-compose-producao.yml'
        self.assertTrue(compose_path.exists(), "Arquivo docker-compose-producao.yml não encontrado")
        with open(compose_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
        self.assertIn('services', data)
        self.assertIn('landing_crassus', data['services'])
        self.assertIn('quiz_crassus', data['services'])
        landing = data['services']['landing_crassus']
        self.assertIn('image', landing)
        self.assertIn('network_swarm_public', landing['networks'])
        quiz = data['services']['quiz_crassus']
        self.assertIn('quiz_dados:/app/dados', quiz['volumes'])
        quiz_labels = quiz['deploy']['labels']
        self.assertTrue(any('server.port=8765' in lbl for lbl in quiz_labels))

    def test_meta_pixel_rastreamento_completo(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.text
        # Validação do ID do Pixel e Script base
        self.assertIn('776532458708522', html)
        self.assertIn("fbq('init', '776532458708522');", html)
        self.assertIn("fbq('track', 'PageView');", html)
        self.assertIn('https://connect.facebook.net/en_US/fbevents.js', html)
        self.assertIn('https://www.facebook.com/tr?id=776532458708522&ev=PageView&noscript=1', html)

        # Validação das funções e eventos de rastreamento do funil
        self.assertIn('Quiz_Etapa_', html)
        self.assertIn('Quiz_Etapa', html)
        self.assertIn('Quiz_Escolha_', html)
        self.assertIn('Quiz_Leitura_Revelada', html)

        # Validação dos eventos padrão do Meta Pixel
        self.assertIn("window.fbq('track', 'Lead'", html)
        self.assertIn("window.fbq('track', 'ViewContent'", html)
        self.assertIn("window.fbq('track', 'InitiateCheckout'", html)

    def test_coleta_whatsapp_frontend(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.text
        # Campo de WhatsApp, DDI e bandeiras presentes na tela 5
        self.assertIn('id="tel"', html)
        self.assertIn('id="ddi"', html)
        self.assertIn('🇧🇷 +55', html)
        self.assertIn('🇵🇹 +351', html)
        self.assertIn('🇺🇸 +1', html)
        self.assertIn('duo-tel', html)
        # Funções de formatação e validação no script
        self.assertIn('formatarTelBR', html)
        self.assertIn('aplicarMascaraTel', html)
        self.assertIn('whatsapp:S.whatsapp', html)
        self.assertIn('phonenumber', html)

    def test_validacao_tela5_visual_e_acessibilidade(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.text
        # Placeholder claro e desambiguado para não parecer preenchido
        self.assertIn('placeholder="DDD + seu número"', html)
        # Elementos de feedback visual e acessibilidade
        self.assertIn('id="telAviso"', html)
        self.assertIn('id="calcAviso"', html)
        self.assertIn('id="calcAvisoLista"', html)
        # Classes CSS de erro e animações
        self.assertIn('.input-erro', html)
        self.assertIn('shake-erro', html)
        self.assertIn('.calc-aviso', html)
        # Validação com foco no primeiro campo faltante e limpeza em tempo real
        self.assertIn('primeiroErroEl.focus()', html)
        self.assertIn('primeiroErroEl.scrollIntoView', html)
        self.assertIn("['nm', 'tel', 'dd', 'mm', 'yy', 'hh', 'mi', 'cid']", html)

    def test_whatsapp_persistido_no_lead(self):
        import json
        dados = pedido()
        dados['whatsapp'] = "+55 (11) 98765-4321"
        with patch.object(llm, 'OPENAI_API_KEY', ''):
            response = self.client.post('/api/leitura', json=dados)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        leitura_id = result['leitura_id']
        arq_lead = registro.DIR_LEITURAS / f"{leitura_id}.json"
        self.assertTrue(arq_lead.exists())
        lead_conteudo = json.loads(arq_lead.read_text(encoding='utf-8'))
        self.assertEqual(lead_conteudo.get('whatsapp'), "+55 (11) 98765-4321")
        self.assertIn('gravado_em_bsb', lead_conteudo)
        self.assertIn('chegou_em_bsb', lead_conteudo)

    @patch('servicos.webhook.disparar_webhook_leitura')
    def test_webhook_disparado_na_leitura(self, mock_webhook):
        dados = pedido()
        dados['nome_completo'] = 'Aryaraj Alves Fernandes'
        dados['whatsapp'] = '+55 (85) 99999-8888'
        with patch.object(llm, 'OPENAI_API_KEY', ''):
            response = self.client.post('/api/leitura', json=dados)
        self.assertEqual(response.status_code, 200)
        mock_webhook.assert_called_once()
        args, kwargs = mock_webhook.call_args
        self.assertEqual(args[0], 'Aryaraj Alves Fernandes')
        self.assertEqual(args[1], '+55 (85) 99999-8888')
        self.assertIn('paragrafos', args[2])

if __name__ == '__main__':
    unittest.main()

