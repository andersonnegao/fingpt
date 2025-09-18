# ⚡ GUIA DE INÍCIO RÁPIDO - 5 MINUTOS

## 🎯 INSTALAÇÃO EXPRESS

### **Windows:**
1. Baixar e extrair o sistema
2. Duplo-clique em `install.bat`
3. Seguir instruções na tela

### **Mac/Linux:**
```bash
# Dar permissão e executar
chmod +x install.sh
./install.sh
```

---

## 🚀 PRIMEIRA EXECUÇÃO

### **1. Configurar (OBRIGATÓRIO)**
Editar `config/settings.py`:
```python
# Seus símbolos (máximo 5 para começar)
STOCK_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

# Valor inicial (simulação)
INITIAL_PORTFOLIO_VALUE = 100000  # $100k
```

### **2. Iniciar Sistema**
```bash
# Terminal 1 - Sistema principal
python main_trading_system.py

# Terminal 2 - Dashboard
cd trading-dashboard
npm run dev
```

### **3. Acessar Dashboard**
Abrir navegador: `http://localhost:5173`

---

## 📊 O QUE VOCÊ VERÁ

### **PRIMEIRA TELA:**
- ✅ Portfolio: $100,000 (inicial)
- ✅ Posições: 0 (começando)
- ✅ Status: Sistema Ativo
- ✅ Última atualização: tempo real

### **PRIMEIROS 10 MINUTOS:**
- 📊 Coleta de dados iniciada
- 🧠 Análise dos símbolos
- 🐋 Detecção de whale movements
- 📈 Primeiros sinais gerados

### **PRIMEIRA HORA:**
- 🎯 Possíveis trades identificados
- 🛡️ Validação de risco aplicada
- 📱 Alertas de movimentos grandes
- 📊 Métricas de performance atualizadas

---

## ⚠️ CHECKLIST DE SEGURANÇA

### **ANTES DE COMEÇAR:**
- [ ] Sistema rodando em modo SIMULAÇÃO
- [ ] Configurações de risco definidas
- [ ] Símbolos escolhidos (máximo 5)
- [ ] Dashboard acessível
- [ ] Logs sendo gerados

### **PRIMEIRAS 24 HORAS:**
- [ ] Monitorar alertas de whale
- [ ] Verificar sinais gerados
- [ ] Confirmar gestão de risco ativa
- [ ] Acompanhar performance
- [ ] Ler logs para entender funcionamento

### **PRIMEIRA SEMANA:**
- [ ] Analisar win rate
- [ ] Verificar drawdown máximo
- [ ] Ajustar configurações se necessário
- [ ] Entender padrões dos whales
- [ ] Decidir sobre capital real

---

## 🎛️ CONTROLES PRINCIPAIS

### **NO DASHBOARD:**
- **▶️ Iniciar/⏸️ Pausar** - Controla o sistema
- **🔄 Atualizar** - Força atualização de dados
- **📊 Abas** - Navegar entre seções
- **🐋 Whale Alerts** - Movimentos importantes

### **NO TERMINAL:**
- **Ctrl+C** - Para o sistema
- **Logs em tempo real** - Acompanhar atividade
- **Status updates** - Confirmações de ações

---

## 🚨 PROBLEMAS COMUNS

### **Sistema não inicia:**
```bash
# Verificar dependências
pip list | grep yfinance
npm --version

# Reinstalar se necessário
pip install -r requirements.txt
```

### **Dashboard não carrega:**
```bash
# Limpar e reinstalar
cd trading-dashboard
rm -rf node_modules
npm install
npm run dev
```

### **Sem dados:**
- Verificar conexão com internet
- Aguardar 5-10 minutos para primeira coleta
- Verificar logs: `tail -f logs/trading_system.log`

---

## 📈 PRIMEIROS RESULTADOS

### **O QUE ESPERAR:**
- **Sinais por dia:** 2-5 (dependendo do mercado)
- **Win rate inicial:** 60-70%
- **Drawdown máximo:** < 3%
- **Whale alerts:** 1-3 por dia

### **MÉTRICAS IMPORTANTES:**
- **Sharpe Ratio:** > 1.5 (bom)
- **Max Drawdown:** < 5% (seguro)
- **Risk/Reward:** > 1.5:1 (mínimo)
- **Portfolio Risk:** < 15% (controlado)

---

## 🎯 PRÓXIMOS PASSOS

### **APÓS 1 SEMANA:**
1. Analisar performance
2. Ajustar configurações
3. Adicionar mais símbolos
4. Considerar capital real

### **APÓS 1 MÊS:**
1. Otimizar parâmetros
2. Personalizar estratégias
3. Integrar com broker
4. Escalar operação

---

## 🆘 SUPORTE RÁPIDO

### **LOGS IMPORTANTES:**
- `logs/trading_system.log` - Atividade geral
- `logs/risk_manager.log` - Gestão de risco
- `data/system_state.json` - Estado atual

### **COMANDOS ÚTEIS:**
```bash
# Ver logs em tempo real
tail -f logs/trading_system.log

# Verificar estado do sistema
cat data/system_state.json

# Reiniciar limpo
rm -rf data/* logs/*
```

---

## 🎉 PARABÉNS!

Seu sistema está rodando! Agora é só:

1. ✅ **Monitorar** - Acompanhar pelo dashboard
2. ✅ **Aprender** - Entender os padrões
3. ✅ **Ajustar** - Otimizar configurações
4. ✅ **Escalar** - Aumentar capital gradualmente

**Bem-vindo ao mundo do copy trading profissional! 🚀📈**

