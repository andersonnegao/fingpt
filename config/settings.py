"""
Configurações do Sistema de Trading Automatizado
Todas as configurações centralizadas aqui
"""

import os
from typing import Dict, List

# ==================== CONFIGURAÇÕES GERAIS ====================
PROJECT_ROOT = "/home/ubuntu/trading_system"
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

# ==================== CONFIGURAÇÕES DE APIS ====================
# Yahoo Finance (via Manus API Hub)
YAHOO_FINANCE_CONFIG = {
    "base_url": "manus_api_hub",
    "rate_limit": 100,  # requests por minuto
    "timeout": 30
}

# SEC EDGAR API
SEC_EDGAR_CONFIG = {
    "base_url": "https://data.sec.gov",
    "rate_limit": 10,  # requests por segundo (limite oficial)
    "user_agent": "TradingSystem/1.0 (contact@example.com)",
    "timeout": 30
}

# Whale Alert API
WHALE_ALERT_CONFIG = {
    "base_url": "https://api.whale-alert.io",
    "api_key": None,  # Usar versão gratuita primeiro
    "rate_limit": 60,  # requests por hora (free tier)
    "timeout": 30
}

# ==================== SÍMBOLOS PARA MONITORAMENTO ====================
# Ações para monitorar (grandes players)
STOCK_SYMBOLS = [
    # Tech Giants
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA",
    # Financial Giants
    "BRK-A", "JPM", "BAC", "WFC", "GS", "MS",
    # ETFs importantes
    "SPY", "QQQ", "IWM", "VTI", "VOO"
]

# Crypto para monitorar whales
CRYPTO_SYMBOLS = [
    "BTC", "ETH", "BNB", "ADA", "SOL", "DOT", "MATIC", "LINK"
]

# ==================== CONFIGURAÇÕES DE TRADING ====================
# Gestão de Risco
RISK_MANAGEMENT = {
    "max_position_size": 0.05,  # 5% do portfolio por posição
    "max_daily_loss": 0.02,     # 2% perda máxima diária
    "stop_loss_pct": 0.03,      # 3% stop loss
    "take_profit_pct": 0.06,    # 6% take profit (2:1 ratio)
    "max_open_positions": 10,   # Máximo 10 posições abertas
    "min_volume": 1000000,      # Volume mínimo para trading
}

# Configurações de Análise Técnica
TECHNICAL_ANALYSIS = {
    "rsi_period": 14,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bollinger_period": 20,
    "bollinger_std": 2,
    "volume_sma": 20,
    "price_sma_short": 10,
    "price_sma_long": 50
}

# ==================== CONFIGURAÇÕES DE WHALES ====================
# Critérios para identificar movimentos de whales
WHALE_CRITERIA = {
    # Stocks - baseado em volume e valor
    "min_volume_spike": 3.0,    # 3x volume médio
    "min_price_change": 0.02,   # 2% mudança de preço
    "min_trade_value": 10000000,  # $10M valor mínimo
    
    # Crypto - baseado em valor das transações
    "btc_whale_threshold": 100,     # 100 BTC
    "eth_whale_threshold": 1000,    # 1000 ETH
    "min_crypto_value": 1000000,    # $1M valor mínimo
}

# ==================== CONFIGURAÇÕES DE INSTITUTIONAL TRACKING ====================
# Hedge funds e instituições para monitorar
TARGET_INSTITUTIONS = [
    "BERKSHIRE HATHAWAY INC",
    "BLACKROCK INC.",
    "VANGUARD GROUP INC",
    "STATE STREET CORP",
    "FIDELITY MANAGEMENT & RESEARCH COMPANY LLC",
    "JPMORGAN CHASE & CO",
    "BANK OF AMERICA CORP",
    "GOLDMAN SACHS GROUP INC",
    "MORGAN STANLEY",
    "CITADEL ADVISORS LLC"
]

# ==================== CONFIGURAÇÕES DE ALERTAS ====================
ALERT_CONFIG = {
    "telegram_enabled": False,  # Configurar depois
    "email_enabled": False,     # Configurar depois
    "console_enabled": True,
    "log_enabled": True,
    
    # Tipos de alertas
    "whale_movement": True,
    "institutional_filing": True,
    "technical_signal": True,
    "risk_alert": True,
    "profit_target": True
}

# ==================== CONFIGURAÇÕES DE DADOS ====================
DATA_CONFIG = {
    "update_frequency": 300,    # 5 minutos
    "historical_days": 365,    # 1 ano de dados históricos
    "save_raw_data": True,
    "compress_old_data": True,
    "max_file_size_mb": 100,
    
    # Timeframes para análise
    "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
    "primary_timeframe": "5m"
}

# ==================== CONFIGURAÇÕES DE FINGPT ====================
FINGPT_CONFIG = {
    "model_path": os.path.join(MODELS_DIR, "fingpt"),
    "max_tokens": 2048,
    "temperature": 0.1,  # Baixa para análises mais consistentes
    "batch_size": 4,
    
    # Prompts específicos
    "sentiment_prompt": "Analyze the sentiment of this financial news and rate from -1 (very negative) to 1 (very positive):",
    "prediction_prompt": "Based on this financial data, predict the likely price movement in the next 24 hours:",
    "risk_prompt": "Assess the risk level of this trading opportunity from 1 (low risk) to 10 (high risk):"
}

# ==================== CONFIGURAÇÕES DE LOGGING ====================
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "max_file_size": "10MB",
    "backup_count": 5,
    "console_output": True
}

# ==================== FUNÇÕES AUXILIARES ====================
def get_data_path(filename: str) -> str:
    """Retorna o caminho completo para um arquivo de dados"""
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, filename)

def get_log_path(filename: str) -> str:
    """Retorna o caminho completo para um arquivo de log"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    return os.path.join(LOGS_DIR, filename)

def get_model_path(filename: str) -> str:
    """Retorna o caminho completo para um arquivo de modelo"""
    os.makedirs(MODELS_DIR, exist_ok=True)
    return os.path.join(MODELS_DIR, filename)

# ==================== VALIDAÇÃO DE CONFIGURAÇÕES ====================
def validate_config():
    """Valida se todas as configurações estão corretas"""
    errors = []
    
    # Verificar se os diretórios podem ser criados
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(LOGS_DIR, exist_ok=True)
        os.makedirs(MODELS_DIR, exist_ok=True)
    except Exception as e:
        errors.append(f"Erro ao criar diretórios: {e}")
    
    # Verificar configurações de risco
    if RISK_MANAGEMENT["max_position_size"] > 0.2:
        errors.append("max_position_size muito alto (>20%)")
    
    if RISK_MANAGEMENT["stop_loss_pct"] > RISK_MANAGEMENT["take_profit_pct"]:
        errors.append("stop_loss maior que take_profit - ratio ruim")
    
    return errors

if __name__ == "__main__":
    errors = validate_config()
    if errors:
        print("Erros de configuração encontrados:")
        for error in errors:
            print(f"- {error}")
    else:
        print("Configurações validadas com sucesso!")

