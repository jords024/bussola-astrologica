@echo off
chcp 65001 >nul
title Bussola Astrologica - funil de teste
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Ambiente Python nao encontrado em .venv
  pause & exit /b 1
)

echo.
echo   Neste computador:  http://127.0.0.1:8765
echo.
echo   No celular, mesma rede Wi-Fi:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  for /f "tokens=1" %%b in ("%%a") do echo      http://%%b:8765
)
echo.
echo   Se o celular nao abrir, rode liberar-celular.cmd como Administrador.
echo   Para parar o servidor: feche esta janela ou aperte Ctrl+C.
echo.

.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8765
pause
