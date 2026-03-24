@echo off
REM ============================================================
REM CRM VITAO360 — SESSION STARTER
REM Roda boot + compliance ANTES de abrir Claude Code.
REM Uso: duplo-clique ou rodar no terminal.
REM ============================================================

echo ============================================================
echo  CRM VITAO360 — SESSION STARTER
echo ============================================================

cd /d "%~dp0\.."

echo.
echo [1/3] Session Boot...
python scripts\session_boot.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo BOOT FALHOU — corrija os erros acima antes de abrir Claude Code.
    pause
    exit /b 1
)

echo.
echo [2/3] Compliance Gate...
python scripts\compliance_gate.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo COMPLIANCE FALHOU — corrija os erros acima.
    pause
    exit /b 1
)

echo.
echo [3/3] Token gerado. Abrindo Claude Code...
echo.
echo ============================================================
echo  PRONTO — Pode trabalhar. Token valido por 4 horas.
echo ============================================================
echo.

REM Abrir Claude Code no diretorio do projeto
claude .

pause
