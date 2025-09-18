import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [systemStatus, setSystemStatus] = useState('running')
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [portfolioData] = useState({
    totalValue: 105420.50,
    totalPnL: 5420.50,
    totalPnLPct: 5.42,
    activePositions: 3,
    winRate: 68.5,
    sharpeRatio: 1.85,
    maxDrawdown: -2.1,
    riskLevel: 'Baixo'
  })

  const [positions] = useState([
    {
      symbol: 'AAPL',
      type: 'LONG',
      entryPrice: 148.50,
      currentPrice: 152.30,
      quantity: 50,
      pnl: 190.00,
      pnlPct: 2.56,
      confidence: 0.78,
      stopLoss: 144.05,
      takeProfit: 156.75
    },
    {
      symbol: 'MSFT',
      type: 'LONG', 
      entryPrice: 335.20,
      currentPrice: 342.10,
      quantity: 20,
      pnl: 138.00,
      pnlPct: 2.06,
      confidence: 0.72,
      stopLoss: 325.14,
      takeProfit: 352.68
    },
    {
      symbol: 'TSLA',
      type: 'LONG',
      entryPrice: 245.80,
      currentPrice: 241.20,
      quantity: 15,
      pnl: -69.00,
      pnlPct: -1.87,
      confidence: 0.65,
      stopLoss: 238.43,
      takeProfit: 258.09
    }
  ])

  const [whaleAlerts] = useState([
    {
      symbol: 'AAPL',
      type: 'volume_spike',
      message: 'Volume spike de 3.2x detectado',
      severity: 'high',
      timestamp: '2025-09-14 17:30:00'
    },
    {
      symbol: 'NVDA',
      type: 'whale_presence',
      message: '4 whales institucionais detectados (12.5% do total)',
      severity: 'high',
      timestamp: '2025-09-14 17:25:00'
    },
    {
      symbol: 'MSFT',
      type: 'institutional_filing',
      message: 'BlackRock aumentou posição em 2.1%',
      severity: 'medium',
      timestamp: '2025-09-14 17:20:00'
    }
  ])

  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdate(new Date())
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const toggleSystem = () => {
    setSystemStatus(prev => prev === 'running' ? 'paused' : 'running')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm dark:bg-slate-900/80 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold">📊</span>
                </div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                  Trading System
                </h1>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                systemStatus === 'running' 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                  : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
              }`}>
                {systemStatus === 'running' ? '🟢 Ativo' : '⏸️ Pausado'}
              </span>
            </div>
            
            <div className="flex items-center space-x-3">
              <span className="text-sm text-slate-600 dark:text-slate-400">
                Última atualização: {lastUpdate.toLocaleTimeString()}
              </span>
              <button 
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  systemStatus === 'running' 
                    ? 'bg-red-600 hover:bg-red-700 text-white' 
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
                onClick={toggleSystem}
              >
                {systemStatus === 'running' ? '⏸️ Pausar' : '▶️ Iniciar'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Portfolio Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg border border-green-200 dark:border-green-800">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-green-700 dark:text-green-300">
                Valor do Portfolio
              </h3>
              <span className="text-green-600">💰</span>
            </div>
            <div className="text-2xl font-bold text-green-900 dark:text-green-100">
              ${portfolioData.totalValue.toLocaleString()}
            </div>
            <p className="text-xs text-green-600 dark:text-green-400 flex items-center mt-1">
              📈 +${portfolioData.totalPnL.toLocaleString()} ({portfolioData.totalPnLPct}%)
            </p>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg border border-blue-200 dark:border-blue-800">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-blue-700 dark:text-blue-300">
                Posições Ativas
              </h3>
              <span className="text-blue-600">🎯</span>
            </div>
            <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
              {portfolioData.activePositions}
            </div>
            <p className="text-xs text-blue-600 dark:text-blue-400">
              Win Rate: {portfolioData.winRate}%
            </p>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg border border-purple-200 dark:border-purple-800">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-purple-700 dark:text-purple-300">
                Sharpe Ratio
              </h3>
              <span className="text-purple-600">📊</span>
            </div>
            <div className="text-2xl font-bold text-purple-900 dark:text-purple-100">
              {portfolioData.sharpeRatio}
            </div>
            <p className="text-xs text-purple-600 dark:text-purple-400">
              Max DD: {portfolioData.maxDrawdown}%
            </p>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg border border-orange-200 dark:border-orange-800">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-orange-700 dark:text-orange-300">
                Nível de Risco
              </h3>
              <span className="text-orange-600">🛡️</span>
            </div>
            <div className="text-2xl font-bold text-orange-900 dark:text-orange-100">
              {portfolioData.riskLevel}
            </div>
            <p className="text-xs text-orange-600 dark:text-orange-400">
              Gestão ativa
            </p>
          </div>
        </div>

        {/* Tabs Navigation */}
        <div className="mb-6">
          <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
            <button className="flex-1 py-2 px-4 rounded-md bg-white dark:bg-slate-700 text-gray-900 dark:text-white font-medium shadow-sm">
              Visão Geral
            </button>
            <button className="flex-1 py-2 px-4 rounded-md text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
              Posições
            </button>
            <button className="flex-1 py-2 px-4 rounded-md text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
              Whale Alerts
            </button>
            <button className="flex-1 py-2 px-4 rounded-md text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
              Gestão de Risco
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Posições Ativas */}
          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Posições Ativas
            </h3>
            <div className="space-y-4">
              {positions.map((position, index) => (
                <div key={index} className="flex items-center justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div>
                      <div className="font-semibold text-lg text-slate-900 dark:text-white">
                        {position.symbol}
                      </div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">
                        {position.type} • {position.quantity} shares
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      position.type === 'LONG' 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`}>
                      {position.type}
                    </span>
                  </div>
                  
                  <div className="text-right">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-slate-900 dark:text-white">
                        ${position.currentPrice.toFixed(2)}
                      </span>
                      <span className={`text-sm ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {position.pnl >= 0 ? '+' : ''}${position.pnl.toFixed(2)} ({position.pnlPct.toFixed(2)}%)
                      </span>
                    </div>
                    <div className="text-xs text-slate-600 dark:text-slate-400">
                      Entry: ${position.entryPrice.toFixed(2)} • Conf: {(position.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Whale Alerts */}
          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center">
              🐋 Alertas de Whales
            </h3>
            <div className="space-y-4">
              {whaleAlerts.map((alert, index) => (
                <div key={index} className="flex items-start space-x-4 p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
                  <div className={`p-2 rounded-full ${
                    alert.severity === 'high' 
                      ? 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-200' 
                      : 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900 dark:text-yellow-200'
                  }`}>
                    {alert.severity === 'high' ? '⚠️' : '👁️'}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-semibold text-slate-900 dark:text-white">
                        {alert.symbol}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        alert.severity === 'high' 
                          ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' 
                          : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                      }`}>
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">
                      {alert.message}
                    </p>
                    <p className="text-xs text-slate-500">
                      {alert.timestamp}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Risk Management */}
        <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
            🛡️ Gestão de Risco
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
              <div className="text-2xl font-bold text-green-600">68.5%</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Win Rate</div>
            </div>
            <div className="text-center p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">2.1:1</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Risk/Reward</div>
            </div>
            <div className="text-center p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">1.85</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Sharpe Ratio</div>
            </div>
            <div className="text-center p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">-2.1%</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Max Drawdown</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App

