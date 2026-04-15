import io
from datetime import datetime

import xlsxwriter
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
from xml.sax.saxutils import escape


def export_to_excel(data, columns, filename=None):
    if filename is None:
        filename = f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Sheet1')

    header_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'bg_color': '#4472C4',
        'font_color': '#FFFFFF',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
    })

    cell_format = workbook.add_format({
        'font_size': 11,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
    })

    for col_idx, column in enumerate(columns):
        worksheet.write(0, col_idx, column['label'], header_format)
        worksheet.set_column(col_idx, col_idx, column.get('width', 15))

    for row_idx, row in enumerate(data, start=1):
        for col_idx, column in enumerate(columns):
            value = row.get(column['key'], '')
            worksheet.write(row_idx, col_idx, value, cell_format)

    workbook.close()
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def export_to_pdf(data, columns, title='', filename=None):
    if filename is None:
        filename = f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'

    # Ensure Chinese characters render correctly.
    # ReportLab default fonts (Helvetica, Times-Roman) do not support CJK glyphs.
    # Unicode CID fonts are built-in and avoid bundling TTF files.
    cjk_font_name = 'STSong-Light'
    try:
        pdfmetrics.getFont(cjk_font_name)
    except KeyError:
        pdfmetrics.registerFont(UnicodeCIDFont(cjk_font_name))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontName=cjk_font_name,
        fontSize=16,
        spaceAfter=20,
    )
    cell_style = ParagraphStyle(
        'CJKCell',
        parent=styles['BodyText'],
        fontName=cjk_font_name,
        fontSize=9,
        leading=11,
    )
    header_style = ParagraphStyle(
        'CJKHeader',
        parent=styles['BodyText'],
        fontName=cjk_font_name,
        fontSize=11,
        leading=13,
    )

    elements = []

    if title:
        elements.append(Paragraph(escape(str(title)), title_style))

    def _cell(value, style):
        return Paragraph(escape(str(value or '')), style)

    table_data = [[_cell(col['label'], header_style) for col in columns]]
    for row in data:
        table_data.append([_cell(row.get(col['key'], ''), cell_style) for col in columns])

    col_widths = [col.get('pdf_width', 80) for col in columns]

    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), cjk_font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
