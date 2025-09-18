"""
Sistema Principal de Trading Automatizado
Integra coleta de dados, análise FinGPT, gestão de risco e execução
"""

import sys
import os
import json
import time
import logging
import schedule
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Importar módulos do sistema
sys.path.append('/home/ubuntu/trading_system')
from config.settings import *
from data_collectors.yahoo_finance_collector import YahooFinanceCollector
from data_collectors.sec_edgar_collector import SECEdgarCollector
from analyzers.fingpt_analyzer import FinGPTAnalyzer
from risk_management.risk_manager import RiskManager

class TradingSystem:
    """Sistema principal de trading automatizado"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.running = False
        
        # Inicializar componentes
        self.yahoo_collector = YahooFinanceCollector()
        self.sec_collector = SECEdgarCollector()
        self.analyzer = FinGPTAnalyzer()
        self.risk_manager = RiskManager()
        
        # Estado do sistema
        self.last_update = None
        self.current_data = {}
        self.active_alerts = []
        self.system_stats = {
            'total_signals': 0,
            'executed_trades': 0,
            'rejected_trades': 0,
            'uptime_start': datetime.now()
        }
        
        self.logger.info("Sistema de Trading inicializado")
    
    def _setup_logger(self):
        """Configura o logger principal do sistema"""
        logger = logging.getLogger('TradingSystem')
        logger.setLevel(logging.INFO)
        
        # Handler para arquivo
        file_handler = logging.FileHandler(get_log_path('trading_system.log'))
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
    
    def start_system(self):
        """Inicia o sistema de trading"""
        try:
            self.logger.info("🚀 Iniciando Sistema de Trading Automatizado")
            self.running = True
            
            # Configurar agendamentos
            self._setup_schedules()
            
            # Executar primeira coleta
            self.logger.info("Executando primeira coleta de dados...")
            self.run_data_collection()
            
            # Iniciar loop principal
            self._run_main_loop()
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar sistema: {e}")
            self.running = False
    
    def stop_system(self):
        """Para o sistema de trading"""
        self.logger.info("🛑 Parando Sistema de Trading")
        self.running = False
        
        # Salvar estado final
        self.save_system_state()
    
    def _setup_schedules(self):
        """Configura os agendamentos do sistema"""
        # Coleta de dados a cada 5 minutos
        schedule.every(DATA_CONFIG['update_frequency']).seconds.do(self.run_data_collection)
        
        # Análise e sinais a cada 10 minutos
        schedule.every(10).minutes.do(self.run_analysis_cycle)
        
        # Monitoramento de risco a cada minuto
        schedule.every(1).minutes.do(self.run_risk_monitoring)
        
        # Backup diário
        schedule.every().day.at("23:59").do(self.daily_backup)
        
        self.logger.info("Agendamentos configurados")
    
    def _run_main_loop(self):
        """Loop principal do sistema"""
        self.logger.info("Iniciando loop principal do sistema")
        
        while self.running:
            try:
                # Executar tarefas agendadas
                schedule.run_pending()
                
                # Atualizar posições ativas
                self.update_active_positions()
                
                # Verificar alertas críticos
                self.check_critical_alerts()
                
                # Pausa antes da próxima iteração
                time.sleep(30)  # 30 segundos
                
            except KeyboardInterrupt:
                self.logger.info("Interrupção do usuário detectada")
                break
            except Exception as e:
                self.logger.error(f"Erro no loop principal: {e}")
                time.sleep(60)  # Pausa maior em caso de erro
        
        self.stop_system()
    
    def run_data_collection(self):
        """Executa ciclo completo de coleta de dados"""
        try:
            self.logger.info("📊 Iniciando coleta de dados")
            
            # Coletar dados do Yahoo Finance
            yahoo_data = self.yahoo_collector.collect_all_symbols(STOCK_SYMBOLS[:5])  # Limitar para teste
            
            # Detectar movimentos de whales
            whale_alerts = []
            for symbol, data in yahoo_data.items():
                alerts = self.yahoo_collector.detect_whale_movements(data)
                whale_alerts.extend(alerts)
            
            # Coletar dados da SEC (menos frequente)
            sec_data = {}
            if datetime.now().minute % 30 == 0:  # A cada 30 minutos
                sec_data = {
                    'whale_activities': self.sec_collector.monitor_whale_institutions(),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Atualizar dados atuais
            self.current_data = {
                'yahoo_data': yahoo_data,
                'sec_data': sec_data,
                'whale_alerts': whale_alerts,
                'collection_time': datetime.now().isoformat()
            }
            
            self.last_update = datetime.now()
            
            # Salvar dados
            self._save_collected_data()
            
            self.logger.info(f"✅ Coleta concluída: {len(yahoo_data)} símbolos, {len(whale_alerts)} alertas")
            
        except Exception as e:
            self.logger.error(f"Erro na coleta de dados: {e}")
    
    def run_analysis_cycle(self):
        """Executa ciclo de análise e geração de sinais"""
        try:
            if not self.current_data.get('yahoo_data'):
                self.logger.warning("Sem dados para análise")
                return
            
            self.logger.info("🧠 Iniciando ciclo de análise")
            
            signals_generated = 0
            
            for symbol, symbol_data in self.current_data['yahoo_data'].items():
                if not symbol_data.get('chart'):
                    continue
                
                try:
                    # Análise completa com FinGPT
                    analysis = self.analyzer.analyze_market_data(symbol_data)
                    
                    if 'error' in analysis:
                        self.logger.warning(f"Erro na análise de {symbol}: {analysis['error']}")
                        continue
                    
                    # Verificar se há sinal de trading
                    trading_signals = analysis.get('trading_signals', {})
                    signal_type = trading_signals.get('overall_signal', 'HOLD')
                    
                    if signal_type in ['BUY', 'SELL']:
                        self.process_trading_signal(symbol, analysis)
                        signals_generated += 1
                    
                    # Salvar análise
                    self.analyzer.save_analysis(analysis)
                    
                except Exception as e:
                    self.logger.error(f"Erro na análise de {symbol}: {e}")
            
            self.system_stats['total_signals'] += signals_generated
            self.logger.info(f"✅ Análise concluída: {signals_generated} sinais gerados")
            
        except Exception as e:
            self.logger.error(f"Erro no ciclo de análise: {e}")
    
    def process_trading_signal(self, symbol: str, analysis: Dict):
        """Processa um sinal de trading"""
        try:
            trading_signals = analysis.get('trading_signals', {})
            current_price = analysis.get('symbol_data', {}).get('chart', {}).get('current_price', 0)
            
            if current_price == 0:
                # Tentar obter preço dos dados atuais
                current_price = self.current_data.get('yahoo_data', {}).get(symbol, {}).get('chart', {}).get('current_price', 0)
            
            if current_price == 0:
                self.logger.warning(f"Preço atual não disponível para {symbol}")
                return
            
            self.logger.info(f"🎯 Processando sinal {trading_signals.get('overall_signal')} para {symbol}")
            
            # Validar trade com risk manager
            validation = self.risk_manager.validate_trade(
                symbol=symbol,
                signal=trading_signals,
                current_price=current_price,
                analysis_data=analysis
            )
            
            if validation['approved']:
                # Executar trade (simulado)
                success = self.execute_trade(symbol, validation, current_price, analysis)
                
                if success:
                    self.system_stats['executed_trades'] += 1
                    self.logger.info(f"✅ Trade executado: {symbol} - {trading_signals.get('overall_signal')}")
                else:
                    self.system_stats['rejected_trades'] += 1
                    self.logger.warning(f"❌ Falha na execução do trade: {symbol}")
            else:
                self.system_stats['rejected_trades'] += 1
                self.logger.info(f"🚫 Trade rejeitado: {symbol} - {validation['reason']}")
            
        except Exception as e:
            self.logger.error(f"Erro ao processar sinal de {symbol}: {e}")
    
    def execute_trade(self, symbol: str, validation: Dict, current_price: float, analysis: Dict) -> bool:
        """Executa um trade (simulado)"""
        try:
            # Em um sistema real, aqui seria feita a conexão com a corretora
            # Por enquanto, apenas simular a execução
            
            success = self.risk_manager.open_position(symbol, validation, current_price, analysis)
            
            if success:
                # Criar alerta de execução
                alert = {
                    'type': 'trade_executed',
                    'symbol': symbol,
                    'signal': analysis.get('trading_signals', {}).get('overall_signal'),
                    'price': current_price,
                    'size': validation['position_size'],
                    'timestamp': datetime.now().isoformat(),
                    'message': f"Trade executado: {symbol} @ ${current_price:.2f}"
                }
                self.active_alerts.append(alert)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro na execução do trade: {e}")
            return False
    
    def run_risk_monitoring(self):
        """Executa monitoramento de risco"""
        try:
            # Atualizar posições com dados atuais
            if self.current_data.get('yahoo_data'):
                self.risk_manager.update_positions(self.current_data['yahoo_data'])
            
            # Calcular métricas de risco
            risk_metrics = self.risk_manager.calculate_risk_metrics()
            
            # Verificar limites críticos
            portfolio_summary = self.risk_manager.get_portfolio_summary()
            
            # Alertas de risco
            if portfolio_summary.get('portfolio_risk_pct', 0) > 15:
                alert = {
                    'type': 'risk_alert',
                    'severity': 'high',
                    'message': f"Risco do portfolio alto: {portfolio_summary.get('portfolio_risk_pct', 0):.1f}%",
                    'timestamp': datetime.now().isoformat()
                }
                self.active_alerts.append(alert)
            
        except Exception as e:
            self.logger.error(f"Erro no monitoramento de risco: {e}")
    
    def update_active_positions(self):
        """Atualiza posições ativas"""
        try:
            if self.current_data.get('yahoo_data'):
                self.risk_manager.update_positions(self.current_data['yahoo_data'])
        except Exception as e:
            self.logger.error(f"Erro ao atualizar posições: {e}")
    
    def check_critical_alerts(self):
        """Verifica alertas críticos"""
        try:
            # Limpar alertas antigos (mais de 1 hora)
            current_time = datetime.now()
            self.active_alerts = [
                alert for alert in self.active_alerts
                if (current_time - datetime.fromisoformat(alert['timestamp'])).seconds < 3600
            ]
            
            # Verificar se há alertas críticos
            critical_alerts = [
                alert for alert in self.active_alerts
                if alert.get('severity') == 'high'
            ]
            
            if critical_alerts:
                self.logger.warning(f"⚠️ {len(critical_alerts)} alertas críticos ativos")
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar alertas: {e}")
    
    def daily_backup(self):
        """Backup diário do sistema"""
        try:
            self.logger.info("💾 Executando backup diário")
            
            # Salvar estado do risk manager
            self.risk_manager.save_state()
            
            # Salvar estado do sistema
            self.save_system_state()
            
            self.logger.info("✅ Backup concluído")
            
        except Exception as e:
            self.logger.error(f"Erro no backup: {e}")
    
    def _save_collected_data(self):
        """Salva dados coletados"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"collected_data_{timestamp}.json"
            filepath = get_data_path(filename)
            
            with open(filepath, 'w') as f:
                json.dump(self.current_data, f, indent=2, default=str)
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados coletados: {e}")
    
    def save_system_state(self):
        """Salva estado completo do sistema"""
        try:
            state = {
                'system_stats': self.system_stats,
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'active_alerts': self.active_alerts,
                'running': self.running,
                'portfolio_summary': self.risk_manager.get_portfolio_summary(),
                'timestamp': datetime.now().isoformat()
            }
            
            filepath = get_data_path('system_state.json')
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            
            self.logger.info("Estado do sistema salvo")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar estado do sistema: {e}")
    
    def get_system_status(self) -> Dict:
        """Retorna status atual do sistema"""
        try:
            uptime = datetime.now() - self.system_stats['uptime_start']
            
            return {
                'running': self.running,
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'uptime_hours': uptime.total_seconds() / 3600,
                'total_signals': self.system_stats['total_signals'],
                'executed_trades': self.system_stats['executed_trades'],
                'rejected_trades': self.system_stats['rejected_trades'],
                'active_alerts': len(self.active_alerts),
                'portfolio_summary': self.risk_manager.get_portfolio_summary(),
                'active_positions': len(self.risk_manager.positions)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter status: {e}")
            return {'error': str(e)}

def main():
    """Função principal"""
    print("🚀 Sistema de Trading Automatizado")
    print("=" * 50)
    
    # Criar e iniciar sistema
    trading_system = TradingSystem()
    
    try:
        # Iniciar sistema
        trading_system.start_system()
    except KeyboardInterrupt:
        print("\n🛑 Interrupção do usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
    finally:
        trading_system.stop_system()
        print("Sistema finalizado.")

if __name__ == "__main__":
    main()

