#!/usr/bin/env python
"""
Generador de Informes de Trading

Genera informes PDF semanales/mensuales desde los logs de órdenes.

Uso:
    # Informe de la última semana
    uv run python scripts/generate_report.py --period week
    
    # Informe del último mes
    uv run python scripts/generate_report.py --period month
    
    # Informe personalizado
    uv run python scripts/generate_report.py --start 2026-01-01 --end 2026-01-07
"""

import argparse
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Image as RLImage


def load_orders(db_path: Path, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Carga órdenes desde SQLite."""
    if not db_path.exists():
        return pd.DataFrame()
    
    conn = sqlite3.connect(db_path)
    
    query = """
        SELECT * FROM order_logs 
        WHERE created_at >= ? AND created_at <= ?
        ORDER BY created_at DESC
    """
    
    try:
        df = pd.read_sql_query(query, conn, params=[
            start_date.isoformat(), 
            end_date.isoformat()
        ])
    except:
        # Intentar con tabla mt5_order_logs
        try:
            query = """
                SELECT * FROM mt5_order_logs 
                WHERE created_at >= ? AND created_at <= ?
                ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn, params=[
                start_date.isoformat(), 
                end_date.isoformat()
            ])
        except:
            df = pd.DataFrame()
    
    conn.close()
    return df


def calculate_metrics(orders: pd.DataFrame) -> dict:
    """Calcula métricas de performance."""
    if orders.empty:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "avg_trade": 0,
            "best_trade": 0,
            "worst_trade": 0,
        }
    
    # Filtrar solo trades completados
    completed = orders[orders["status"] == "filled"] if "status" in orders.columns else orders
    
    metrics = {
        "total_trades": len(completed),
        "total_orders": len(orders),
    }
    
    # Si tenemos información de slippage
    if "slippage_pct" in completed.columns:
        metrics["avg_slippage"] = completed["slippage_pct"].mean()
    
    # Calcular por símbolo
    if "symbol" in completed.columns:
        metrics["symbols_traded"] = completed["symbol"].nunique()
        metrics["trades_by_symbol"] = completed.groupby("symbol").size().to_dict()
    
    return metrics


def generate_pdf_report(
    orders: pd.DataFrame,
    metrics: dict,
    period_name: str,
    start_date: datetime,
    end_date: datetime,
    output_path: Path,
):
    """Genera informe PDF."""
    
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=20,
    )
    story.append(Paragraph(f"📊 Informe de Trading - {period_name}", title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Período
    period_text = f"Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
    story.append(Paragraph(period_text, styles["Normal"]))
    story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))
    
    # Resumen de métricas
    story.append(Paragraph("📈 Resumen de Actividad", styles["Heading2"]))
    story.append(Spacer(1, 0.1 * inch))
    
    summary_data = [
        ["Métrica", "Valor"],
        ["Total de Órdenes", str(metrics.get("total_orders", 0))],
        ["Trades Ejecutados", str(metrics.get("total_trades", 0))],
        ["Símbolos Operados", str(metrics.get("symbols_traded", 0))],
    ]
    
    if "avg_slippage" in metrics:
        summary_data.append(["Slippage Promedio", f"{metrics['avg_slippage']:.4f}%"])
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a4e69")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#dee2e6")),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Desglose por símbolo
    if "trades_by_symbol" in metrics and metrics["trades_by_symbol"]:
        story.append(Paragraph("🎯 Trades por Símbolo", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))
        
        symbol_data = [["Símbolo", "Cantidad de Trades"]]
        for symbol, count in metrics["trades_by_symbol"].items():
            symbol_data.append([symbol, str(count)])
        
        symbol_table = Table(symbol_data, colWidths=[3*inch, 2*inch])
        symbol_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a4e69")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#dee2e6")),
        ]))
        story.append(symbol_table)
        story.append(Spacer(1, 0.3 * inch))
    
    # Historial de órdenes
    if not orders.empty:
        story.append(Paragraph("📋 Historial de Órdenes", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))
        
        # Seleccionar columnas relevantes
        display_cols = ["timestamp", "symbol", "side", "status"]
        available_cols = [c for c in display_cols if c in orders.columns]
        
        if available_cols:
            display_df = orders[available_cols].head(20)  # Últimas 20
            
            order_data = [available_cols]
            for _, row in display_df.iterrows():
                order_data.append([str(row[col])[:20] for col in available_cols])
            
            col_width = 5.5 * inch / len(available_cols)
            order_table = Table(order_data, colWidths=[col_width] * len(available_cols))
            order_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a4e69")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
                ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#dee2e6")),
            ]))
            story.append(order_table)
    else:
        story.append(Paragraph("No hay órdenes en este período.", styles["Normal"]))
    
    story.append(Spacer(1, 0.5 * inch))
    
    # Footer
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.gray,
    )
    story.append(Paragraph("Generado automáticamente por Portafolio ML Trading System", footer_style))
    
    # Build PDF
    doc.build(story)
    print(f"✅ Informe generado: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generador de Informes de Trading")
    parser.add_argument("--period", choices=["day", "week", "month"], default="week",
                       help="Período del informe")
    parser.add_argument("--start", type=str, help="Fecha inicio (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="Fecha fin (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, help="Archivo de salida")
    
    args = parser.parse_args()
    
    # Determinar fechas
    end_date = datetime.now()
    
    if args.start and args.end:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
        end_date = datetime.strptime(args.end, "%Y-%m-%d")
        period_name = f"{args.start} a {args.end}"
    elif args.period == "day":
        start_date = end_date - timedelta(days=1)
        period_name = "Diario"
    elif args.period == "week":
        start_date = end_date - timedelta(days=7)
        period_name = "Semanal"
    else:  # month
        start_date = end_date - timedelta(days=30)
        period_name = "Mensual"
    
    print(f"📊 Generando informe {period_name}...")
    print(f"   Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    
    # Cargar órdenes de Alpaca y MT5
    orders_alpaca = load_orders(Path("data/orders.db"), start_date, end_date)
    orders_mt5 = load_orders(Path("data/mt5_orders.db"), start_date, end_date)
    
    # Combinar
    all_orders = pd.concat([orders_alpaca, orders_mt5], ignore_index=True)
    
    print(f"   Órdenes encontradas: {len(all_orders)}")
    
    # Calcular métricas
    metrics = calculate_metrics(all_orders)
    
    # Generar output path
    if args.output:
        output_path = Path(args.output)
    else:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = reports_dir / f"trading_report_{args.period}_{timestamp}.pdf"
    
    # Generar PDF
    generate_pdf_report(
        orders=all_orders,
        metrics=metrics,
        period_name=period_name,
        start_date=start_date,
        end_date=end_date,
        output_path=output_path,
    )


if __name__ == "__main__":
    main()
