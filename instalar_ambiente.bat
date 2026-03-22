@echo off
setlocal enabledelayedexpansion

:: ======================================================
:: CONFIGURAÇÃO DE CAMINHOS
:: ======================================================
set "PASTA_PROJETO=%~dp0"
set "ENV_LOCAL=%PASTA_PROJETO%.venv"

echo ======================================================
echo INSTALACAO DE AMBIENTE UV - AUTOMACAO DE PRECOS
echo ======================================================
echo.

:: 1. Configurações para passar pelo Firewall/Proxy da empresa
set "UV_INSECURE=true"
set "UV_NATIVE_TLS=true"
set "UV_LINK_MODE=copy"

:: 2. Criar ou recriar a pasta do ambiente (.venv)
if exist "%ENV_LOCAL%" (
    echo [!] O ambiente %ENV_LOCAL% ja existe. Apagando para recriar...
    rmdir /S /Q "%ENV_LOCAL%"
)

echo.
echo [1/3] Verificando executavel UV...

:: Tenta ver se o comando 'uv' já está instalado no Windows globalmente
where uv >nul 2>nul
if %errorlevel% equ 0 (
    set "UV_CMD=uv"
    echo [OK] UV encontrado no sistema.
) else (
    :: Se não estiver instalado globalmente, procura o ficheiro uv.exe na pasta
    if exist "%PASTA_PROJETO%uv.exe" (
        set "UV_CMD="%PASTA_PROJETO%uv.exe""
        echo [OK] Arquivo uv.exe encontrado na pasta do projeto.
    ) else (
        echo [!] UV nao encontrado. Tentando baixar e instalar automaticamente da internet...
        
        :: Usa o PowerShell para baixar e executar o instalador oficial do UV
        powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
        
        :: O script oficial instala o uv na pasta do utilizador. Vamos verificar se deu certo:
        if exist "%USERPROFILE%\.local\bin\uv.exe" (
            set "UV_CMD="%USERPROFILE%\.local\bin\uv.exe""
            echo [OK] UV baixado e instalado com sucesso!
        ) else (
            :: Se falhar (ex: firewall da empresa bloqueou o PowerShell), avisa o utilizador
            echo [ERRO] Nao foi possivel instalar o UV automaticamente.
            echo O Firewall da empresa pode ter bloqueado o download.
            echo Por favor, baixe o uv.exe manualmente do GitHub e coloque na pasta: %PASTA_PROJETO%
            pause
            exit /b
        )
    )
)

echo.
echo [2/3] Instalando Python e criando ambiente local (.venv)...
%UV_CMD% venv "%ENV_LOCAL%" --python 3.12

echo.
echo [3/3] Sincronizando bibliotecas do pyproject.toml...
%UV_CMD% sync

if %errorlevel% equ 0 (
    echo.
    echo ======================================================
    echo SUCESSO! Ambiente configurado na pasta: 
    echo %ENV_LOCAL%
    echo ======================================================
) else (
    echo.
    echo [ERRO] Falha na sincronizacao das bibliotecas.
)
echo.
pause