# -*- coding: utf-8 -*-
"""Serviço de autenticação, sessão por cookie e tela de login do Painel Admin."""
from __future__ import annotations

import secrets
from typing import Optional

from fastapi import HTTPException

import config

COOKIE_SESSAO_NOME = "bsl_painel_sessao"
_SESSOES_ATIVAS: dict[str, str] = {}


class PainelNaoAutenticadoError(HTTPException):
    """Exceção 401 sem cabeçalho WWW-Authenticate para exibir tela de login HTML customizada."""

    def __init__(self, detail: str = "autenticação necessária"):
        super().__init__(status_code=401, detail=detail)


def criar_sessao_painel(usuario: str) -> str:
    token = secrets.token_urlsafe(32)
    _SESSOES_ATIVAS[token] = usuario
    if len(_SESSOES_ATIVAS) > 500:
        antigos = list(_SESSOES_ATIVAS.keys())[:100]
        for k in antigos:
            _SESSOES_ATIVAS.pop(k, None)
    return token


def validar_sessao_painel(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    return _SESSOES_ATIVAS.get(token)


def encerrar_sessao_painel(token: Optional[str]) -> None:
    if token:
        _SESSOES_ATIVAS.pop(token, None)


def validar_credenciais_painel(identificador: str, senha: str) -> Optional[str]:
    """Valida tanto o par (SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD) quanto (PAINEL_USUARIO, PAINEL_SENHA)."""
    ident = (identificador or "").strip()
    pwd = (senha or "").strip()
    if not ident or not pwd:
        return None

    # 1. Credenciais de Super Admin (E-mail ou Nome + Senha)
    admin_email = getattr(config, "SUPER_ADMIN_EMAIL", "aryarajmarketing@gmail.com").strip()
    admin_nome = getattr(config, "SUPER_ADMIN_NAME", "Aryaraj").strip()
    admin_senha = getattr(config, "SUPER_ADMIN_PASSWORD", "123456").strip()

    if admin_senha and secrets.compare_digest(pwd, admin_senha):
        if (admin_email and secrets.compare_digest(ident.lower(), admin_email.lower())) or (
            admin_nome and secrets.compare_digest(ident.lower(), admin_nome.lower())
        ):
            return admin_email or ident

    # 2. Credenciais clássicas do Painel (PAINEL_USUARIO + PAINEL_SENHA)
    painel_user = (config.PAINEL_USUARIO or "").strip()
    painel_pwd = (config.PAINEL_SENHA or "").strip()
    if painel_user and painel_pwd:
        if secrets.compare_digest(ident, painel_user) and secrets.compare_digest(pwd, painel_pwd):
            return painel_user

    return None


def renderizar_tela_login(erro: str = "") -> str:
    """Renderiza a tela de login premium da Bússola Astrológica."""
    erro_visivel = "flex" if erro else "none"
    erro_texto = erro or ""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Login · Painel Bússola Astrológica</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,500;0,600;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-deep: #0b0a08;
      --bg-card: rgba(23, 21, 17, 0.88);
      --amber: #d4a24c;
      --amber-bright: #e8b963;
      --amber-glow: rgba(212, 162, 76, 0.22);
      --sand: #f4efe6;
      --sand-muted: #9e9587;
      --line: rgba(244, 239, 230, 0.11);
      --danger: #ef4444;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background-color: var(--bg-deep);
      background-image:
        radial-gradient(circle at 50% 0%, rgba(212, 162, 76, 0.16) 0%, transparent 58%),
        radial-gradient(circle at 85% 90%, rgba(212, 162, 76, 0.08) 0%, transparent 45%);
      color: var(--sand);
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      -webkit-font-smoothing: antialiased;
    }}
    .login-wrapper {{
      width: 100%;
      max-width: 430px;
      animation: surgir 0.45s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    @keyframes surgir {{
      from {{ opacity: 0; transform: translateY(14px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .login-card {{
      background: var(--bg-card);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(212, 162, 76, 0.26);
      border-radius: 22px;
      padding: 38px 34px 34px;
      box-shadow:
        0 28px 65px rgba(0, 0, 0, 0.72),
        0 0 0 1px rgba(255, 255, 255, 0.03) inset;
      position: relative;
      overflow: hidden;
    }}
    .login-card::before {{
      content: "";
      position: absolute;
      top: 0;
      left: 15%;
      right: 15%;
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--amber), transparent);
      opacity: 0.75;
    }}
    .login-header {{
      text-align: center;
      margin-bottom: 28px;
    }}
    .login-logo {{
      width: 58px;
      height: 58px;
      margin: 0 auto 14px;
      border-radius: 16px;
      background: radial-gradient(circle at 30% 30%, rgba(212, 162, 76, 0.25), rgba(212, 162, 76, 0.06));
      border: 1px solid rgba(212, 162, 76, 0.38);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28px;
      box-shadow: 0 10px 25px rgba(212, 162, 76, 0.14);
    }}
    .login-badge {{
      display: inline-block;
      font-size: 10.5px;
      font-weight: 700;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--amber);
      margin-bottom: 8px;
    }}
    .login-title {{
      font-family: 'EB Garamond', Georgia, serif;
      font-size: 31px;
      font-weight: 500;
      color: var(--sand);
      line-height: 1.15;
      margin-bottom: 8px;
    }}
    .login-subtitle {{
      font-size: 13.5px;
      color: var(--sand-muted);
      line-height: 1.5;
    }}
    .login-erro {{
      display: {erro_visivel};
      align-items: center;
      gap: 10px;
      background: rgba(239, 68, 68, 0.12);
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: #fca5a5;
      padding: 12px 14px;
      border-radius: 12px;
      font-size: 13px;
      line-height: 1.4;
      margin-bottom: 20px;
    }}
    .field-group {{
      margin-bottom: 18px;
    }}
    .field-label {{
      display: block;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.04em;
      color: #d5cec2;
      margin-bottom: 8px;
    }}
    .input-box {{
      position: relative;
      display: flex;
      align-items: center;
    }}
    .input-icon {{
      position: absolute;
      left: 15px;
      color: var(--sand-muted);
      font-size: 16px;
      pointer-events: none;
      transition: color 0.2s ease;
      display: flex;
      align-items: center;
    }}
    .input-field {{
      width: 100%;
      height: 50px;
      padding: 0 44px 0 44px;
      background: rgba(11, 10, 8, 0.75);
      border: 1px solid var(--line);
      border-radius: 13px;
      color: var(--sand);
      font-family: inherit;
      font-size: 14.5px;
      transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
      outline: none;
    }}
    .input-field::placeholder {{
      color: rgba(158, 149, 135, 0.48);
    }}
    .input-field:focus {{
      border-color: var(--amber);
      background: rgba(16, 14, 11, 0.95);
      box-shadow: 0 0 0 3.5px var(--amber-glow);
    }}
    .input-box:focus-within .input-icon {{
      color: var(--amber);
    }}
    .toggle-pwd {{
      position: absolute;
      right: 12px;
      background: none;
      border: none;
      color: var(--sand-muted);
      cursor: pointer;
      padding: 6px;
      border-radius: 8px;
      font-size: 15px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: color 0.2s ease, background 0.2s ease;
    }}
    .toggle-pwd:hover {{
      color: var(--sand);
      background: rgba(255, 255, 255, 0.05);
    }}
    .btn-submit {{
      width: 100%;
      height: 52px;
      margin-top: 8px;
      border: none;
      border-radius: 13px;
      background: linear-gradient(135deg, #e5b358 0%, #c89132 100%);
      color: #14110b;
      font-family: inherit;
      font-size: 15px;
      font-weight: 700;
      letter-spacing: 0.02em;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      box-shadow: 0 10px 26px rgba(212, 162, 76, 0.28);
      transition: transform 0.18s ease, filter 0.18s ease, box-shadow 0.18s ease;
    }}
    .btn-submit:hover:not(:disabled) {{
      transform: translateY(-1px);
      filter: brightness(1.06);
      box-shadow: 0 14px 32px rgba(212, 162, 76, 0.38);
    }}
    .btn-submit:active:not(:disabled) {{
      transform: translateY(0);
    }}
    .btn-submit:disabled {{
      opacity: 0.65;
      cursor: wait;
    }}
    .login-footer {{
      margin-top: 22px;
      text-align: center;
      font-size: 12px;
      color: rgba(158, 149, 135, 0.65);
    }}
  </style>
</head>
<body>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">🧭</div>
        <span class="login-badge">✦ Acesso Administrativo</span>
        <h1 class="login-title">Bússola Astrológica</h1>
        <p class="login-subtitle">Digite seu e-mail e senha para acessar as métricas e configurações do funil.</p>
      </div>

      <div id="login-erro" class="login-erro" role="alert">
        <span>⚠️</span>
        <span id="login-erro-msg">{erro_texto}</span>
      </div>

      <form id="form-login-painel" onsubmit="return submeterLoginPainel(event);">
        <div class="field-group">
          <label class="field-label" for="login-email">E-mail ou Usuário</label>
          <div class="input-box">
            <span class="input-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
            </span>
            <input
              type="text"
              id="login-email"
              name="email"
              class="input-field"
              placeholder="aryarajmarketing@gmail.com"
              autocomplete="username"
              required
              autofocus
            >
          </div>
        </div>

        <div class="field-group">
          <label class="field-label" for="login-senha">Senha</label>
          <div class="input-box">
            <span class="input-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            </span>
            <input
              type="password"
              id="login-senha"
              name="senha"
              class="input-field"
              placeholder="Digite sua senha"
              autocomplete="current-password"
              required
            >
            <button type="button" class="toggle-pwd" id="btn-toggle-senha" onclick="alternarVisibilidadeSenha()" title="Mostrar ou ocultar senha">
              👁️
            </button>
          </div>
        </div>

        <button type="submit" class="btn-submit" id="btn-login-entrar">
          <span>Entrar no Painel</span>
          <span>→</span>
        </button>
      </form>

      <div class="login-footer">
        Ambiente seguro · Bússola Astrológica
      </div>
    </div>
  </div>

  <script>
    function alternarVisibilidadeSenha() {{
      var inp = document.getElementById('login-senha');
      var btn = document.getElementById('btn-toggle-senha');
      if (!inp) return;
      if (inp.type === 'password') {{
        inp.type = 'text';
        if (btn) btn.textContent = '🙈';
      }} else {{
        inp.type = 'password';
        if (btn) btn.textContent = '👁️';
      }}
    }}

    function submeterLoginPainel(ev) {{
      ev.preventDefault();
      var emailEl = document.getElementById('login-email');
      var senhaEl = document.getElementById('login-senha');
      var erroBox = document.getElementById('login-erro');
      var erroMsg = document.getElementById('login-erro-msg');
      var btn = document.getElementById('btn-login-entrar');

      var email = (emailEl ? emailEl.value : '').trim();
      var senha = (senhaEl ? senhaEl.value : '').trim();
      if (!email || !senha) return false;

      if (erroBox) erroBox.style.display = 'none';
      if (btn) {{
        btn.disabled = true;
        btn.innerHTML = '<span>Verificando acesso...</span>';
      }}

      fetch('/painel/login', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json', 'Accept': 'application/json' }},
        body: JSON.stringify({{ email: email, senha: senha }})
      }})
      .then(function(r) {{
        return r.json().then(function(d) {{ return {{ status: r.status, ok: r.ok, data: d }}; }});
      }})
      .then(function(res) {{
        if (res.ok && res.data && res.data.ok) {{
          window.location.reload();
        }} else {{
          if (erroBox && erroMsg) {{
            erroMsg.textContent = (res.data && res.data.detail) ? res.data.detail : 'E-mail ou senha incorretos.';
            erroBox.style.display = 'flex';
          }}
          if (btn) {{
            btn.disabled = false;
            btn.innerHTML = '<span>Entrar no Painel</span><span>→</span>';
          }}
        }}
      }})
      .catch(function() {{
        if (erroBox && erroMsg) {{
          erroMsg.textContent = 'Erro de conexão ao tentar entrar. Tente novamente.';
          erroBox.style.display = 'flex';
        }}
        if (btn) {{
          btn.disabled = false;
          btn.innerHTML = '<span>Entrar no Painel</span><span>→</span>';
        }}
      }});
      return false;
    }}
  </script>
</body>
</html>"""
