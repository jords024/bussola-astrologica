@echo off
chcp 65001 >nul
title Liberar porta 8765 para o celular

net session >nul 2>&1
if errorlevel 1 (
  echo.
  echo   Precisa rodar como Administrador.
  echo   Feche, clique com o botao direito neste arquivo
  echo   e escolha "Executar como administrador".
  echo.
  pause & exit /b 1
)

if /i "%~1"=="remover" (
  netsh advfirewall firewall delete rule name="Bussola Astrologica dev 8765" >nul 2>&1
  echo   Regra removida. A porta 8765 voltou a ficar fechada.
  pause & exit /b 0
)

netsh advfirewall firewall delete rule name="Bussola Astrologica dev 8765" >nul 2>&1
netsh advfirewall firewall add rule name="Bussola Astrologica dev 8765" ^
  dir=in action=allow protocol=TCP localport=8765 remoteip=localsubnet >nul

if errorlevel 1 (
  echo   Nao consegui criar a regra.
  pause & exit /b 1
)

echo.
echo   Porta 8765 liberada, so para aparelhos da sua propria rede.
echo   Nada fica exposto para a internet.
echo.
echo   No celular, abra:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  for /f "tokens=1" %%b in ("%%a") do echo      http://%%b:8765
)
echo.
echo   Para desfazer depois:  liberar-celular.cmd remover
echo.
pause
