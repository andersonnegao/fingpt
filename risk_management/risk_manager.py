"""
Sistema de Gestão de Risco Avançado
Garante que perdas sejam "acidentes" e não a regra
"""

import sys
import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import math

# Importar configurações
sys.path.append('/home/ubuntu/trading_system')
from config.settings import *

@dataclass
class Position:
    """Representa uma posição de trading"""
    symbol: str
    entry_price: float
    quantity: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    position_type: str  # 'long' ou 'short'
    risk_amount: float
    confidence: float
    analysis_data: Dict

@dataclass
class RiskMetrics:
    """Métricas de risco calculadas"""
    position_risk: float
    portfolio_risk: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    risk_reward_ratio: float
    var_95: float  # Value at Risk 95%

class RiskManager:
    """Gerenciador de risco avançado para trading automatizado"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.positions = {}  # Posições ativas
        self.closed_positions = []  # Histórico de posições
        self.portfolio_value = 100000  # Valor inicial do portfolio ($100k)
        self.daily_pnl = []
        self.risk_metrics = None
        
    def _setup_logger(self):
        """Configura o logger para o risk manager"""
        logger = logging.getLogger('RiskManager')
        logger.setLevel(logging.INFO)
        
        # Handler para arquivo
        file_handler = logging.FileHandler(get_log_path('risk_manager.log'))
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
    
    def validate_trade(self, symbol: str, signal: Dict, current_price: float, 
                      analysis_data: Dict) -> Dict:
        """
        Valida se um trade deve ser executado baseado nas regras de risco
        
        Returns:
            Dict com 'approved', 'reason', 'position_size', 'stop_loss', 'take_profit'
        """
        try:
            validation_result = {
                'approved': False,
                'reason': '',
                'position_size': 0.0,
                'stop_loss': 0.0,
                'take_profit': 0.0,
                'risk_amount': 0.0
            }
            
            # 1. Verificar se já temos posição neste símbolo
            if symbol in self.positions:
                validation_result['reason'] = f"Já existe posição ativa em {symbol}"
                return validation_result
            
            # 2. Verificar número máximo de posições
            if len(self.positions) >= RISK_MANAGEMENT['max_open_positions']:
                validation_result['reason'] = f"Máximo de {RISK_MANAGEMENT['max_open_positions']} posições atingido"
                return validation_result
            
            # 3. Verificar perda diária máxima
            if self._check_daily_loss_limit():
                validation_result['reason'] = "Limite de perda diária atingido"
                return validation_result
            
            # 4. Calcular position size baseado no risco
            position_size = self._calculate_position_size(
                current_price, signal, analysis_data
            )
            
            if position_size <= 0:
                validation_result['reason'] = "Position size calculado é zero ou negativo"
                return validation_result
            
            # 5. Calcular stop loss e take profit
            stop_loss, take_profit = self._calculate_stop_take_levels(
                current_price, signal, analysis_data
            )
            
            # 6. Verificar risk/reward ratio
            risk_reward = self._calculate_risk_reward_ratio(
                current_price, stop_loss, take_profit, signal.get('overall_signal', 'HOLD')
            )
            
            if risk_reward < 1.5:  # Mínimo 1.5:1
                validation_result['reason'] = f"Risk/reward ratio muito baixo: {risk_reward:.2f}"
                return validation_result
            
            # 7. Verificar volume mínimo
            volume_data = analysis_data.get('technical_analysis', {}).get('volume', {})
            current_volume = volume_data.get('current', 0)
            
            if current_volume < RISK_MANAGEMENT['min_volume']:
                validation_result['reason'] = f"Volume insuficiente: {current_volume:,}"
                return validation_result
            
            # 8. Verificar confiança mínima
            confidence = signal.get('confidence', 0)
            if confidence < 0.6:  # Mínimo 60% de confiança
                validation_result['reason'] = f"Confiança muito baixa: {confidence:.2f}"
                return validation_result
            
            # 9. Calcular valor em risco
            risk_amount = abs(current_price - stop_loss) * position_size
            max_risk = self.portfolio_value * RISK_MANAGEMENT['max_position_size']
            
            if risk_amount > max_risk:
                validation_result['reason'] = f"Risco muito alto: ${risk_amount:.2f} > ${max_risk:.2f}"
                return validation_result
            
            # Trade aprovado!
            validation_result.update({
                'approved': True,
                'reason': 'Trade aprovado por todas as validações de risco',
                'position_size': position_size,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_amount': risk_amount,
                'risk_reward_ratio': risk_reward,
                'confidence': confidence
            })
            
            self.logger.info(f"Trade aprovado para {symbol}: Size={position_size:.2f}, R/R={risk_reward:.2f}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Erro na validação de trade: {e}")
            return {
                'approved': False,
                'reason': f'Erro na validação: {e}',
                'position_size': 0.0,
                'stop_loss': 0.0,
                'take_profit': 0.0,
                'risk_amount': 0.0
            }
    
    def _calculate_position_size(self, current_price: float, signal: Dict, 
                               analysis_data: Dict) -> float:
        """Calcula o tamanho da posição baseado no risco"""
        try:
            # Position size baseado na confiança e risco
            base_size = RISK_MANAGEMENT['max_position_size']
            confidence = signal.get('confidence', 0.5)
            
            # Ajustar baseado no risco da análise
            risk_assessment = analysis_data.get('risk_assessment', {})
            risk_score = risk_assessment.get('risk_score', 5)
            
            # Reduzir position size para ativos mais arriscados
            risk_multiplier = 1.0 - (risk_score / 10) * 0.5  # Máximo 50% de redução
            
            # Ajustar baseado na confiança
            confidence_multiplier = confidence
            
            # Calcular position size final
            position_size_pct = base_size * risk_multiplier * confidence_multiplier
            
            # Converter para quantidade de ações/contratos
            max_investment = self.portfolio_value * position_size_pct
            position_size = max_investment / current_price
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular position size: {e}")
            return 0.0
    
    def _calculate_stop_take_levels(self, current_price: float, signal: Dict, 
                                  analysis_data: Dict) -> Tuple[float, float]:
        """Calcula níveis de stop loss e take profit"""
        try:
            signal_type = signal.get('overall_signal', 'HOLD')
            
            # Stop loss baseado na configuração e análise técnica
            base_stop_pct = RISK_MANAGEMENT['stop_loss_pct']
            base_take_pct = RISK_MANAGEMENT['take_profit_pct']
            
            # Ajustar baseado na volatilidade (Bollinger Bands)
            technical_analysis = analysis_data.get('technical_analysis', {})
            bb_data = technical_analysis.get('bollinger_bands', {})
            
            if bb_data:
                upper = bb_data.get('upper', current_price * 1.02)
                lower = bb_data.get('lower', current_price * 0.98)
                volatility = (upper - lower) / current_price
                
                # Ajustar stops baseado na volatilidade
                volatility_multiplier = max(0.5, min(2.0, volatility / 0.04))  # Normalizar para 4% volatilidade base
                stop_pct = base_stop_pct * volatility_multiplier
                take_pct = base_take_pct * volatility_multiplier
            else:
                stop_pct = base_stop_pct
                take_pct = base_take_pct
            
            # Calcular níveis baseado no tipo de sinal
            if signal_type == 'BUY':
                stop_loss = current_price * (1 - stop_pct)
                take_profit = current_price * (1 + take_pct)
            elif signal_type == 'SELL':
                stop_loss = current_price * (1 + stop_pct)
                take_profit = current_price * (1 - take_pct)
            else:
                # HOLD - não deveria chegar aqui
                stop_loss = current_price * 0.97
                take_profit = current_price * 1.03
            
            # Verificar se os níveis fazem sentido com suporte/resistência
            sr_data = technical_analysis.get('support_resistance', {})
            if sr_data:
                support = sr_data.get('support', 0)
                resistance = sr_data.get('resistance', 0)
                
                if signal_type == 'BUY' and support > 0:
                    # Ajustar stop loss para logo abaixo do suporte
                    suggested_stop = support * 0.995
                    if suggested_stop > stop_loss:
                        stop_loss = suggested_stop
                
                if signal_type == 'BUY' and resistance > 0:
                    # Ajustar take profit para logo abaixo da resistência
                    suggested_take = resistance * 0.995
                    if suggested_take < take_profit and suggested_take > current_price:
                        take_profit = suggested_take
            
            return stop_loss, take_profit
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular stop/take levels: {e}")
            return current_price * 0.97, current_price * 1.03
    
    def _calculate_risk_reward_ratio(self, current_price: float, stop_loss: float, 
                                   take_profit: float, signal_type: str) -> float:
        """Calcula o ratio risco/recompensa"""
        try:
            if signal_type == 'BUY':
                risk = current_price - stop_loss
                reward = take_profit - current_price
            elif signal_type == 'SELL':
                risk = stop_loss - current_price
                reward = current_price - take_profit
            else:
                return 0.0
            
            if risk <= 0:
                return 0.0
            
            return reward / risk
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular risk/reward ratio: {e}")
            return 0.0
    
    def _check_daily_loss_limit(self) -> bool:
        """Verifica se o limite de perda diária foi atingido"""
        try:
            today = datetime.now().date()
            today_pnl = sum([pnl for date, pnl in self.daily_pnl if date == today])
            
            max_daily_loss = self.portfolio_value * RISK_MANAGEMENT['max_daily_loss']
            
            return today_pnl < -max_daily_loss
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar limite de perda diária: {e}")
            return False
    
    def open_position(self, symbol: str, validation_result: Dict, 
                     current_price: float, analysis_data: Dict) -> bool:
        """Abre uma nova posição"""
        try:
            signal = analysis_data.get('trading_signals', {})
            signal_type = signal.get('overall_signal', 'HOLD')
            
            position = Position(
                symbol=symbol,
                entry_price=current_price,
                quantity=validation_result['position_size'],
                entry_time=datetime.now(),
                stop_loss=validation_result['stop_loss'],
                take_profit=validation_result['take_profit'],
                position_type='long' if signal_type == 'BUY' else 'short',
                risk_amount=validation_result['risk_amount'],
                confidence=validation_result['confidence'],
                analysis_data=analysis_data
            )
            
            self.positions[symbol] = position
            
            self.logger.info(f"Posição aberta: {symbol} {position.position_type} "
                           f"@ ${current_price:.2f}, Size: {position.quantity:.2f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao abrir posição: {e}")
            return False
    
    def update_positions(self, market_data: Dict):
        """Atualiza todas as posições com dados de mercado atuais"""
        try:
            positions_to_close = []
            
            for symbol, position in self.positions.items():
                if symbol in market_data:
                    current_price = market_data[symbol].get('chart', {}).get('current_price', 0)
                    
                    if current_price > 0:
                        # Verificar stop loss e take profit
                        should_close, reason = self._check_exit_conditions(position, current_price)
                        
                        if should_close:
                            positions_to_close.append((symbol, reason, current_price))
            
            # Fechar posições que atingiram condições de saída
            for symbol, reason, exit_price in positions_to_close:
                self.close_position(symbol, exit_price, reason)
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar posições: {e}")
    
    def _check_exit_conditions(self, position: Position, current_price: float) -> Tuple[bool, str]:
        """Verifica se uma posição deve ser fechada"""
        try:
            if position.position_type == 'long':
                # Long position
                if current_price <= position.stop_loss:
                    return True, "Stop loss atingido"
                elif current_price >= position.take_profit:
                    return True, "Take profit atingido"
            else:
                # Short position
                if current_price >= position.stop_loss:
                    return True, "Stop loss atingido"
                elif current_price <= position.take_profit:
                    return True, "Take profit atingido"
            
            # Verificar tempo máximo de posição (ex: 7 dias)
            days_open = (datetime.now() - position.entry_time).days
            if days_open > 7:
                return True, "Tempo máximo de posição atingido"
            
            return False, ""
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar condições de saída: {e}")
            return False, "Erro na verificação"
    
    def close_position(self, symbol: str, exit_price: float, reason: str) -> Dict:
        """Fecha uma posição e calcula P&L"""
        try:
            if symbol not in self.positions:
                return {'error': f'Posição {symbol} não encontrada'}
            
            position = self.positions[symbol]
            
            # Calcular P&L
            if position.position_type == 'long':
                pnl = (exit_price - position.entry_price) * position.quantity
            else:
                pnl = (position.entry_price - exit_price) * position.quantity
            
            pnl_pct = pnl / (position.entry_price * position.quantity) * 100
            
            # Atualizar portfolio
            self.portfolio_value += pnl
            
            # Registrar P&L diário
            today = datetime.now().date()
            self.daily_pnl.append((today, pnl))
            
            # Mover para histórico
            position_result = {
                'symbol': symbol,
                'entry_price': position.entry_price,
                'exit_price': exit_price,
                'quantity': position.quantity,
                'position_type': position.position_type,
                'entry_time': position.entry_time,
                'exit_time': datetime.now(),
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'reason': reason,
                'confidence': position.confidence
            }
            
            self.closed_positions.append(position_result)
            del self.positions[symbol]
            
            self.logger.info(f"Posição fechada: {symbol} - P&L: ${pnl:.2f} ({pnl_pct:.2f}%) - {reason}")
            
            return position_result
            
        except Exception as e:
            self.logger.error(f"Erro ao fechar posição: {e}")
            return {'error': str(e)}
    
    def calculate_risk_metrics(self) -> RiskMetrics:
        """Calcula métricas de risco do portfolio"""
        try:
            if not self.closed_positions:
                return RiskMetrics(0, 0, 0, 0, 0, 0, 0)
            
            # Extrair dados das posições fechadas
            pnls = [pos['pnl'] for pos in self.closed_positions]
            pnl_pcts = [pos['pnl_pct'] for pos in self.closed_positions]
            
            # Win rate
            wins = len([pnl for pnl in pnls if pnl > 0])
            total_trades = len(pnls)
            win_rate = wins / total_trades if total_trades > 0 else 0
            
            # Average win/loss
            winning_trades = [pnl for pnl in pnls if pnl > 0]
            losing_trades = [pnl for pnl in pnls if pnl < 0]
            
            avg_win = np.mean(winning_trades) if winning_trades else 0
            avg_loss = abs(np.mean(losing_trades)) if losing_trades else 0
            
            # Risk/Reward ratio
            risk_reward_ratio = avg_win / avg_loss if avg_loss > 0 else 0
            
            # Sharpe ratio (simplificado)
            if len(pnl_pcts) > 1:
                returns_std = np.std(pnl_pcts)
                avg_return = np.mean(pnl_pcts)
                sharpe_ratio = avg_return / returns_std if returns_std > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Maximum Drawdown
            cumulative_returns = np.cumsum(pnls)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = cumulative_returns - running_max
            max_drawdown = abs(np.min(drawdowns)) if len(drawdowns) > 0 else 0
            
            # Value at Risk (95%)
            var_95 = np.percentile(pnls, 5) if len(pnls) > 0 else 0
            
            # Portfolio risk (posições ativas)
            portfolio_risk = sum([pos.risk_amount for pos in self.positions.values()])
            portfolio_risk_pct = portfolio_risk / self.portfolio_value * 100
            
            self.risk_metrics = RiskMetrics(
                position_risk=portfolio_risk_pct,
                portfolio_risk=portfolio_risk_pct,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                win_rate=win_rate * 100,
                risk_reward_ratio=risk_reward_ratio,
                var_95=var_95
            )
            
            return self.risk_metrics
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular métricas de risco: {e}")
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0)
    
    def get_portfolio_summary(self) -> Dict:
        """Retorna resumo do portfolio"""
        try:
            metrics = self.calculate_risk_metrics()
            
            # P&L total
            total_pnl = sum([pos['pnl'] for pos in self.closed_positions])
            total_pnl_pct = total_pnl / 100000 * 100  # Baseado no valor inicial
            
            # Posições ativas
            active_positions_value = sum([
                pos.entry_price * pos.quantity for pos in self.positions.values()
            ])
            
            summary = {
                'portfolio_value': self.portfolio_value,
                'initial_value': 100000,
                'total_pnl': total_pnl,
                'total_pnl_pct': total_pnl_pct,
                'active_positions': len(self.positions),
                'active_positions_value': active_positions_value,
                'closed_trades': len(self.closed_positions),
                'win_rate': metrics.win_rate,
                'sharpe_ratio': metrics.sharpe_ratio,
                'max_drawdown': metrics.max_drawdown,
                'risk_reward_ratio': metrics.risk_reward_ratio,
                'var_95': metrics.var_95,
                'portfolio_risk_pct': metrics.portfolio_risk
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar resumo do portfolio: {e}")
            return {}
    
    def save_state(self, filename: str = None):
        """Salva estado do risk manager"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"risk_manager_state_{timestamp}.json"
            
            state = {
                'portfolio_value': self.portfolio_value,
                'positions': {symbol: {
                    'symbol': pos.symbol,
                    'entry_price': pos.entry_price,
                    'quantity': pos.quantity,
                    'entry_time': pos.entry_time.isoformat(),
                    'stop_loss': pos.stop_loss,
                    'take_profit': pos.take_profit,
                    'position_type': pos.position_type,
                    'risk_amount': pos.risk_amount,
                    'confidence': pos.confidence
                } for symbol, pos in self.positions.items()},
                'closed_positions': self.closed_positions,
                'daily_pnl': [(date.isoformat(), pnl) for date, pnl in self.daily_pnl],
                'portfolio_summary': self.get_portfolio_summary()
            }
            
            filepath = get_data_path(filename)
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            
            self.logger.info(f"Estado do risk manager salvo em {filepath}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar estado: {e}")

