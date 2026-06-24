import csv
import os
from datetime import datetime


def export_transactions_csv(transactions, filepath):
    """Export transactions list to CSV."""
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            'No Invoice', 'Kasir', 'Total', 'Diskon', 'Total Akhir',
            'Bayar', 'Kembalian', 'Status', 'Tanggal'
        ])
        for t in transactions:
            writer.writerow([
                t['invoice_no'],
                t['cashier_name'],
                t['total_amount'],
                t['discount_amount'],
                t['final_amount'],
                t['paid_amount'],
                t['change_amount'],
                t['status'],
                t['created_at'],
            ])
    return filepath


def export_products_csv(products, filepath):
    """Export product list to CSV."""
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Kode', 'Nama Produk', 'Kategori', 'Harga', 'Stok', 'Deskripsi'])
        for p in products:
            writer.writerow([
                p['code'], p['name'], p['category'],
                p['price'], p['stock'], p['description'] or ''
            ])
    return filepath


def format_rupiah(amount):
    return f"Rp {amount:,.0f}".replace(',', '.')


def export_receipt_txt(invoice_no, cashier_name, items, total, discount,
                        final, paid, change, filepath):
    """Export a plain-text receipt."""
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    lines = [
        "=" * 40,
        "         THRIFTCASH",
        "    Toko Pakaian Bekas",
        "=" * 40,
        f"No      : {invoice_no}",
        f"Kasir   : {cashier_name}",
        f"Tanggal : {now}",
        "-" * 40,
    ]
    for it in items:
        name = it['product_name'][:20]
        lines.append(f"{name}")
        lines.append(f"  {it['quantity']} x {format_rupiah(it['price']):<14} {format_rupiah(it['subtotal'])}")
    lines += [
        "-" * 40,
        f"{'Subtotal':<24} {format_rupiah(total)}",
        f"{'Diskon':<24} {format_rupiah(discount)}",
        "=" * 40,
        f"{'TOTAL':<24} {format_rupiah(final)}",
        f"{'Bayar':<24} {format_rupiah(paid)}",
        f"{'Kembalian':<24} {format_rupiah(change)}",
        "=" * 40,
        "",
        "   Terima kasih sudah berbelanja!",
        "      ThriftCash — Bayar Cerdas",
        "=" * 40,
    ]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return filepath


def export_transactions_pdf_reportlab(transactions, filepath):
    """Export transactions to PDF using reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm

        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                leftMargin=1.5*cm, rightMargin=1.5*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('title', fontSize=18, fontName='Helvetica-Bold',
                                     textColor=colors.HexColor('#2D6A4F'), spaceAfter=4)
        sub_style = ParagraphStyle('sub', fontSize=10, textColor=colors.grey, spaceAfter=16)

        story.append(Paragraph("ThriftCash", title_style))
        story.append(Paragraph(f"Laporan Transaksi — Dicetak {datetime.now().strftime('%d/%m/%Y %H:%M')}", sub_style))

        headers = ['No Invoice', 'Kasir', 'Total Akhir', 'Bayar', 'Kembalian', 'Tanggal']
        data = [headers]
        for t in transactions:
            data.append([
                t['invoice_no'],
                t['cashier_name'],
                format_rupiah(t['final_amount']),
                format_rupiah(t['paid_amount']),
                format_rupiah(t['change_amount']),
                t['created_at'][:16],
            ])

        col_widths = [4*cm, 3*cm, 3*cm, 3*cm, 3*cm, 3.5*cm]
        tbl = Table(data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2D6A4F')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F0F4F1')]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8E4')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
        ]))
        story.append(tbl)

        total_rev = sum(t['final_amount'] for t in transactions)
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            f"<b>Total Pendapatan: {format_rupiah(total_rev)}</b> dari <b>{len(transactions)}</b> transaksi",
            styles['Normal']
        ))

        doc.build(story)
        return filepath
    except ImportError:
        return None
