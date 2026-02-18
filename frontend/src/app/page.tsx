"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Wallet,
  Target,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  Percent,
  Play,
  Loader2,
  X,
  ChevronDown,
  Download,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from "recharts";

const API_URL = "http://localhost:8000";

interface BacktestResult {
  success: boolean;
  stats: Record<string, number>;
  equity_data: Array<{ date: string; value: number }>;
  trades_count: number;
  strategy_name: string;
  trades_data?: Array<{ entry_date: string; exit_date: string; return_pct: number; pnl: number }>;
  drawdown_data?: Array<{ date: string; value: number }>;
  monthly_returns?: Array<{ month: string; return: number }>;
  error?: string;
}

interface MetricCardProps {
  title: string;
  value: string;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  icon: React.ReactNode;
  delay?: number;
}

function MetricCard({ title, value, change, changeType = "neutral", icon, delay = 0 }: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="glass rounded-2xl p-6 card-hover"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground uppercase tracking-wider font-medium mb-1">
            {title}
          </p>
          <p className="text-3xl font-bold font-mono text-foreground">
            {value}
          </p>
          {change && (
            <div className={`flex items-center gap-1 mt-2 text-sm font-medium ${changeType === "positive" ? "text-green-400" :
              changeType === "negative" ? "text-red-400" :
                "text-gray-400"
              }`}>
              {changeType === "positive" ? <ArrowUpRight className="w-4 h-4" /> :
                changeType === "negative" ? <ArrowDownRight className="w-4 h-4" /> : null}
              {change}
            </div>
          )}
        </div>
        <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400">
          {icon}
        </div>
      </div>
    </motion.div>
  );
}

