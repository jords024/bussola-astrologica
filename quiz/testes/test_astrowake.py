"""
Testes unitários para a Landing Page Astrowake (LP Astrowake)
Valida estrutura do pop-up modal, fechamento exclusivo via botão (não fecha ao clicar fora),
e campo de WhatsApp com seletor de DDI (+55 Brasil padrão).
"""
import re
from pathlib import Path

DIR_ASTROWAKE = Path(__file__).resolve().parent.parent.parent / "lp-astrowake"
INDEX_HTML = DIR_ASTROWAKE / "index.html"
INSCRICAO_JS = DIR_ASTROWAKE / "inscricao.js"
CONFIG_JS = DIR_ASTROWAKE / "config.js"


def test_arquivos_astrowake_existem():
    """Garante que todos os arquivos da LP Astrowake estão presentes."""
    assert INDEX_HTML.exists(), "index.html não encontrado em lp-astrowake"
    assert INSCRICAO_JS.exists(), "inscricao.js não encontrado em lp-astrowake"
    assert CONFIG_JS.exists(), "config.js não encontrado em lp-astrowake"


def test_popup_nao_fecha_ao_clicar_fora():
    """
    Garante que o véu/backdrop do modal (.modal-veu) NÃO possui o atributo data-fechar,
    impedindo que o modal feche acidentalmente ao clicar fora do cartão.
    Apenas o botão 'X' (.modal-x) deve conter data-fechar.
    """
    conteudo = INDEX_HTML.read_text(encoding="utf-8")
    
    # .modal-veu não pode ter data-fechar
    padrao_veu_sem_fechar = re.search(r'<div\s+class="modal-veu"[^>]*data-fechar', conteudo)
    assert padrao_veu_sem_fechar is None, "O elemento .modal-veu NÃO deve ter data-fechar (não pode fechar ao clicar fora)"
    assert '<div class="modal-veu"></div>' in conteudo, "Elemento .modal-veu deve existir sem data-fechar"

    # .modal-x deve ter data-fechar
    assert 'class="modal-x" data-fechar' in conteudo, "O botão fechar (.modal-x) deve ter data-fechar"


def test_campo_whatsapp_possui_dropdown_ddi_brasil_padrao():
    """
    Garante que o campo de WhatsApp possui um select de DDI com Brasil (+55) selecionado por padrão,
    além de outras opções internacionais como Portugal (+351), EUA (+1), Espanha (+34), etc.
    """
    conteudo = INDEX_HTML.read_text(encoding="utf-8")

    assert 'id="in-ddi"' in conteudo, "Elemento select de DDI (#in-ddi) deve existir"
    assert 'class="ddi-select"' in conteudo, "Classe ddi-select deve estar aplicada no seletor"
    assert '<option value="55" selected>🇧🇷 +55</option>' in conteudo, "Brasil (+55) deve ser a opção padrão selecionada"
    assert 'value="351"' in conteudo, "Portugal (+351) deve estar nas opções de DDI"
    assert 'value="1"' in conteudo, "EUA (+1) deve estar nas opções de DDI"
    assert 'value="34"' in conteudo, "Espanha (+34) deve estar nas opções de DDI"


def test_estilos_campo_telefone_ddi_presentes():
    """Garante que as regras de CSS para .campo-telefone e .ddi-select estão declaradas."""
    conteudo = INDEX_HTML.read_text(encoding="utf-8")

    assert ".campo-telefone{" in conteudo or ".campo-telefone {" in conteudo
    assert ".ddi-select" in conteudo
    assert ".ddi-wrapper" in conteudo


def test_inscricao_js_suporta_ddi_e_mascara_internacional():
    """
    Garante que o script inscricao.js captura o DDI, formata conforme o país,
    valida adequadamente e inclui o DDI no payload enviado ao webhook.
    """
    conteudo = INSCRICAO_JS.read_text(encoding="utf-8")

    assert "const campoDdi" in conteudo or "document.getElementById('in-ddi')" in conteudo
    assert "mascaraInternacional" in conteudo, "Função mascaraInternacional deve estar presente"
    assert "ddi: ddi" in conteudo, "DDI deve ser enviado no payload do webhook"
    assert "numeroE164" in conteudo or "'+' + ddi" in conteudo, "Número deve ser formatado em E.164 (+DDI e dígitos)"


def test_config_js_estrutura_webhook():
    """Garante que config.js possui a estrutura esperada para WEBHOOK e GRUPO_WHATSAPP."""
    conteudo = CONFIG_JS.read_text(encoding="utf-8")

    assert "window.ASTROWAKE" in conteudo
    assert "WEBHOOK:" in conteudo
    assert "GRUPO_WHATSAPP:" in conteudo
