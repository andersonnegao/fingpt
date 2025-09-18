@echo off
echo 🚀 Instalador do Sistema de Trading Automatizado
echo ================================================

REM Verificar Python
echo 🐍 Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python não encontrado!
    echo 📥 Baixe e instale Python de: https://python.org/downloads/
    echo ⚠️  IMPORTANTE: Marque "Add to PATH" durante a instalação
    pause
    exit /b 1
) else (
    echo ✅ Python encontrado
)

REM Verificar Node.js
echo 📦 Verificando Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js não encontrado!
    echo 📥 Baixe e instale Node.js de: https://nodejs.org/
    echo ⚠️  Escolha a versão LTS
    pause
    exit /b 1
) else (
    echo ✅ Node.js encontrado
)

REM Verificar npm
echo 📦 Verificando npm...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm não encontrado!
    echo ⚠️  npm vem com Node.js. Reinstale Node.js
    pause
    exit /b 1
) else (
    echo ✅ npm encontrado
)

REM Instalar dependências Python
echo 📚 Instalando dependências Python...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Erro ao instalar dependências Python
    pause
    exit /b 1
) else (
    echo ✅ Dependências Python instaladas
)

REM Configurar dashboard
echo 🎨 Configurando dashboard...
cd trading-dashboard
if not exist package.json (
    echo ❌ Arquivo package.json não encontrado
    pause
    exit /b 1
)

npm install
if %errorlevel% neq 0 (
    echo ❌ Erro ao instalar dependências do dashboard
    pause
    exit /b 1
) else (
    echo ✅ Dashboard configurado
)

cd ..

REM Criar diretórios
echo 📁 Criando diretórios...
if not exist data mkdir data
if not exist logs mkdir logs

echo.
echo 🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!
echo ====================================
echo.
echo 📋 PRÓXIMOS PASSOS:
echo 1. Edite config\settings.py com suas preferências
echo 2. Execute: python main_trading_system.py
echo 3. Em outro terminal: cd trading-dashboard ^&^& npm run dev
echo 4. Acesse: http://localhost:5173
echo.
echo 📖 Leia o README.md para instruções detalhadas
echo.
echo 🚀 Bom trading!
echo.
pause

