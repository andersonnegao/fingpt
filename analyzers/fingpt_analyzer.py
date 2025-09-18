"""
Analisador FinGPT para Trading Automatizado
Usa FinGPT para análise de sentimento, previsões e insights de trading
"""

import sys
import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import talib
import openai

# Importar configurações
sys.path.append('/home/ubuntu/trading_system')
from config.settings import *

class FinGPTAnalyzer:
    """Analisador que combina FinGPT com análise técnica tradicional"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.openai_client = openai.OpenAI()  # Usa as env vars já configuradas
        self.analysis_cache = {}
        
    def _setup_logger(self):
        """Configura o logger para este analisador"""
        logger = logging.getLogger('FinGPTAnalyzer')
        logger.setLevel(logging.INFO)
        
        # Handler para arquivo
        file_handler = logging.FileHandler(get_log_path('fingpt_analyzer.log'))
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
    
    def analyze_market_data(self, symbol_data: Dict) -> Dict:
        """
        Análise completa dos dados de mercado usando FinGPT + TA
        """
        try:
            symbol = symbol_data.get('chart', {}).get('symbol', 'UNKNOWN')
            self.logger.info(f"Analisando dados para {symbol}")
            
            # Extrair dados de preços
            price_data = self._extract_price_data(symbol_data)
            if not price_data:
                return {'error': 'Dados de preços insuficientes'}
            
            # Análise técnica tradicional
            technical_analysis = self._perform_technical_analysis(price_data)
            
            # Análise de holders/whales
            whale_analysis = self._analyze_whale_data(symbol_data)
            
            # Análise de sentimento com FinGPT
            sentiment_analysis = self._analyze_sentiment_with_fingpt(symbol_data)
            
            # Previsão de preço com FinGPT
            price_prediction = self._predict_price_with_fingpt(symbol_data, technical_analysis)
            
            # Avaliação de risco
            risk_assessment = self._assess_risk_with_fingpt(symbol_data, technical_analysis)
            
            # Combinar todas as análises
            comprehensive_analysis = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'technical_analysis': technical_analysis,
                'whale_analysis': whale_analysis,
                'sentiment_analysis': sentiment_analysis,
                'price_prediction': price_prediction,
                'risk_assessment': risk_assessment,
                'trading_signals': self._generate_trading_signals(
                    technical_analysis, whale_analysis, sentiment_analysis, risk_assessment
                )
            }
            
            self.logger.info(f"Análise completa para {symbol} finalizada")
            return comprehensive_analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise de mercado: {e}")
            return {'error': str(e)}
    
    def _extract_price_data(self, symbol_data: Dict) -> Optional[pd.DataFrame]:
        """Extrai e formata dados de preços para análise"""
        try:
            chart_data = symbol_data.get('chart', {})
            prices = chart_data.get('prices', [])
            
            if not prices:
                return None
            
            # Converter para DataFrame
            df = pd.DataFrame(prices)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            
            # Remover valores nulos
            df = df.dropna()
            
            if len(df) < 10:  # Mínimo de dados necessários
                return None
            
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados de preços: {e}")
            return None
    
    def _perform_technical_analysis(self, df: pd.DataFrame) -> Dict:
        """Realiza análise técnica usando TA-Lib"""
        try:
            analysis = {}
            
            # Converter para arrays numpy
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            volume = df['volume'].values
            
            # RSI
            rsi = talib.RSI(close, timeperiod=TECHNICAL_ANALYSIS['rsi_period'])
            analysis['rsi'] = {
                'current': float(rsi[-1]) if not np.isnan(rsi[-1]) else None,
                'signal': 'oversold' if rsi[-1] < 30 else 'overbought' if rsi[-1] > 70 else 'neutral'
            }
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(
                close, 
                fastperiod=TECHNICAL_ANALYSIS['macd_fast'],
                slowperiod=TECHNICAL_ANALYSIS['macd_slow'],
                signalperiod=TECHNICAL_ANALYSIS['macd_signal']
            )
            analysis['macd'] = {
                'macd': float(macd[-1]) if not np.isnan(macd[-1]) else None,
                'signal': float(macd_signal[-1]) if not np.isnan(macd_signal[-1]) else None,
                'histogram': float(macd_hist[-1]) if not np.isnan(macd_hist[-1]) else None,
                'trend': 'bullish' if macd[-1] > macd_signal[-1] else 'bearish'
            }
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(
                close,
                timeperiod=TECHNICAL_ANALYSIS['bollinger_period'],
                nbdevup=TECHNICAL_ANALYSIS['bollinger_std'],
                nbdevdn=TECHNICAL_ANALYSIS['bollinger_std']
            )
            current_price = close[-1]
            analysis['bollinger_bands'] = {
                'upper': float(bb_upper[-1]) if not np.isnan(bb_upper[-1]) else None,
                'middle': float(bb_middle[-1]) if not np.isnan(bb_middle[-1]) else None,
                'lower': float(bb_lower[-1]) if not np.isnan(bb_lower[-1]) else None,
                'position': 'above_upper' if current_price > bb_upper[-1] else 'below_lower' if current_price < bb_lower[-1] else 'middle'
            }
            
            # Moving Averages
            sma_short = talib.SMA(close, timeperiod=TECHNICAL_ANALYSIS['price_sma_short'])
            sma_long = talib.SMA(close, timeperiod=TECHNICAL_ANALYSIS['price_sma_long'])
            analysis['moving_averages'] = {
                'sma_short': float(sma_short[-1]) if not np.isnan(sma_short[-1]) else None,
                'sma_long': float(sma_long[-1]) if not np.isnan(sma_long[-1]) else None,
                'trend': 'bullish' if sma_short[-1] > sma_long[-1] else 'bearish'
            }
            
            # Volume Analysis
            volume_sma = talib.SMA(volume.astype(float), timeperiod=TECHNICAL_ANALYSIS['volume_sma'])
            current_volume = volume[-1]
            avg_volume = volume_sma[-1] if not np.isnan(volume_sma[-1]) else volume.mean()
            analysis['volume'] = {
                'current': float(current_volume),
                'average': float(avg_volume),
                'ratio': float(current_volume / avg_volume) if avg_volume > 0 else 0,
                'signal': 'high' if current_volume > avg_volume * 1.5 else 'low' if current_volume < avg_volume * 0.5 else 'normal'
            }
            
            # Support and Resistance
            analysis['support_resistance'] = self._calculate_support_resistance(df)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise técnica: {e}")
            return {}
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Calcula níveis de suporte e resistência"""
        try:
            high_prices = df['high'].values
            low_prices = df['low'].values
            close_prices = df['close'].values
            
            # Calcular níveis básicos
            recent_high = np.max(high_prices[-20:])  # Máxima dos últimos 20 períodos
            recent_low = np.min(low_prices[-20:])    # Mínima dos últimos 20 períodos
            current_price = close_prices[-1]
            
            return {
                'resistance': float(recent_high),
                'support': float(recent_low),
                'current_price': float(current_price),
                'distance_to_resistance': float((recent_high - current_price) / current_price * 100),
                'distance_to_support': float((current_price - recent_low) / current_price * 100)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular suporte/resistência: {e}")
            return {}
    
    def _analyze_whale_data(self, symbol_data: Dict) -> Dict:
        """Analisa dados de whales e instituições"""
        try:
            holders_data = symbol_data.get('holders', {})
            
            if not holders_data:
                return {'status': 'no_data'}
            
            institutional = holders_data.get('institutional', [])
            whale_count = holders_data.get('whale_institutions_count', 0)
            
            # Calcular concentração institucional
            total_institutional_pct = sum([h.get('pct_held', 0) for h in institutional])
            
            # Identificar mudanças recentes (simplificado)
            whale_analysis = {
                'whale_institutions_count': whale_count,
                'total_institutional_percentage': total_institutional_pct,
                'concentration_level': 'high' if total_institutional_pct > 70 else 'medium' if total_institutional_pct > 40 else 'low',
                'whale_signal': 'bullish' if whale_count > 3 else 'neutral',
                'top_whales': institutional[:5]  # Top 5 holders
            }
            
            return whale_analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise de whales: {e}")
            return {}
    
    def _analyze_sentiment_with_fingpt(self, symbol_data: Dict) -> Dict:
        """Análise de sentimento usando FinGPT/OpenAI"""
        try:
            symbol = symbol_data.get('chart', {}).get('symbol', 'UNKNOWN')
            
            # Preparar contexto para análise
            context = self._prepare_market_context(symbol_data)
            
            prompt = f"""
            {FINGPT_CONFIG['sentiment_prompt']}
            
            Market Data for {symbol}:
            {context}
            
            Please analyze the sentiment and provide:
            1. Sentiment score (-1 to 1)
            2. Key factors influencing sentiment
            3. Confidence level (0 to 1)
            
            Respond in JSON format.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=FINGPT_CONFIG['max_tokens'],
                temperature=FINGPT_CONFIG['temperature']
            )
            
            # Processar resposta
            sentiment_text = response.choices[0].message.content
            
            # Tentar extrair JSON da resposta
            try:
                sentiment_data = json.loads(sentiment_text)
            except:
                # Fallback para análise básica
                sentiment_data = {
                    'sentiment_score': 0.0,
                    'key_factors': ['Unable to parse detailed analysis'],
                    'confidence': 0.5,
                    'raw_response': sentiment_text
                }
            
            return sentiment_data
            
        except Exception as e:
            self.logger.error(f"Erro na análise de sentimento: {e}")
            return {'sentiment_score': 0.0, 'confidence': 0.0, 'error': str(e)}
    
    def _predict_price_with_fingpt(self, symbol_data: Dict, technical_analysis: Dict) -> Dict:
        """Previsão de preço usando FinGPT/OpenAI"""
        try:
            symbol = symbol_data.get('chart', {}).get('symbol', 'UNKNOWN')
            current_price = symbol_data.get('chart', {}).get('current_price', 0)
            
            # Preparar contexto técnico
            tech_summary = self._summarize_technical_analysis(technical_analysis)
            
            prompt = f"""
            {FINGPT_CONFIG['prediction_prompt']}
            
            Symbol: {symbol}
            Current Price: ${current_price}
            
            Technical Analysis Summary:
            {tech_summary}
            
            Provide a price prediction with:
            1. Target price for next 24 hours
            2. Probability of upward movement (0-1)
            3. Key technical factors
            4. Confidence level (0-1)
            
            Respond in JSON format.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=FINGPT_CONFIG['max_tokens'],
                temperature=FINGPT_CONFIG['temperature']
            )
            
            prediction_text = response.choices[0].message.content
            
            try:
                prediction_data = json.loads(prediction_text)
            except:
                # Fallback baseado em análise técnica
                prediction_data = {
                    'target_price': current_price * 1.01,  # 1% conservador
                    'upward_probability': 0.5,
                    'key_factors': ['Technical analysis fallback'],
                    'confidence': 0.3,
                    'raw_response': prediction_text
                }
            
            return prediction_data
            
        except Exception as e:
            self.logger.error(f"Erro na previsão de preço: {e}")
            return {'target_price': 0, 'confidence': 0.0, 'error': str(e)}
    
    def _assess_risk_with_fingpt(self, symbol_data: Dict, technical_analysis: Dict) -> Dict:
        """Avaliação de risco usando FinGPT/OpenAI"""
        try:
            symbol = symbol_data.get('chart', {}).get('symbol', 'UNKNOWN')
            
            # Preparar contexto de risco
            risk_context = self._prepare_risk_context(symbol_data, technical_analysis)
            
            prompt = f"""
            {FINGPT_CONFIG['risk_prompt']}
            
            Symbol: {symbol}
            Risk Context:
            {risk_context}
            
            Assess the risk and provide:
            1. Risk score (1-10, where 10 is highest risk)
            2. Main risk factors
            3. Recommended position size (% of portfolio)
            4. Stop loss suggestion (% below current price)
            
            Respond in JSON format.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=FINGPT_CONFIG['max_tokens'],
                temperature=FINGPT_CONFIG['temperature']
            )
            
            risk_text = response.choices[0].message.content
            
            try:
                risk_data = json.loads(risk_text)
            except:
                # Fallback conservador
                risk_data = {
                    'risk_score': 7,  # Conservador
                    'main_risk_factors': ['Unable to parse detailed risk analysis'],
                    'recommended_position_size': 2.0,  # 2% conservador
                    'stop_loss_suggestion': 3.0,  # 3% stop loss
                    'raw_response': risk_text
                }
            
            return risk_data
            
        except Exception as e:
            self.logger.error(f"Erro na avaliação de risco: {e}")
            return {'risk_score': 8, 'recommended_position_size': 1.0, 'error': str(e)}
    
    def _prepare_market_context(self, symbol_data: Dict) -> str:
        """Prepara contexto de mercado para análise"""
        try:
            chart_data = symbol_data.get('chart', {})
            current_price = chart_data.get('current_price', 0)
            volume_spike = chart_data.get('volume_spike', 0)
            
            context = f"""
            Current Price: ${current_price}
            Volume Spike: {volume_spike:.2f}x normal
            Exchange: {chart_data.get('exchange', 'Unknown')}
            Market Cap: ${chart_data.get('market_cap', 0):,}
            """
            
            return context
            
        except Exception as e:
            return f"Error preparing context: {e}"
    
    def _summarize_technical_analysis(self, technical_analysis: Dict) -> str:
        """Resume análise técnica para o prompt"""
        try:
            summary = []
            
            # RSI
            rsi_data = technical_analysis.get('rsi', {})
            if rsi_data:
                summary.append(f"RSI: {rsi_data.get('current', 'N/A')} ({rsi_data.get('signal', 'neutral')})")
            
            # MACD
            macd_data = technical_analysis.get('macd', {})
            if macd_data:
                summary.append(f"MACD: {macd_data.get('trend', 'neutral')} trend")
            
            # Moving Averages
            ma_data = technical_analysis.get('moving_averages', {})
            if ma_data:
                summary.append(f"MA Trend: {ma_data.get('trend', 'neutral')}")
            
            # Volume
            volume_data = technical_analysis.get('volume', {})
            if volume_data:
                summary.append(f"Volume: {volume_data.get('signal', 'normal')}")
            
            return " | ".join(summary)
            
        except Exception as e:
            return f"Error summarizing technical analysis: {e}"
    
    def _prepare_risk_context(self, symbol_data: Dict, technical_analysis: Dict) -> str:
        """Prepara contexto de risco"""
        try:
            context = []
            
            # Volatilidade baseada em Bollinger Bands
            bb_data = technical_analysis.get('bollinger_bands', {})
            if bb_data:
                context.append(f"BB Position: {bb_data.get('position', 'unknown')}")
            
            # Volume
            volume_data = technical_analysis.get('volume', {})
            if volume_data:
                context.append(f"Volume Ratio: {volume_data.get('ratio', 1):.2f}")
            
            # Whale presence
            whale_data = symbol_data.get('holders', {})
            if whale_data:
                whale_count = whale_data.get('whale_institutions_count', 0)
                context.append(f"Whale Institutions: {whale_count}")
            
            return " | ".join(context)
            
        except Exception as e:
            return f"Error preparing risk context: {e}"
    
    def _generate_trading_signals(self, technical_analysis: Dict, whale_analysis: Dict, 
                                sentiment_analysis: Dict, risk_assessment: Dict) -> Dict:
        """Gera sinais de trading combinando todas as análises"""
        try:
            signals = {
                'overall_signal': 'HOLD',
                'confidence': 0.0,
                'entry_price': None,
                'stop_loss': None,
                'take_profit': None,
                'position_size': 0.0,
                'reasoning': []
            }
            
            score = 0
            max_score = 0
            reasoning = []
            
            # Análise técnica (peso: 40%)
            if technical_analysis:
                tech_score = 0
                
                # RSI
                rsi_data = technical_analysis.get('rsi', {})
                if rsi_data.get('signal') == 'oversold':
                    tech_score += 2
                    reasoning.append("RSI oversold (bullish)")
                elif rsi_data.get('signal') == 'overbought':
                    tech_score -= 2
                    reasoning.append("RSI overbought (bearish)")
                
                # MACD
                macd_data = technical_analysis.get('macd', {})
                if macd_data.get('trend') == 'bullish':
                    tech_score += 1
                    reasoning.append("MACD bullish")
                elif macd_data.get('trend') == 'bearish':
                    tech_score -= 1
                    reasoning.append("MACD bearish")
                
                # Moving Averages
                ma_data = technical_analysis.get('moving_averages', {})
                if ma_data.get('trend') == 'bullish':
                    tech_score += 1
                    reasoning.append("MA trend bullish")
                elif ma_data.get('trend') == 'bearish':
                    tech_score -= 1
                    reasoning.append("MA trend bearish")
                
                score += tech_score * 0.4
                max_score += 4 * 0.4
            
            # Análise de whales (peso: 30%)
            if whale_analysis:
                whale_score = 0
                
                whale_signal = whale_analysis.get('whale_signal', 'neutral')
                if whale_signal == 'bullish':
                    whale_score += 2
                    reasoning.append("Strong whale presence")
                
                concentration = whale_analysis.get('concentration_level', 'low')
                if concentration == 'high':
                    whale_score += 1
                    reasoning.append("High institutional concentration")
                
                score += whale_score * 0.3
                max_score += 3 * 0.3
            
            # Análise de sentimento (peso: 20%)
            if sentiment_analysis:
                sentiment_score = sentiment_analysis.get('sentiment_score', 0)
                confidence = sentiment_analysis.get('confidence', 0)
                
                if sentiment_score > 0.3 and confidence > 0.6:
                    score += 2 * 0.2
                    reasoning.append("Positive sentiment")
                elif sentiment_score < -0.3 and confidence > 0.6:
                    score -= 2 * 0.2
                    reasoning.append("Negative sentiment")
                
                max_score += 2 * 0.2
            
            # Avaliação de risco (peso: 10%)
            if risk_assessment:
                risk_score = risk_assessment.get('risk_score', 5)
                
                if risk_score <= 3:
                    score += 1 * 0.1
                    reasoning.append("Low risk")
                elif risk_score >= 8:
                    score -= 1 * 0.1
                    reasoning.append("High risk")
                
                max_score += 1 * 0.1
            
            # Calcular sinal final
            if max_score > 0:
                confidence = abs(score) / max_score
                
                if score > 0.6:
                    signals['overall_signal'] = 'BUY'
                elif score < -0.6:
                    signals['overall_signal'] = 'SELL'
                else:
                    signals['overall_signal'] = 'HOLD'
                
                signals['confidence'] = confidence
                signals['reasoning'] = reasoning
                
                # Calcular position size baseado no risco
                base_position = RISK_MANAGEMENT['max_position_size']
                risk_multiplier = 1.0 - (risk_assessment.get('risk_score', 5) / 10)
                signals['position_size'] = base_position * risk_multiplier * confidence
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar sinais de trading: {e}")
            return {'overall_signal': 'HOLD', 'confidence': 0.0, 'error': str(e)}
    
    def save_analysis(self, analysis: Dict, filename: str = None):
        """Salva análise em arquivo JSON"""
        try:
            if filename is None:
                symbol = analysis.get('symbol', 'UNKNOWN')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"analysis_{symbol}_{timestamp}.json"
            
            filepath = get_data_path(filename)
            
            with open(filepath, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            
            self.logger.info(f"Análise salva em {filepath}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar análise: {e}")

# ==================== EXEMPLO DE USO ====================
if __name__ == "__main__":
    analyzer = FinGPTAnalyzer()
    
    # Carregar dados de exemplo (do coletor anterior)
    try:
        data_files = [f for f in os.listdir(get_data_path('')) if f.startswith('yahoo_data_')]
        if data_files:
            latest_file = sorted(data_files)[-1]
            with open(get_data_path(latest_file), 'r') as f:
                sample_data = json.load(f)
            
            print("Iniciando análise com FinGPT...")
            
            for symbol, symbol_data in sample_data.items():
                if symbol_data.get('chart'):  # Verificar se tem dados válidos
                    print(f"\nAnalisando {symbol}...")
                    
                    analysis = analyzer.analyze_market_data(symbol_data)
                    
                    if 'error' not in analysis:
                        # Mostrar resultados principais
                        signals = analysis.get('trading_signals', {})
                        print(f"📊 Sinal: {signals.get('overall_signal', 'N/A')}")
                        print(f"🎯 Confiança: {signals.get('confidence', 0):.2f}")
                        print(f"💰 Position Size: {signals.get('position_size', 0):.2f}%")
                        
                        reasoning = signals.get('reasoning', [])
                        if reasoning:
                            print("📝 Reasoning:")
                            for reason in reasoning:
                                print(f"  - {reason}")
                        
                        # Salvar análise
                        analyzer.save_analysis(analysis)
                    else:
                        print(f"❌ Erro na análise: {analysis['error']}")
                    
                    break  # Analisar apenas o primeiro símbolo para teste
        else:
            print("Nenhum dado encontrado. Execute o coletor primeiro.")
            
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")

