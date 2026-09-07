import unittest
from urllib.parse import unquote, urlparse, parse_qs
from fastapi.testclient import TestClient
import main


class TestWhatsappButton(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)
        self.response = self.client.get("/")
        self.assertEqual(self.response.status_code, 200)
        self.html = self.response.text

    def test_whatsapp_button_element_present(self):
        """Verifica se os elementos estruturais do botão de WhatsApp existem no HTML."""
        self.assertIn('id="whatsappSuporteWrapper"', self.html)
        self.assertIn('id="whatsappSuporteBtn"', self.html)
        self.assertIn('class="whatsapp-btn-float"', self.html)
        self.assertIn('class="whatsapp-btn-wrapper"', self.html)
        self.assertIn('aria-label="Fale conosco no WhatsApp"', self.html)

    def test_whatsapp_link_destination_and_phone(self):
        """Verifica se o link aponta para o número correto de suporte (+55 47 9233-1247)."""
        self.assertIn("https://wa.me/554792331247", self.html)

    def test_whatsapp_message_exact_and_encoded(self):
        """Verifica se a mensagem fixa solicitada está codificada de forma correta na URL."""
        expected_msg = "Gostaria de saber mais sobre o Bussola Astrologica"
        self.assertIn("text=Gostaria%20de%20saber%20mais%20sobre%20o%20Bussola%20Astrologica", self.html)

        import re
        match = re.search(r'href="(https://wa\.me/[^"]+)"', self.html)
        self.assertIsNotNone(match, "Link do WhatsApp não encontrado no HTML")
        url = match.group(1)
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        self.assertIn("text", params)
        decoded_msg = params["text"][0]
        self.assertEqual(decoded_msg, expected_msg)

    def test_security_attributes(self):
        """Verifica se o link abre em nova aba de forma segura."""
        self.assertIn('target="_blank"', self.html)
        self.assertIn('rel="noopener noreferrer"', self.html)

    def test_fixed_position_css_and_styling(self):
        """Garante que o botão possui estilo fixo no canto inferior direito e z-index prioritário."""
        self.assertIn("position: fixed;", self.html)
        self.assertIn("bottom: 24px;", self.html)
        self.assertIn("right: 24px;", self.html)
        self.assertIn("z-index: 99999;", self.html)
        self.assertIn("background-color: #25D366;", self.html)
        self.assertIn(".whatsapp-btn-pulse", self.html)

    def test_exibicao_exclusiva_na_tela_de_oferta(self):
        """Garante que o botão fica oculto por padrão (display: none) e só aparece na tela de oferta."""
        # CSS define display: none por padrão
        self.assertIn("display: none;", self.html)
        self.assertIn(".whatsapp-btn-wrapper.visivel", self.html)
        self.assertIn("display: flex;", self.html)

        # JS controla a exibição exclusivamente para a etapa de oferta (data-s="10")
        self.assertIn("function atualizarBtnWhatsApp", self.html)
        self.assertIn("getAttribute('data-s') === '10'", self.html)
        self.assertIn("waWrap.classList.add('visivel')", self.html)
        self.assertIn("waWrap.classList.remove('visivel')", self.html)

    def test_whatsapp_click_telemetry(self):
        """Verifica se o script registra evento de telemetria ao clicar no botão do WhatsApp."""
        self.assertIn("whatsapp_suporte_clique", self.html)
        self.assertIn("botao_flutuante_quiz", self.html)


if __name__ == "__main__":
    unittest.main()
