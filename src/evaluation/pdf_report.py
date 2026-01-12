"""Generador de PDF Alpha Report - Factsheet profesional tipo Goldman Sachs.

Genera un PDF con métricas, gráficos y análisis de la estrategia.

Ejemplo de uso:
    generator = AlphaReportGenerator()
    pdf_bytes = generator.generate(backtest_result, metadata)
    with open("report.pdf", "wb") as f:
        f.write(pdf_bytes)
"""

import io
from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    Image, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from ..backtest.engine import BacktestResult
from ..data.schemas import DataMetadata


class AlphaReportGenerator:
    """
    Genera PDF profesional tipo Factsheet/Alpha Report.
    
    Incluye:
    - Header con nombre de estrategia y período
    - Métricas clave: Sharpe, Sortino, Max DD, Win Rate
    - Tabla de estadísticas completa
    - Resumen de trades
    - Footer con timestamp
    """
    
    def __init__(
        self,
        title: str = "Alpha Strategy Report",
        subtitle: str = "Quantitative Trading Analysis",
    ):
        """
        Args:
            title: Título del reporte.
            subtitle: Subtítulo descriptivo.
        """
        self.title = title
        self.subtitle = subtitle
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados."""
        # Título principal
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=6,
            alignment=TA_CENTER,
        ))
        
        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER,
        ))
        
        # Sección header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#16213e'),
            spaceBefore=15,
            spaceAfter=10,
            borderPadding=5,
        ))
        
        # Métrica grande
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=20,
            textColor=colors.HexColor('#0f4c75'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))
        
        # Métrica label
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#888888'),
            alignment=TA_CENTER,
        ))
    
    def generate(
        self,
        result: BacktestResult,
        metadata: Optional[DataMetadata] = None,
        strategy_name: str = "Strategy",
        strategy_params: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Genera PDF como bytes.
        
        Args:
            result: Resultado del backtest.
            metadata: Metadata del dataset.
            strategy_name: Nombre de la estrategia.
            strategy_params: Parámetros de la estrategia.
            
        Returns:
            PDF como bytes (listo para guardar o descargar).
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )
        
        story = []
        
        # Header
        story.extend(self._build_header(strategy_name, metadata))
        
        # Línea separadora
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
        story.append(Spacer(1, 20))
        
        # Métricas principales
        story.extend(self._build_key_metrics(result))
        story.append(Spacer(1, 20))
        
        # Tabla de estadísticas
        story.extend(self._build_stats_table(result))
        story.append(Spacer(1, 20))
        
        # Resumen de trades
        story.extend(self._build_trades_summary(result))
        story.append(Spacer(1, 30))
        
        # Parámetros de estrategia
        if strategy_params:
            story.extend(self._build_params_section(strategy_params))
        
        # Footer
        story.extend(self._build_footer())
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _build_header(self, strategy_name: str, metadata: Optional[DataMetadata]) -> list:
        """Construye el header del reporte."""
        elements = []
        
        elements.append(Paragraph(self.title, self.styles['MainTitle']))
        elements.append(Paragraph(self.subtitle, self.styles['Subtitle']))
        
        # Info de la estrategia
        if metadata:
            info_text = f"<b>{strategy_name}</b> | {metadata.ticker} | {metadata.timeframe}"
            info_text += f" | {metadata.start_date.strftime('%Y-%m-%d')} to {metadata.end_date.strftime('%Y-%m-%d')}"
        else:
            info_text = f"<b>{strategy_name}</b>"
        
        elements.append(Paragraph(info_text, self.styles['Normal']))
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _build_key_metrics(self, result: BacktestResult) -> list:
        """Construye sección de métricas clave."""
        elements = []
        
        elements.append(Paragraph("Key Performance Metrics", self.styles['SectionHeader']))
        
        stats = result.stats
        
        # Crear tabla de métricas 2x4
        metrics = [
            ("Total Return", f"{stats.get('total_return_pct', 0):.2f}%"),
            ("Sharpe Ratio", f"{stats.get('sharpe_ratio', 0):.2f}"),
            ("Max Drawdown", f"{stats.get('max_drawdown_pct', 0):.2f}%"),
            ("Win Rate", f"{stats.get('win_rate_pct', 0):.1f}%"),
            ("Profit Factor", f"{stats.get('profit_factor', 0):.2f}"),
            ("Avg Trade", f"{stats.get('avg_trade_pct', 0):.2f}%"),
            ("Total Trades", f"{int(stats.get('num_trades', 0))}"),
            ("Sortino Ratio", f"{stats.get('sortino_ratio', 0):.2f}"),
        ]
        
        # 2 filas x 4 columnas
        table_data = []
        for i in range(0, len(metrics), 4):
            row_labels = []
            row_values = []
            for j in range(4):
                if i + j < len(metrics):
                    label, value = metrics[i + j]
                    row_labels.append(label)
                    row_values.append(value)
                else:
                    row_labels.append("")
                    row_values.append("")
            table_data.append(row_values)
            table_data.append(row_labels)
        
        table = Table(table_data, colWidths=[3.5*cm]*4)
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 16),
            ('FONTSIZE', (0, 2), (-1, 2), 16),
            ('FONTSIZE', (0, 1), (-1, 1), 9),
            ('FONTSIZE', (0, 3), (-1, 3), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0f4c75')),
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#0f4c75')),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#888888')),
            ('TEXTCOLOR', (0, 3), (-1, 3), colors.HexColor('#888888')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _build_stats_table(self, result: BacktestResult) -> list:
        """Construye tabla de estadísticas detalladas."""
        elements = []
        
        elements.append(Paragraph("Detailed Statistics", self.styles['SectionHeader']))
        
        stats = result.stats
        
        # 2 columnas de stats
        left_stats = [
            ("Initial Capital", f"${stats.get('initial_capital', 10000):,.2f}"),
            ("Final Equity", f"${stats.get('final_equity', 10000):,.2f}"),
            ("Total Return", f"{stats.get('total_return_pct', 0):.2f}%"),
            ("Annual Return", f"{stats.get('annual_return_pct', 0):.2f}%"),
            ("Max Drawdown", f"{stats.get('max_drawdown_pct', 0):.2f}%"),
        ]
        
        right_stats = [
            ("Sharpe Ratio", f"{stats.get('sharpe_ratio', 0):.3f}"),
            ("Sortino Ratio", f"{stats.get('sortino_ratio', 0):.3f}"),
            ("Calmar Ratio", f"{stats.get('calmar_ratio', 0):.3f}"),
            ("Win Rate", f"{stats.get('win_rate_pct', 0):.1f}%"),
            ("Profit Factor", f"{stats.get('profit_factor', 0):.2f}"),
        ]
        
        # Combinar en tabla
        table_data = [["Metric", "Value", "Metric", "Value"]]
        for i in range(max(len(left_stats), len(right_stats))):
            row = []
            if i < len(left_stats):
                row.extend(left_stats[i])
            else:
                row.extend(["", ""])
            if i < len(right_stats):
                row.extend(right_stats[i])
            else:
                row.extend(["", ""])
            table_data.append(row)
        
        table = Table(table_data, colWidths=[4*cm, 3*cm, 4*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _build_trades_summary(self, result: BacktestResult) -> list:
        """Construye resumen de trades."""
        elements = []
        
        elements.append(Paragraph("Trades Summary", self.styles['SectionHeader']))
        
        trades = result.trades
        
        if trades.empty:
            elements.append(Paragraph("No trades executed.", self.styles['Normal']))
            return elements
        
        # Stats básicos de trades
        total_trades = len(trades)
        if 'pnl' in trades.columns:
            winning = len(trades[trades['pnl'] > 0])
            losing = len(trades[trades['pnl'] < 0])
            avg_win = trades[trades['pnl'] > 0]['pnl'].mean() if winning > 0 else 0
            avg_loss = trades[trades['pnl'] < 0]['pnl'].mean() if losing > 0 else 0
        else:
            winning = losing = 0
            avg_win = avg_loss = 0
        
        summary_data = [
            ["Total Trades", str(total_trades)],
            ["Winning Trades", f"{winning} ({winning/total_trades*100:.0f}%)" if total_trades > 0 else "0"],
            ["Losing Trades", f"{losing} ({losing/total_trades*100:.0f}%)" if total_trades > 0 else "0"],
            ["Average Win", f"${avg_win:,.2f}"],
            ["Average Loss", f"${avg_loss:,.2f}"],
        ]
        
        table = Table(summary_data, colWidths=[6*cm, 4*cm])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e0e0e0')),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _build_params_section(self, params: Dict[str, Any]) -> list:
        """Construye sección de parámetros."""
        elements = []
        
        elements.append(Paragraph("Strategy Parameters", self.styles['SectionHeader']))
        
        table_data = [[k, str(v)] for k, v in params.items()]
        table = Table(table_data, colWidths=[5*cm, 5*cm])
        table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _build_footer(self) -> list:
        """Construye footer."""
        elements = []
        
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
        elements.append(Spacer(1, 10))
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer_text = f"<i>Generated on {timestamp} | Trading Backtester Pro</i>"
        
        elements.append(Paragraph(footer_text, ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#888888'),
            alignment=TA_CENTER,
        )))
        
        return elements
