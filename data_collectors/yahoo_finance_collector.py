"""
Coletor de Dados do Yahoo Finance via Manus API Hub
Coleta dados de preços, holders e insights para análise de whales
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

# Adicionar o caminho do Manus API
sys.path.append('/opt/.manus/.sandbox-runtime')
from data_api import ApiClient

# Importar configurações
sys.path.append('/home/ubuntu/trading_system')
from config.settings import *

class YahooFinanceCollector:
    """Coletor de dados do Yahoo Finance via Manus API Hub"""
    
    def __init__(self):
        self.client = ApiClient()
        self.logger = self._setup_logger()
        self.data_cache = {}
        self.last_request_time = {}
        
    def _setup_logger(self):
        """Configura o logger para este coletor"""
        logger = logging.getLogger('YahooFinanceCollector')
        logger.setLevel(logging.INFO)
        
        # Handler para arquivo
        file_handler = logging.FileHandler(get_log_path('yahoo_collector.log'))
        file_handler.setLevel(logging.INFO)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(LOGGING_CONFIG['format'])
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _rate_limit_check(self, api_name: str):
        """Verifica rate limit antes de fazer request"""
        now = time.time()
        if api_name in self.last_request_time:
            time_diff = now - self.last_request_time[api_name]
            min_interval = 60 / YAHOO_FINANCE_CONFIG['rate_limit']  # segundos entre requests
            
            if time_diff < min_interval:
                sleep_time = min_interval - time_diff
                self.logger.info(f"Rate limit: aguardando {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self.last_request_time[api_name] = time.time()
    
    def get_stock_chart(self, symbol: str, interval: str = "1d", range_period: str = "1mo") -> Optional[Dict]:
        """
        Coleta dados de preços históricos
        
        Args:
            symbol: Símbolo da ação (ex: AAPL)
            interval: Intervalo (1m, 5m, 15m, 30m, 1h, 1d)
            range_period: Período (1d, 5d, 1mo, 3mo, 6mo, 1y)
        """
        try:
            self._rate_limit_check('stock_chart')
            
            response = self.client.call_api('YahooFinance/get_stock_chart', query={
                'symbol': symbol,
                'region': 'US',
                'interval': interval,
                'range': range_period,
                'includeAdjustedClose': True,
                'events': 'div,split'
            })
            
            if response and 'chart' in response and 'result' in response['chart']:
                result = response['chart']['result'][0]
                
                # Processar dados para formato mais útil
                processed_data = self._process_chart_data(result, symbol)
                
                self.logger.info(f"Dados coletados para {symbol}: {len(processed_data.get('prices', []))} pontos")
                return processed_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar dados de {symbol}: {e}")
            return None
    
    def get_stock_holders(self, symbol: str) -> Optional[Dict]:
        """
        Coleta informações sobre holders institucionais
        Essencial para whale watching!
        """
        try:
            self._rate_limit_check('stock_holders')
            
            response = self.client.call_api('YahooFinance/get_stock_holders', query={
                'symbol': symbol,
                'region': 'US',
                'lang': 'en-US'
            })
            
            if response and 'quoteSummary' in response:
                quote_summary = response['quoteSummary']
                if quote_summary and 'result' in quote_summary and quote_summary['result']:
                    result = quote_summary['result'][0]
                    
                    # Processar dados de holders
                    processed_holders = self._process_holders_data(result, symbol)
                    
                    self.logger.info(f"Holders coletados para {symbol}: {len(processed_holders.get('institutional', []))} institucionais")
                    return processed_holders
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar holders de {symbol}: {e}")
            return None
    
    def get_stock_insights(self, symbol: str) -> Optional[Dict]:
        """
        Coleta insights e análises técnicas
        """
        try:
            self._rate_limit_check('stock_insights')
            
            response = self.client.call_api('YahooFinance/get_stock_insights', query={
                'symbol': symbol
            })
            
            if response:
                processed_insights = self._process_insights_data(response, symbol)
                self.logger.info(f"Insights coletados para {symbol}")
                return processed_insights
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar insights de {symbol}: {e}")
            return None
    
    def _process_chart_data(self, raw_data: Dict, symbol: str) -> Dict:
        """Processa dados de preços em formato útil"""
        try:
            meta = raw_data.get('meta', {})
            timestamps = raw_data.get('timestamp', [])
            quotes = raw_data.get('indicators', {}).get('quote', [{}])[0]
            
            prices = []
            for i, timestamp in enumerate(timestamps):
                if i < len(quotes.get('open', [])):
                    price_data = {
                        'timestamp': timestamp,
                        'datetime': datetime.fromtimestamp(timestamp),
                        'open': quotes['open'][i],
                        'high': quotes['high'][i],
                        'low': quotes['low'][i],
                        'close': quotes['close'][i],
                        'volume': quotes['volume'][i]
                    }
                    prices.append(price_data)
            
            # Calcular métricas importantes
            current_price = meta.get('regularMarketPrice', 0)
            volume_avg = sum([p['volume'] for p in prices[-20:] if p['volume']]) / min(20, len(prices))
            current_volume = prices[-1]['volume'] if prices else 0
            volume_spike = current_volume / volume_avg if volume_avg > 0 else 0
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'currency': meta.get('currency', 'USD'),
                'exchange': meta.get('exchangeName', ''),
                'market_cap': meta.get('marketCap', 0),
                'volume_avg_20d': volume_avg,
                'volume_spike': volume_spike,
                'prices': prices,
                'meta': meta,
                'collected_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao processar dados de preços: {e}")
            return {}
    
    def _process_holders_data(self, raw_data: Dict, symbol: str) -> Dict:
        """Processa dados de holders para whale detection"""
        try:
            institutional = []
            mutual_funds = []
            insiders = []
            
            # Processar institutional holders
            inst_data = raw_data.get('institutionalHolders', {})
            if inst_data and 'holders' in inst_data:
                for holder in inst_data['holders']:
                    processed_holder = {
                        'organization': holder.get('organization', ''),
                        'shares': self._extract_value(holder.get('shares', {})),
                        'value': self._extract_value(holder.get('value', {})),
                        'pct_held': self._extract_value(holder.get('pctHeld', {})),
                        'date_reported': self._extract_date(holder.get('dateReported', {})),
                        'is_target_whale': holder.get('organization', '') in TARGET_INSTITUTIONS
                    }
                    institutional.append(processed_holder)
            
            # Processar mutual fund holders
            mf_data = raw_data.get('mutualFundHolders', {})
            if mf_data and 'holders' in mf_data:
                for holder in mf_data['holders']:
                    processed_holder = {
                        'organization': holder.get('organization', ''),
                        'shares': self._extract_value(holder.get('shares', {})),
                        'value': self._extract_value(holder.get('value', {})),
                        'pct_held': self._extract_value(holder.get('pctHeld', {})),
                        'date_reported': self._extract_date(holder.get('dateReported', {}))
                    }
                    mutual_funds.append(processed_holder)
            
            # Processar insider holders
            insider_data = raw_data.get('insiderHolders', {})
            if insider_data and 'holders' in insider_data:
                for holder in insider_data['holders']:
                    processed_holder = {
                        'name': holder.get('name', ''),
                        'relation': holder.get('relation', ''),
                        'position_direct': self._extract_value(holder.get('positionDirect', {})),
                        'latest_trans_date': self._extract_date(holder.get('latestTransDate', {})),
                        'transaction_description': holder.get('transactionDescription', '')
                    }
                    insiders.append(processed_holder)
            
            return {
                'symbol': symbol,
                'institutional': institutional,
                'mutual_funds': mutual_funds,
                'insiders': insiders,
                'whale_institutions_count': len([h for h in institutional if h['is_target_whale']]),
                'collected_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao processar dados de holders: {e}")
            return {}
    
    def _process_insights_data(self, raw_data: Dict, symbol: str) -> Dict:
        """Processa dados de insights"""
        try:
            return {
                'symbol': symbol,
                'insights': raw_data.get('insights', {}),
                'raw_data': raw_data,
                'collected_at': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Erro ao processar insights: {e}")
            return {}
    
    def _extract_value(self, value_dict: Dict) -> float:
        """Extrai valor numérico de dicionários do Yahoo Finance"""
        if isinstance(value_dict, dict):
            return value_dict.get('raw', 0)
        return value_dict if isinstance(value_dict, (int, float)) else 0
    
    def _extract_date(self, date_dict: Dict) -> str:
        """Extrai data formatada de dicionários do Yahoo Finance"""
        if isinstance(date_dict, dict):
            return date_dict.get('fmt', '')
        return str(date_dict) if date_dict else ''
    
    def collect_all_symbols(self, symbols: List[str] = None) -> Dict[str, Dict]:
        """
        Coleta dados para todos os símbolos configurados
        """
        if symbols is None:
            symbols = STOCK_SYMBOLS
        
        all_data = {}
        
        for symbol in symbols:
            self.logger.info(f"Coletando dados para {symbol}")
            
            symbol_data = {
                'chart': self.get_stock_chart(symbol),
                'holders': self.get_stock_holders(symbol),
                'insights': self.get_stock_insights(symbol)
            }
            
            all_data[symbol] = symbol_data
            
            # Pequena pausa entre símbolos
            time.sleep(1)
        
        return all_data
    
    def detect_whale_movements(self, symbol_data: Dict) -> List[Dict]:
        """
        Detecta movimentos de whales baseado nos dados coletados
        """
        alerts = []
        
        try:
            chart_data = symbol_data.get('chart', {})
            holders_data = symbol_data.get('holders', {})
            
            if not chart_data or not holders_data:
                return alerts
            
            symbol = chart_data.get('symbol', '')
            
            # Verificar volume spike
            volume_spike = chart_data.get('volume_spike', 0)
            if volume_spike >= WHALE_CRITERIA['min_volume_spike']:
                alerts.append({
                    'type': 'volume_spike',
                    'symbol': symbol,
                    'volume_spike': volume_spike,
                    'message': f"{symbol}: Volume spike de {volume_spike:.2f}x detectado",
                    'severity': 'high' if volume_spike > 5 else 'medium'
                })
            
            # Verificar presença de whales institucionais
            whale_count = holders_data.get('whale_institutions_count', 0)
            if whale_count > 0:
                whale_institutions = [h for h in holders_data.get('institutional', []) if h['is_target_whale']]
                total_whale_percentage = sum([h['pct_held'] for h in whale_institutions])
                
                alerts.append({
                    'type': 'whale_presence',
                    'symbol': symbol,
                    'whale_count': whale_count,
                    'total_percentage': total_whale_percentage,
                    'message': f"{symbol}: {whale_count} whales institucionais detectedos ({total_whale_percentage:.2f}% do total)",
                    'severity': 'high' if total_whale_percentage > 10 else 'medium'
                })
            
        except Exception as e:
            self.logger.error(f"Erro ao detectar whale movements: {e}")
        
        return alerts
    
    def save_data(self, data: Dict, filename: str = None):
        """Salva dados coletados em arquivo JSON"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"yahoo_data_{timestamp}.json"
            
            filepath = get_data_path(filename)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info(f"Dados salvos em {filepath}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados: {e}")

# ==================== EXEMPLO DE USO ====================
if __name__ == "__main__":
    collector = YahooFinanceCollector()
    
    # Testar com alguns símbolos
    test_symbols = ["AAPL", "MSFT", "TSLA"]
    
    print("Iniciando coleta de dados...")
    all_data = collector.collect_all_symbols(test_symbols)
    
    # Detectar whale movements
    print("\nDetectando movimentos de whales...")
    all_alerts = []
    for symbol, data in all_data.items():
        alerts = collector.detect_whale_movements(data)
        all_alerts.extend(alerts)
        
        if alerts:
            print(f"\n🐋 ALERTAS para {symbol}:")
            for alert in alerts:
                print(f"  - {alert['message']}")
    
    if not all_alerts:
        print("Nenhum movimento de whale detectado no momento.")
    
    # Salvar dados
    collector.save_data(all_data)
    print(f"\nDados coletados e salvos para {len(test_symbols)} símbolos.")

