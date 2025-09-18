#!/bin/bash

echo "🚀 Instalador do Sistema de Trading Automatizado"
echo "================================================"

# Detectar sistema operacional
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
else
    echo "❌ Sistema operacional não suportado: $OSTYPE"
    exit 1
fi

echo "📱 Sistema detectado: $OS"

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar Python
echo "🐍 Verificando Python..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo "✅ Python encontrado: $PYTHON_VERSION"
    
    # Verificar se é versão 3.8+
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        echo "✅ Versão do Python compatível"
    else
        echo "❌ Python 3.8+ necessário. Versão atual: $PYTHON_VERSION"
        exit 1
    fi
else
    echo "❌ Python não encontrado. Instalando..."
    
    if [[ "$OS" == "linux" ]]; then
        sudo apt update
        sudo apt install python3 python3-pip -y
    elif [[ "$OS" == "mac" ]]; then
        if command_exists brew; then
            brew install python@3.11
        else
            echo "❌ Homebrew não encontrado. Instale manualmente: https://brew.sh"
            exit 1
        fi
    fi
fi

# Verificar Node.js
echo "📦 Verificando Node.js..."
if command_exists node; then
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    echo "✅ Node.js encontrado: v$NODE_VERSION"
    
    if [ "$NODE_VERSION" -ge 16 ]; then
        echo "✅ Versão do Node.js compatível"
    else
        echo "❌ Node.js 16+ necessário. Versão atual: $NODE_VERSION"
        exit 1
    fi
else
    echo "❌ Node.js não encontrado. Instalando..."
    
    if [[ "$OS" == "linux" ]]; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt install nodejs -y
    elif [[ "$OS" == "mac" ]]; then
        if command_exists brew; then
            brew install node
        else
            echo "❌ Homebrew não encontrado. Instale manualmente: https://nodejs.org"
            exit 1
        fi
    fi
fi

# Instalar dependências Python
echo "📚 Instalando dependências Python..."
if command_exists pip3; then
    pip3 install -r requirements.txt
    echo "✅ Dependências Python instaladas"
else
    echo "❌ pip3 não encontrado"
    exit 1
fi

# Configurar dashboard
echo "🎨 Configurando dashboard..."
cd trading-dashboard

if [ -f "package.json" ]; then
    npm install
    echo "✅ Dashboard configurado"
else
    echo "❌ Arquivo package.json não encontrado no dashboard"
    exit 1
fi

cd ..

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p data logs

# Configurar permissões
chmod +x main_trading_system.py

echo ""
echo "🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "===================================="
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "1. Edite config/settings.py com suas preferências"
echo "2. Execute: python3 main_trading_system.py"
echo "3. Em outro terminal: cd trading-dashboard && npm run dev"
echo "4. Acesse: http://localhost:5173"
echo ""
echo "📖 Leia o README.md para instruções detalhadas"
echo ""
echo "🚀 Bom trading!"