# ==================== EXEMPLO DE USO ====================
if __name__ == "__main__":
    risk_manager = RiskManager()
    
    print("Sistema de Gestão de Risco Inicializado")
    print(f"Portfolio inicial: ${risk_manager.portfolio_value:,.2f}")
    
    # Simular validação de trade
    sample_signal = {
        'overall_signal': 'BUY',
        'confidence': 0.75,
        'reasoning': ['RSI oversold', 'MACD bullish', 'Strong whale presence']
    }
    
    sample_analysis = {
        'technical_analysis': {
            'rsi': {'current': 25, 'signal': 'oversold'},
            'volume': {'current': 2000000},
            'bollinger_bands': {'upper': 155, 'lower': 145},
            'support_resistance': {'support': 148, 'resistance': 158}
        },
        'risk_assessment': {'risk_score': 4},
        'trading_signals': sample_signal
    }
    
    # Testar validação
    validation = risk_manager.validate_trade(
        symbol='AAPL',
        signal=sample_signal,
        current_price=150.0,
        analysis_data=sample_analysis
    )
    
    print(f"\nValidação de Trade para AAPL:")
    print(f"Aprovado: {validation['approved']}")
    print(f"Razão: {validation['reason']}")
    
    if validation['approved']:
        print(f"Position Size: {validation['position_size']:.2f}")
        print(f"Stop Loss: ${validation['stop_loss']:.2f}")
        print(f"Take Profit: ${validation['take_profit']:.2f}")
        print(f"Risk/Reward: {validation['risk_reward_ratio']:.2f}")
        
        # Abrir posição
        success = risk_manager.open_position('AAPL', validation, 150.0, sample_analysis)
        if success:
            print("Posição aberta com sucesso!")
    
    # Mostrar resumo do portfolio
    summary = risk_manager.get_portfolio_summary()
    print(f"\nResumo do Portfolio:")
    print(f"Valor atual: ${summary['portfolio_value']:,.2f}")
    print(f"Posições ativas: {summary['active_positions']}")
    print(f"Trades fechados: {summary['closed_trades']}")
    
    # Salvar estado
    risk_manager.save_state()
    print("Estado salvo com sucesso!")