function StrategyModal({
  isOpen,
  onClose,
  onSubmit,
  isLoading
}: {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (config: BacktestConfig) => void;
  isLoading: boolean;
}) {
  const [config, setConfig] = useState<BacktestConfig>({
    ticker: "SPY",
    timeframe: "1d",
    strategy_type: "ma_cross",
    fast_period: 10,
    slow_period: 50,
    initial_capital: 100000,
  });

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="glass rounded-2xl p-6 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">Nueva Estrategia</h2>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Ticker */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">Ticker</label>
            <select
              value={config.ticker}
              onChange={(e) => setConfig({ ...config, ticker: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none transition-colors"
            >
              <option value="SPY">SPY - S&P 500 ETF</option>
              <option value="QQQ">QQQ - Nasdaq 100</option>
              <option value="AAPL">AAPL - Apple</option>
              <option value="MSFT">MSFT - Microsoft</option>
              <option value="TSLA">TSLA - Tesla</option>
              <option value="NVDA">NVDA - NVIDIA</option>
              <option value="BTC-USD">BTC-USD - Bitcoin</option>
            </select>
          </div>

          {/* Timeframe */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">Timeframe</label>
            <div className="grid grid-cols-3 gap-2">
              {["15m", "1h", "1d"].map((tf) => (
                <button
                  key={tf}
                  onClick={() => setConfig({ ...config, timeframe: tf })}
                  className={`py-2 px-4 rounded-xl font-medium transition-all ${config.timeframe === tf
                    ? "bg-blue-500 text-white"
                    : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                    }`}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>

          {/* Strategy Type */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">Estrategia</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setConfig({ ...config, strategy_type: "ma_cross" })}
                className={`py-3 px-4 rounded-xl font-medium transition-all ${config.strategy_type === "ma_cross"
                  ? "bg-blue-500 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                  }`}
              >
                MA Cross
              </button>
              <button
                onClick={() => setConfig({ ...config, strategy_type: "ml" })}
                className={`py-3 px-4 rounded-xl font-medium transition-all ${config.strategy_type === "ml"
                  ? "bg-purple-500 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                  }`}
              >
                Machine Learning
              </button>
            </div>
          </div>

          {/* MA Parameters */}
          {config.strategy_type === "ma_cross" && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">MA Rápida</label>
                <input
                  type="number"
                  value={config.fast_period}
                  onChange={(e) => setConfig({ ...config, fast_period: parseInt(e.target.value) })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">MA Lenta</label>
                <input
                  type="number"
                  value={config.slow_period}
                  onChange={(e) => setConfig({ ...config, slow_period: parseInt(e.target.value) })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>
          )}

          {/* Capital */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">Capital Inicial</label>
            <input
              type="number"
              value={config.initial_capital}
              onChange={(e) => setConfig({ ...config, initial_capital: parseFloat(e.target.value) })}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Submit Button */}
          <button
            onClick={() => onSubmit(config)}
            disabled={isLoading}
            className="w-full py-4 rounded-xl font-semibold text-white bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Ejecutando Backtest...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                Ejecutar Backtest
              </>
            )}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

interface BacktestConfig {
  ticker: string;
  timeframe: string;
  strategy_type: string;
  fast_period: number;
  slow_period: number;
  initial_capital: number;
}

export default function Dashboard() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [currentConfig, setCurrentConfig] = useState<BacktestConfig | null>(null);

  const runBacktest = async (config: BacktestConfig) => {
    setIsLoading(true);
    setCurrentConfig(config);

    try {
      const response = await fetch(`${API_URL}/api/backtest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      const data = await response.json();
      setResult(data);
      setIsModalOpen(false);
    } catch (error) {
      console.error("Error running backtest:", error);
      setResult({
        success: false,
        stats: {},
        equity_data: [],
        trades_count: 0,
        strategy_name: "",
        error: "Error de conexión. ¿Está corriendo el API? (uv run uvicorn api:app --reload)",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const stats = result?.stats || {};
  const equityData = result?.equity_data || [];
  const drawdownData = result?.drawdown_data || [];
  const monthlyReturns = result?.monthly_returns || [];
  const tradesData = result?.trades_data || [];

  const downloadPDF = async () => {
    if (!currentConfig) return;

    try {
      const response = await fetch(`${API_URL}/api/report/pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentConfig),
      });

      if (!response.ok) throw new Error("Error generating PDF");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report_${currentConfig.ticker}_${currentConfig.strategy_type}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error downloading PDF:", error);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Background gradient */}
      <div className="fixed inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 pointer-events-none" />

      {/* Strategy Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <StrategyModal
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            onSubmit={runBacktest}
            isLoading={isLoading}
          />
        )}
      </AnimatePresence>

      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <header className="border-b border-gray-800/50 backdrop-blur-lg bg-gray-900/80 sticky top-0 z-40">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-blue-500/10">
                  <Zap className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                  <h1 className="text-xl font-bold gradient-text">Trading Backtester Pro</h1>
                  <p className="text-xs text-gray-500">Backtesting institucional • ML avanzado</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                {result?.success && (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 text-green-400 text-sm font-medium">
                    <div className="w-2 h-2 rounded-full bg-green-400 pulse-live" />
                    {result.strategy_name}
                  </div>
                )}
                {result?.success && (
                  <button
                    onClick={downloadPDF}
                    className="px-4 py-2 rounded-xl bg-emerald-500/10 text-emerald-400 font-medium hover:bg-emerald-500/20 transition-colors flex items-center gap-2 border border-emerald-500/30"
                  >
                    <Download className="w-4 h-4" />
                    Descargar PDF
                  </button>
                )}
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="px-4 py-2 rounded-xl bg-blue-500 text-white font-medium hover:bg-blue-600 transition-colors flex items-center gap-2"
                >
                  <Play className="w-4 h-4" />
                  Nueva Estrategia
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto px-6 py-8">
          {/* Error Message */}
          {result?.error && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400"
            >
              <p className="font-medium">Error: {result.error}</p>
            </motion.div>
          )}

          {/* Current Strategy Info */}
          {currentConfig && result?.success && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mb-6 p-4 rounded-xl glass flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="p-2 rounded-lg bg-blue-500/10">
                  <BarChart3 className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Estrategia Activa</p>
                  <p className="font-semibold text-white">
                    {currentConfig.ticker} • {result.strategy_name} • {currentConfig.timeframe}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">Capital Inicial</p>
                <p className="font-mono font-semibold text-white">
                  ${currentConfig.initial_capital.toLocaleString()}
                </p>
              </div>
            </motion.div>
          )}

          {/* Hero Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <MetricCard
              title="Equity Total"
              value={result?.success ? `$${(stats.final_equity || 100000).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "$100,000"}
              change={result?.success ? `${(stats.total_return_pct || 0).toFixed(1)}% Total` : "—"}
              changeType={stats.total_return_pct > 0 ? "positive" : stats.total_return_pct < 0 ? "negative" : "neutral"}
              icon={<Wallet className="w-6 h-6" />}
              delay={0}
            />
            <MetricCard
              title="Sharpe Ratio"
              value={result?.success ? (stats.sharpe_ratio || 0).toFixed(2) : "—"}
              change={stats.sharpe_ratio > 1 ? "Excelente" : stats.sharpe_ratio > 0.5 ? "Bueno" : "Bajo"}
              changeType={stats.sharpe_ratio > 1 ? "positive" : stats.sharpe_ratio > 0.5 ? "neutral" : "negative"}
              icon={<Target className="w-6 h-6" />}
              delay={0.1}
            />
            <MetricCard
              title="Max Drawdown"
              value={result?.success ? `${(stats.max_drawdown_pct || 0).toFixed(1)}%` : "—"}
              change={Math.abs(stats.max_drawdown_pct || 0) < 10 ? "Controlado" : "Alto"}
              changeType={Math.abs(stats.max_drawdown_pct || 0) < 10 ? "positive" : "negative"}
              icon={<TrendingDown className="w-6 h-6" />}
              delay={0.2}
            />
            <MetricCard
              title="Win Rate"
              value={result?.success ? `${(stats.win_rate_pct || 0).toFixed(1)}%` : "—"}
              change={`${stats.total_trades || 0} trades`}
              changeType={stats.win_rate_pct > 50 ? "positive" : "neutral"}
              icon={<Percent className="w-6 h-6" />}
              delay={0.3}
            />
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Equity Chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="glass rounded-2xl p-6 card-hover"
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-white">Curva de Equity</h3>
                  <p className="text-sm text-gray-500">Performance acumulado</p>
                </div>
              </div>
              {equityData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={equityData}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="date" stroke="#64748b" fontSize={10} tickFormatter={(v) => v.slice(5)} />
                    <YAxis stroke="#64748b" fontSize={10} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(17, 24, 39, 0.95)",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: "12px",
                      }}
                      formatter={(value) => [`$${(value ?? 0).toLocaleString()}`, "Equity"]}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#6366f1"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorValue)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>Ejecuta un backtest para ver la curva de equity</p>
                  </div>
                </div>
              )}
            </motion.div>

            {/* Stats Grid */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.5 }}
              className="glass rounded-2xl p-6 card-hover"
            >
              <h3 className="text-lg font-semibold text-white mb-4">Estadísticas Detalladas</h3>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: "Profit Factor", value: (stats.profit_factor || 0).toFixed(2), icon: <BarChart3 className="w-4 h-4" /> },
                  { label: "Sortino Ratio", value: (stats.sortino_ratio || 0).toFixed(2), icon: <Target className="w-4 h-4" /> },
                  { label: "Calmar Ratio", value: (stats.calmar_ratio || 0).toFixed(2), icon: <Activity className="w-4 h-4" /> },
                  { label: "Avg Trade", value: `${(stats.avg_trade_pct || 0).toFixed(2)}%`, icon: <TrendingUp className="w-4 h-4" /> },
                  { label: "Best Trade", value: `${(stats.best_trade_pct || 0).toFixed(1)}%`, icon: <ArrowUpRight className="w-4 h-4" /> },
                  { label: "Worst Trade", value: `${(stats.worst_trade_pct || 0).toFixed(1)}%`, icon: <ArrowDownRight className="w-4 h-4" /> },
                ].map((stat, index) => (
                  <div key={index} className="p-4 rounded-xl bg-gray-800/50 hover:bg-gray-800 transition-colors">
                    <div className="flex items-center gap-2 text-gray-400 mb-1">
                      {stat.icon}
                      <span className="text-xs uppercase tracking-wider">{stat.label}</span>
                    </div>
                    <p className="text-xl font-bold font-mono text-white">
                      {result?.success ? stat.value : "—"}
                    </p>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Monthly Returns & Drawdown Charts */}
          {result?.success && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Monthly Returns Chart */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.6 }}
                className="glass rounded-2xl p-6 card-hover"
              >
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white">Retornos Mensuales</h3>
                    <p className="text-sm text-gray-500">Performance por mes</p>
                  </div>
                </div>
                {monthlyReturns.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={monthlyReturns}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="month" stroke="#64748b" fontSize={10} />
                      <YAxis stroke="#64748b" fontSize={10} tickFormatter={(v) => `${v}%`} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "rgba(17, 24, 39, 0.95)",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: "12px",
                        }}
                        formatter={(value) => [`${(Number(value) ?? 0).toFixed(2)}%`, "Retorno"]}
                      />
                      <Bar dataKey="return" radius={[4, 4, 0, 0]}>
                        {monthlyReturns.map((entry, index) => (
                          <Cell key={index} fill={entry.return >= 0 ? "#22c55e" : "#ef4444"} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[250px] flex items-center justify-center text-gray-500">
                    <p>Sin datos de retornos mensuales</p>
                  </div>
                )}
              </motion.div>

              {/* Drawdown Chart */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.7 }}
                className="glass rounded-2xl p-6 card-hover"
              >
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white">Drawdown</h3>
                    <p className="text-sm text-gray-500">Caídas desde máximos</p>
                  </div>
                </div>
                {drawdownData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={drawdownData}>
                      <defs>
                        <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="date" stroke="#64748b" fontSize={10} tickFormatter={(v) => v.slice(5)} />
                      <YAxis stroke="#64748b" fontSize={10} tickFormatter={(v) => `${v}%`} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "rgba(17, 24, 39, 0.95)",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: "12px",
                        }}
                        formatter={(value) => [`${(Number(value) ?? 0).toFixed(2)}%`, "Drawdown"]}
                      />
                      <Area
                        type="monotone"
                        dataKey="value"
                        stroke="#ef4444"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorDrawdown)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[250px] flex items-center justify-center text-gray-500">
                    <p>Sin datos de drawdown</p>
                  </div>
                )}
              </motion.div>
            </div>
          )}

          {/* Trades Table */}
          {result?.success && tradesData.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.8 }}
              className="glass rounded-2xl p-6 card-hover mb-8"
            >
              <h3 className="text-lg font-semibold text-white mb-4">Últimos Trades</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left py-3 px-4 text-sm text-gray-400 font-medium">Entrada</th>
                      <th className="text-left py-3 px-4 text-sm text-gray-400 font-medium">Salida</th>
                      <th className="text-right py-3 px-4 text-sm text-gray-400 font-medium">Retorno %</th>
                      <th className="text-right py-3 px-4 text-sm text-gray-400 font-medium">P&L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tradesData.slice(-10).reverse().map((trade, index) => (
                      <tr key={index} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                        <td className="py-3 px-4 text-sm text-gray-300 font-mono">{trade.entry_date?.slice(0, 10)}</td>
                        <td className="py-3 px-4 text-sm text-gray-300 font-mono">{trade.exit_date?.slice(0, 10)}</td>
                        <td className={`py-3 px-4 text-sm font-mono text-right ${trade.return_pct >= 0 ? "text-green-400" : "text-red-400"}`}>
                          {trade.return_pct >= 0 ? "+" : ""}{trade.return_pct.toFixed(2)}%
                        </td>
                        <td className={`py-3 px-4 text-sm font-mono text-right ${trade.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                          {trade.pnl >= 0 ? "+" : ""}${trade.pnl.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* Footer */}
          <motion.footer
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="mt-12 text-center text-gray-500 text-sm"
          >
            <p>Trading Backtester Pro • Next.js + FastAPI + Python</p>
          </motion.footer>
        </main>
      </div>
    </div>
  );
}
