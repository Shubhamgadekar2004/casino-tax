"""
Report Service — Generates PDF tax reports and Excel exports.
"""
import io
import pandas as pd
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from database.database import execute_query
from models.individual import get_individual_by_id
from models.transaction import get_player_ledger
from services.tax_service import calculate_tax


def generate_pdf_tax_certificate(individual_id: str) -> bytes:
    """Generate a PDF Tax & TDS Certificate for an individual."""
    ind = get_individual_by_id(individual_id)
    if not ind:
        raise ValueError(f"Individual {individual_id} not found")

    ledger = get_player_ledger(individual_id)
    summary = calculate_tax(individual_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CertTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        alignment=1,  # Center
    )
    subtitle_style = ParagraphStyle(
        "CertSubTitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
    )
    h2_style = ParagraphStyle(
        "CertH2",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "CertBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("<b>CASINO WINNINGS TAX & TDS CERTIFICATE</b>", title_style))
    story.append(Paragraph("Form 16A Equivalent — Demonstration Prototype", subtitle_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (IST)", subtitle_style))
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1")))
    story.append(Spacer(1, 10))

    # Player & Casino Details (2-column layout)
    story.append(Paragraph("<b>1. Taxpayer & Deductor Information</b>", h2_style))

    info_data = [
        [
            Paragraph(f"<b>Taxpayer Name:</b> {ind.get('first_name', '')} {ind.get('last_name', '')}".strip(), body_style),
            Paragraph("<b>Deductor Name:</b> Royal Horizon Casino Ltd.", body_style),
        ],
        [
            Paragraph(f"<b>PAN:</b> {ind['pan']}", body_style),
            Paragraph("<b>TAN:</b> MUMC12345F", body_style),
        ],
        [
            Paragraph(f"<b>KYC ID:</b> {ind.get('individual_id', '')}", body_style),
            Paragraph("<b>Jurisdiction:</b> Income Tax Dept, India", body_style),
        ],
        [
            Paragraph(f"<b>Risk Status:</b> {ind.get('risk_tier', 'LOW').upper()}", body_style),
            Paragraph("<b>Assessment Year:</b> 2025-26", body_style),
        ],
    ]

    t_info = Table(info_data, colWidths=[270, 270])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 15))

    # Tax Summary Table
    story.append(Paragraph("<b>2. Income & Tax Summary (u/s 115BB / 194B)</b>", h2_style))

    tax_summary_data = [
        ["Component", "Amount (INR)", "Applicable Rate / Section"],
        ["Gross Winnings Allocated", f"Rs. {summary['gross_winnings']:,.2f}", "Sec 115BB"],
        ["Total Buy-In Invested", f"Rs. {summary['total_buy_in']:,.2f}", "Deduction not allowable u/s 115BB"],
        ["Net Taxable Winnings", f"Rs. {summary['net_winnings']:,.2f}", "Taxable Gross Winnings"],
        ["Calculated Income Tax", f"Rs. {summary['tax_calculated']:,.2f}", f"Flat {summary['tax_rate_percent']}%"],
        ["TDS Deducted at Source", f"Rs. {summary['tds_deducted']:,.2f}", "Sec 194B (30%)"],
        ["Net Payout Received", f"Rs. {summary['net_payout']:,.2f}", "Gross - TDS"],
    ]

    t_tax = Table(tax_summary_data, colWidths=[240, 150, 150])
    t_tax.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ]))
    story.append(t_tax)
    story.append(Spacer(1, 15))

    # Detailed Transaction History
    story.append(Paragraph("<b>3. Game-wise Transaction Breakdown</b>", h2_style))

    tx_headers = ["Tx ID", "Date", "Game", "Buy-in (Rs.)", "Payout (Rs.)", "TDS (Rs.)", "Type"]
    tx_rows = [tx_headers]

    for tx in ledger[:15]:  # Limit to 15 rows for fit
        tx_rows.append([
            tx['transaction_id'],
            str(tx['timestamp'])[:10],
            tx['game_name'],
            f"{tx['buy_in_amount']:,.0f}",
            f"{tx['payout_amount']:,.0f}",
            f"{tx['tds_deducted']:,.0f}",
            tx['transaction_type'].replace('_', ' ').title(),
        ])

    t_ledger = Table(tx_rows, colWidths=[65, 70, 125, 75, 75, 65, 65])
    t_ledger.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#334155")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(t_ledger)
    story.append(Spacer(1, 20))

    # Disclaimer footer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1")))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<b>Disclaimer:</b> This document is automatically generated by the Casino Tax Demonstration System "
        "for illustrative and educational purposes only. Synthetic data used.",
        subtitle_style,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_excel_export() -> bytes:
    """Export all database tables into a multi-tab Excel file."""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 1. Individuals
        df_ind = pd.DataFrame(execute_query("SELECT * FROM individuals"))
        df_ind.to_excel(writer, sheet_name="Individuals", index=False)

        # 2. Games
        df_games = pd.DataFrame(execute_query("SELECT * FROM games"))
        df_games.to_excel(writer, sheet_name="Games", index=False)

        # 3. Game Participants
        df_parts = pd.DataFrame(execute_query("SELECT * FROM game_participants"))
        df_parts.to_excel(writer, sheet_name="Participants", index=False)

        # 4. Winnings Allocation
        df_win = pd.DataFrame(execute_query("SELECT * FROM winning_allocations"))
        df_win.to_excel(writer, sheet_name="Winnings Allocation", index=False)

        # 5. Transactions
        df_tx = pd.DataFrame(execute_query("SELECT * FROM transactions"))
        df_tx.to_excel(writer, sheet_name="Transactions", index=False)

        # 6. Tax Calculations
        df_tax = pd.DataFrame(execute_query("SELECT * FROM tax_calculations"))
        df_tax.to_excel(writer, sheet_name="Tax Calculations", index=False)

        # 7. TDS Records
        df_tds = pd.DataFrame(execute_query("SELECT * FROM tds_records"))
        df_tds.to_excel(writer, sheet_name="TDS Records", index=False)

        # 8. ITR Records
        df_itr = pd.DataFrame(execute_query("SELECT * FROM itr_records"))
        df_itr.to_excel(writer, sheet_name="ITR Declarations", index=False)

        # 9. Risk Scores
        df_risk = pd.DataFrame(execute_query("SELECT * FROM risk_scores"))
        df_risk.to_excel(writer, sheet_name="Risk Scores", index=False)

        # 10. Audit Logs
        df_audit = pd.DataFrame(execute_query("SELECT * FROM audit_logs"))
        df_audit.to_excel(writer, sheet_name="Audit Logs", index=False)

    output.seek(0)
    return output.getvalue()
