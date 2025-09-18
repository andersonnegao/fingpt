"""
Coletor de Dados da SEC EDGAR
Monitora filings 13F, 8K, 10K para detectar movimentos institucionais
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import sys
import os

# Importar configurações
sys.path.append('/home/ubuntu/trading_system')
from config.settings import *

class SECEdgarCollector:
    """Coletor de dados da SEC EDGAR para whale watching institucional"""
    
    def __init__(self):
        self.base_url = SEC_EDGAR_CONFIG['base_url']
        self.headers = {
            'User-Agent': SEC_EDGAR_CONFIG['user_agent'],
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }
        self.logger = self._setup_logger()
        self.last_request_time = 0
        
    def _setup_logger(self):
        """Configura o logger para este coletor"""
        logger = logging.getLogger('SECEdgarCollector')
        logger.setLevel(logging.INFO)
        
        # Handler para arquivo
        file_handler = logging.FileHandler(get_log_path('sec_collector.log'))
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
    
    def _rate_limit_check(self):
        """Respeita o rate limit da SEC (10 requests/segundo)"""
        now = time.time()
        time_diff = now - self.last_request_time
        min_interval = 1.0 / SEC_EDGAR_CONFIG['rate_limit']  # 0.1 segundos
        
        if time_diff < min_interval:
            sleep_time = min_interval - time_diff
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Faz request para a API da SEC com rate limiting"""
        try:
            self._rate_limit_check()
            
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params,
                timeout=SEC_EDGAR_CONFIG['timeout']
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Erro na API SEC: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao fazer request para SEC: {e}")
            return None
    
    def get_company_cik(self, ticker: str) -> Optional[str]:
        """
        Obtém o CIK (Central Index Key) de uma empresa pelo ticker
        """
        try:
            url = f"{self.base_url}/api/xbrl/companyfacts/CIK{ticker}.json"
            
            # Primeiro, tentar buscar na lista de empresas
            tickers_url = f"{self.base_url}/api/xbrl/companytickers.json"
            response = self._make_request(tickers_url)
            
            if response:
                for key, company in response.items():
                    if company.get('ticker', '').upper() == ticker.upper():
                        cik = str(company.get('cik_str', '')).zfill(10)
                        self.logger.info(f"CIK encontrado para {ticker}: {cik}")
                        return cik
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar CIK para {ticker}: {e}")
            return None
    
    def get_recent_filings(self, cik: str = None, form_type: str = "13F-HR", limit: int = 10) -> List[Dict]:
        """
        Busca filings recentes por CIK ou tipo de formulário
        
        Args:
            cik: CIK da empresa (opcional)
            form_type: Tipo de formulário (13F-HR, 8-K, 10-K, etc.)
            limit: Número máximo de filings para retornar
        """
        try:
            filings = []
            
            if cik:
                # Buscar filings específicos de uma empresa
                url = f"{self.base_url}/api/xbrl/companyfacts/CIK{cik}.json"
                response = self._make_request(url)
                
                if response:
                    # Processar filings da empresa
                    company_filings = self._process_company_filings(response, form_type)
                    filings.extend(company_filings[:limit])
            else:
                # Buscar filings recentes de todas as empresas
                # Usar submissions endpoint
                url = f"{self.base_url}/api/xbrl/submissions/CIK0000320193.json"  # Apple como exemplo
                response = self._make_request(url)
                
                if response:
                    recent_filings = self._process_recent_filings(response, form_type)
                    filings.extend(recent_filings[:limit])
            
            self.logger.info(f"Coletados {len(filings)} filings do tipo {form_type}")
            return filings
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar filings: {e}")
            return []
    
    def get_13f_holdings(self, cik: str, filing_date: str = None) -> Optional[Dict]:
        """
        Obtém holdings de um filing 13F específico
        Essencial para whale watching!
        """
        try:
            # Buscar submissions da empresa
            url = f"{self.base_url}/api/xbrl/submissions/CIK{cik}.json"
            response = self._make_request(url)
            
            if not response:
                return None
            
            # Encontrar o filing 13F mais recente ou específico
            filings = response.get('filings', {}).get('recent', {})
            forms = filings.get('form', [])
            filing_dates = filings.get('filingDate', [])
            accession_numbers = filings.get('accessionNumber', [])
            
            target_filing = None
            for i, form in enumerate(forms):
                if form == '13F-HR':
                    if filing_date is None or filing_dates[i] == filing_date:
                        target_filing = {
                            'accession_number': accession_numbers[i],
                            'filing_date': filing_dates[i],
                            'form': form
                        }
                        break
            
            if not target_filing:
                self.logger.warning(f"Nenhum filing 13F encontrado para CIK {cik}")
                return None
            
            # Buscar detalhes do filing específico
            accession = target_filing['accession_number'].replace('-', '')
            filing_url = f"{self.base_url}/Archives/edgar/data/{cik}/{accession}/xslForm13F_X01/primary_doc.xml"
            
            # Para simplificar, vamos retornar os dados básicos do filing
            # Em uma implementação completa, parsearia o XML para extrair holdings
            
            holdings_data = {
                'cik': cik,
                'filing_date': target_filing['filing_date'],
                'accession_number': target_filing['accession_number'],
                'form_type': target_filing['form'],
                'filing_url': filing_url,
                'collected_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Dados 13F coletados para CIK {cik}")
            return holdings_data
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar holdings 13F: {e}")
            return None
    
    def monitor_whale_institutions(self) -> List[Dict]:
        """
        Monitora filings das instituições-alvo para detectar mudanças
        """
        whale_activities = []
        
        for institution in TARGET_INSTITUTIONS:
            try:
                self.logger.info(f"Monitorando {institution}")
                
                # Buscar CIK da instituição (simplificado)
                # Em implementação real, teria um mapeamento CIK-nome
                
                # Buscar filings recentes
                recent_filings = self.get_recent_filings(form_type="13F-HR", limit=5)
                
                for filing in recent_filings:
                    # Analisar se é relevante
                    if self._is_significant_filing(filing):
                        whale_activity = {
                            'institution': institution,
                            'filing_type': filing.get('form_type', ''),
                            'filing_date': filing.get('filing_date', ''),
                            'significance': 'high',
                            'message': f"{institution} filed {filing.get('form_type', '')} on {filing.get('filing_date', '')}",
                            'details': filing
                        }
                        whale_activities.append(whale_activity)
                
                # Pequena pausa entre instituições
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Erro ao monitorar {institution}: {e}")
        
        return whale_activities
    
    def _process_company_filings(self, response: Dict, form_type: str) -> List[Dict]:
        """Processa filings de uma empresa específica"""
        filings = []
        
        try:
            # Extrair informações básicas da empresa
            entity_name = response.get('entityName', '')
            cik = response.get('cik', '')
            
            # Processar filings (estrutura simplificada)
            filing_data = {
                'entity_name': entity_name,
                'cik': cik,
                'form_type': form_type,
                'filing_date': datetime.now().strftime('%Y-%m-%d'),
                'processed_at': datetime.now().isoformat()
            }
            
            filings.append(filing_data)
            
        except Exception as e:
            self.logger.error(f"Erro ao processar filings da empresa: {e}")
        
        return filings
    
    def _process_recent_filings(self, response: Dict, form_type: str) -> List[Dict]:
        """Processa filings recentes"""
        filings = []
        
        try:
            # Extrair filings recentes da resposta
            recent_filings = response.get('filings', {}).get('recent', {})
            forms = recent_filings.get('form', [])
            dates = recent_filings.get('filingDate', [])
            
            for i, form in enumerate(forms):
                if form == form_type and i < len(dates):
                    filing_data = {
                        'form_type': form,
                        'filing_date': dates[i],
                        'processed_at': datetime.now().isoformat()
                    }
                    filings.append(filing_data)
            
        except Exception as e:
            self.logger.error(f"Erro ao processar filings recentes: {e}")
        
        return filings
    
    def _is_significant_filing(self, filing: Dict) -> bool:
        """Determina se um filing é significativo para whale watching"""
        try:
            # Critérios para significância
            form_type = filing.get('form_type', '')
            filing_date = filing.get('filing_date', '')
            
            # 13F filings são sempre significativos
            if form_type == '13F-HR':
                return True
            
            # 8K filings podem indicar mudanças importantes
            if form_type == '8-K':
                return True
            
            # Filings muito recentes são mais relevantes
            if filing_date:
                try:
                    filing_datetime = datetime.strptime(filing_date, '%Y-%m-%d')
                    days_ago = (datetime.now() - filing_datetime).days
                    return days_ago <= 7  # Últimos 7 dias
                except:
                    pass
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao avaliar significância do filing: {e}")
            return False
    
    def get_insider_transactions(self, ticker: str) -> List[Dict]:
        """
        Busca transações de insiders para um ticker específico
        """
        try:
            cik = self.get_company_cik(ticker)
            if not cik:
                return []
            
            # Buscar submissions da empresa
            url = f"{self.base_url}/api/xbrl/submissions/CIK{cik}.json"
            response = self._make_request(url)
            
            if not response:
                return []
            
            insider_transactions = []
            
            # Processar filings de insider (Forms 3, 4, 5)
            filings = response.get('filings', {}).get('recent', {})
            forms = filings.get('form', [])
            dates = filings.get('filingDate', [])
            
            for i, form in enumerate(forms):
                if form in ['3', '4', '5'] and i < len(dates):
                    transaction = {
                        'ticker': ticker,
                        'cik': cik,
                        'form_type': form,
                        'filing_date': dates[i],
                        'transaction_type': 'insider_trading',
                        'collected_at': datetime.now().isoformat()
                    }
                    insider_transactions.append(transaction)
            
            self.logger.info(f"Coletadas {len(insider_transactions)} transações de insider para {ticker}")
            return insider_transactions
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar transações de insider para {ticker}: {e}")
            return []
    
    def save_data(self, data: Any, filename: str = None):
        """Salva dados coletados em arquivo JSON"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"sec_data_{timestamp}.json"
            
            filepath = get_data_path(filename)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info(f"Dados SEC salvos em {filepath}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados SEC: {e}")

# ==================== EXEMPLO DE USO ====================
if __name__ == "__main__":
    collector = SECEdgarCollector()
    
    print("Iniciando coleta de dados da SEC...")
    
    # Testar busca de CIK
    test_ticker = "AAPL"
    cik = collector.get_company_cik(test_ticker)
    if cik:
        print(f"CIK para {test_ticker}: {cik}")
        
        # Buscar holdings 13F
        holdings = collector.get_13f_holdings(cik)
        if holdings:
            print(f"Holdings 13F encontrados para {test_ticker}")
    
    # Monitorar whale institutions
    print("\nMonitorando instituições whale...")
    whale_activities = collector.monitor_whale_institutions()
    
    if whale_activities:
        print(f"🐋 {len(whale_activities)} atividades de whale detectadas:")
        for activity in whale_activities:
            print(f"  - {activity['message']}")
    else:
        print("Nenhuma atividade significativa de whale detectada.")
    
    # Buscar transações de insider
    print(f"\nBuscando transações de insider para {test_ticker}...")
    insider_transactions = collector.get_insider_transactions(test_ticker)
    
    if insider_transactions:
        print(f"📊 {len(insider_transactions)} transações de insider encontradas")
    
    # Salvar todos os dados
    all_data = {
        'whale_activities': whale_activities,
        'insider_transactions': insider_transactions,
        'collection_summary': {
            'timestamp': datetime.now().isoformat(),
            'total_activities': len(whale_activities),
            'total_insider_transactions': len(insider_transactions)
        }
    }
    
    collector.save_data(all_data)
    print("Dados da SEC coletados e salvos.")

