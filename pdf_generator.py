import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_report(player_name, role_type, key_metrics, insights):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=10
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=10,
        spaceAfter=8
    )
    body_style = styles['Normal']
    
    story = []
    
    # Header Section
    story.append(Paragraph("Player Development Coaching Report", title_style))
    story.append(Paragraph(f"<b>Player:</b> {player_name} | <b>Focus:</b> {role_type}", body_style))
    story.append(Spacer(1, 12))
    
    # Key Performance Indicators Table
    story.append(Paragraph("Key Metrics Summary", section_style))
    table_data = [["Metric", "Value", "Benchmark Target"]]
    for k, v, b in key_metrics:
        table_data.append([k, str(v), str(b)])
        
    t = Table(table_data, colWidths=[200, 150, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F3F4F6')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    # Coaching Action Items
    story.append(Paragraph("Actionable Coaching Insights", section_style))
    for insight in insights:
        story.append(Paragraph(f"- {insight}", body_style))
        story.append(Spacer(1, 4))
        
    doc.build(story)
    buffer.seek(0)
    return buffer