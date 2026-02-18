"""
API FastAPI para Trading Backtester Pro

Expone endpoints para:
- Ejecutar backtests
- Obtener datos de mercado
- Estado del bot
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data import DataLoader
from src.strategy import MACrossStrategy
from src.backtest import BacktestEngine, TradingCosts
from src.ml import FeatureEngineer, MLModel, MLStrategy
from src.evaluation.pdf_report import AlphaReportGenerator

app = FastAPI(
    title="Trading Backtester Pro API",
    description="API para backtesting y trading algorítmico",
    version="1.0.0",
)

# CORS para permitir requests del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BacktestRequest(BaseModel):
    ticker: str = "SPY"
    timeframe: str = "1d"
    strategy_type: str = "ma_cross"  # ma_cross | ml
    fast_period: int = 10
    slow_period: int = 50
    initial_capital: float = 100000
    commission_pct: float = 0.001
    sl_pct: Optional[float] = None
    tp_pct: Optional[float] = None


class BacktestResponse(BaseModel):
    success: bool
    stats: dict
    equity_data: list
    trades_count: int
    strategy_name: str
    trades_data: Optional[List[dict]] = None
    drawdown_data: Optional[List[dict]] = None
    monthly_returns: Optional[List[dict]] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "Trading Backtester Pro API", "status": "online"}


@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/api/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    try:
        # Load data
        loader = DataLoader()
        prices, metadata = loader.load(
            ticker=request.ticker,
            timeframe=request.timeframe,
            use_cache=True
        )
        
        if prices.empty:
            raise HTTPException(status_code=400, detail="No data available for ticker")
        
        # Create strategy
        if request.strategy_type == "ma_cross":
            strategy = MACrossStrategy(
                fast_period=request.fast_period,
                slow_period=request.slow_period
            )
        elif request.strategy_type == "ml":
            # Train ML model
            fe = FeatureEngineer()
            features, target = fe.prepare_dataset(prices, horizon=1, dropna=True)
            
            if len(features) < 100:
                raise HTTPException(status_code=400, detail="Not enough data for ML training")
            
            train_size = int(len(features) * 0.8)
            X_train = features.iloc[:train_size]
            y_train = target.iloc[:train_size]
            
            model = MLModel(model_type="random_forest")
            model.train(X_train, y_train)
            
            strategy = MLStrategy(model=model, feature_engineer=fe)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {request.strategy_type}")
        
        # Generate signals
        signal_result = strategy.generate_signals(prices)
        
        # Run backtest
        costs = TradingCosts(
            commission_pct=request.commission_pct,
            slippage_pct=0.0005
        )
        engine = BacktestEngine(
            initial_capital=request.initial_capital,
            costs=costs
        )
        
        result = engine.run(
            prices=prices,
            signals=signal_result.signals,
            sl_pct=request.sl_pct,
            tp_pct=request.tp_pct
        )
        
        # Format equity data for chart
        equity_data = [
            {"date": date.strftime("%Y-%m-%d"), "value": round(value, 2)}
            for date, value in zip(result.equity.index, result.equity.values)
        ]
        
        # Sample if too many points
        if len(equity_data) > 500:
            step = len(equity_data) // 500
            equity_data = equity_data[::step]
        
        # Calculate drawdown data
        import pandas as pd
        equity_series = result.equity
        running_max = equity_series.cummax()
        drawdown = (equity_series - running_max) / running_max * 100
        drawdown_data = [
            {"date": date.strftime("%Y-%m-%d"), "value": round(dd, 2)}
            for date, dd in zip(drawdown.index, drawdown.values)
        ]
        if len(drawdown_data) > 500:
            step = len(drawdown_data) // 500
            drawdown_data = drawdown_data[::step]
        
        # Calculate monthly returns
        equity_df = pd.DataFrame({"equity": result.equity})
        equity_df.index = pd.to_datetime(equity_df.index)
        monthly = equity_df.resample("ME").last()
        monthly_returns = []
        for i in range(1, len(monthly)):
            prev_val = monthly.iloc[i-1]["equity"]
            curr_val = monthly.iloc[i]["equity"]
            ret = (curr_val - prev_val) / prev_val * 100
            monthly_returns.append({
                "month": monthly.index[i].strftime("%b %Y"),
                "return": round(ret, 2)
            })
        
        # Format trades data
        trades_data = []
        if not result.trades.empty:
            trades_df = result.trades.copy()
            for _, trade in trades_df.tail(20).iterrows():
                trade_dict = {
                    "entry_date": str(trade.get("entry_date", trade.name) if hasattr(trade, "get") else trade.name),
                    "exit_date": str(trade.get("exit_date", "")),
                    "return_pct": round(float(trade.get("return_pct", trade.get("pnl", 0) / request.initial_capital * 100)), 2),
                    "pnl": round(float(trade.get("pnl", 0)), 2),
                }
                trades_data.append(trade_dict)
        
        # Convert numpy types to native Python types
        def convert_to_native(obj):
            import numpy as np
            if isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, (np.integer,)):
                return int(obj)
            elif isinstance(obj, (np.floating,)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        native_stats = convert_to_native(result.stats)
        
        return BacktestResponse(
            success=True,
            stats=native_stats,
            equity_data=equity_data,
            trades_count=int(result.stats.get("total_trades", 0)),
            strategy_name=strategy.name,
            trades_data=trades_data,
            drawdown_data=drawdown_data,
            monthly_returns=monthly_returns
        )
        
    except Exception as e:
        return BacktestResponse(
            success=False,
            stats={},
            equity_data=[],
            trades_count=0,
            strategy_name="",
            error=str(e)
        )


@app.get("/api/tickers")
async def get_tickers():
    """Lista de tickers populares."""
    return {
        "tickers": [
            {"symbol": "SPY", "name": "S&P 500 ETF"},
            {"symbol": "QQQ", "name": "Nasdaq 100 ETF"},
            {"symbol": "AAPL", "name": "Apple Inc."},
            {"symbol": "MSFT", "name": "Microsoft Corp."},
            {"symbol": "GOOGL", "name": "Alphabet Inc."},
            {"symbol": "AMZN", "name": "Amazon.com Inc."},
            {"symbol": "TSLA", "name": "Tesla Inc."},
            {"symbol": "NVDA", "name": "NVIDIA Corp."},
            {"symbol": "META", "name": "Meta Platforms"},
            {"symbol": "BTC-USD", "name": "Bitcoin USD"},
            {"symbol": "ETH-USD", "name": "Ethereum USD"},
        ]
    }


@app.get("/api/bot/status")
async def get_bot_status():
    """Estado del bot de trading."""
    try:
        from src.execution import AlpacaExecutor
        executor = AlpacaExecutor()
        account = executor.get_account()
        positions = executor.get_positions()
        
        return {
            "status": "running",
            "account": account,
            "positions": positions,
            "bot_type": "alpaca"
        }
    except Exception as e:
        return {
            "status": "offline",
            "error": str(e)
        }


@app.post("/api/report/pdf")
async def generate_pdf_report(request: BacktestRequest):
    """Genera PDF del backtest."""
    try:
        # Load data
        loader = DataLoader()
        prices, metadata = loader.load(
            ticker=request.ticker,
            timeframe=request.timeframe,
            use_cache=True
        )
        
        if prices.empty:
            raise HTTPException(status_code=400, detail="No data available")
        
        # Create strategy
        if request.strategy_type == "ma_cross":
            strategy = MACrossStrategy(
                fast_period=request.fast_period,
                slow_period=request.slow_period
            )
            strategy_params = {
                "fast_period": request.fast_period,
                "slow_period": request.slow_period,
            }
        elif request.strategy_type == "ml":
            fe = FeatureEngineer()
            features, target = fe.prepare_dataset(prices, horizon=1, dropna=True)
            train_size = int(len(features) * 0.8)
            model = MLModel(model_type="random_forest")
            model.train(features.iloc[:train_size], target.iloc[:train_size])
            strategy = MLStrategy(model=model, feature_engineer=fe)
            strategy_params = {"model_type": "random_forest"}
        else:
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {request.strategy_type}")
        
        # Generate signals and run backtest
        signal_result = strategy.generate_signals(prices)
        costs = TradingCosts(commission_pct=request.commission_pct, slippage_pct=0.0005)
        engine = BacktestEngine(initial_capital=request.initial_capital, costs=costs)
        result = engine.run(
            prices=prices,
            signals=signal_result.signals,
            sl_pct=request.sl_pct,
            tp_pct=request.tp_pct
        )
        
        # Generate PDF
        generator = AlphaReportGenerator(
            title="Trading Backtester Pro",
            subtitle="Quantitative Strategy Analysis"
        )
        pdf_bytes = generator.generate(
            result=result,
            metadata=metadata,
            strategy_name=strategy.name,
            strategy_params=strategy_params
        )
        
        filename = f"backtest_report_{request.ticker}_{request.strategy_type}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
