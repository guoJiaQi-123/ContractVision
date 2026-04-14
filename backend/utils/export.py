import io
from datetime import datetime

import xlsxwriter
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle


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

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=20,
    )

    elements = []

    if title:
        elements.append(Paragraph(title, title_style))

    table_data = [[col['label'] for col in columns]]
    for row in data:
        table_data.append([str(row.get(col['key'], '')) for col in columns])

    col_widths = [col.get('pdf_width', 80) for col in columns]

    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
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
