from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import mm

def create_pdf(run):
    buffer=BytesIO(); doc=SimpleDocTemplate(buffer,pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=15*mm,bottomMargin=15*mm)
    styles=getSampleStyleSheet(); story=[]
    story.append(Paragraph('Wi-Fi TestLab — Network Test Report',styles['Title']))
    story.append(Paragraph(f'Test timestamp: {run.get("timestamp", "-")} | Test label: {run.get("label","-")}',styles['Normal']))
    story.append(Spacer(1,10))
    story.append(Paragraph('Network information',styles['Heading2']))
    wifi=run.get('wifi',{})
    story.append(Table([[str(k),str(v)] for k,v in wifi.items()],colWidths=[45*mm,110*mm],style=TableStyle([('GRID',(0,0),(-1,-1),0.4,colors.grey),('BACKGROUND',(0,0),(0,-1),colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP')]))); story.append(Spacer(1,8))
    story.append(Paragraph('Ping test results',styles['Heading2']))
    headers=['Target','Sent','Recv','Loss %','Avg ms','Min ms','Max ms']
    data=[headers]
    for p in run.get('pings',[]): data.append([p.get('target'),p.get('sent'),p.get('received'),p.get('packet_loss_pct'),p.get('avg_latency_ms'),p.get('min_latency_ms'),p.get('max_latency_ms')])
    story.append(Table(data,repeatRows=1,colWidths=[25*mm,15*mm,15*mm,20*mm,20*mm,20*mm,20*mm],style=TableStyle([('GRID',(0,0),(-1,-1),0.4,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))); story.append(Spacer(1,8))
    story.append(Paragraph('Speed test',styles['Heading2']))
    speed=run.get('speed',{})
    story.append(Paragraph(f'Download: {speed.get("download_mbps", "N/A")} Mbps | Upload: {speed.get("upload_mbps", "N/A")} Mbps | Status: {speed.get("speed_status", "-")}',styles['Normal'])); story.append(Spacer(1,8))
    story.append(Paragraph('Troubleshooting suggestions',styles['Heading2']))
    for i,tip in enumerate(run.get('diagnosis',[]),1): story.append(Paragraph(f'{i}. {tip}',styles['Normal'])); story.append(Spacer(1,4))
    story.append(Spacer(1,10)); story.append(Paragraph('Interpretation note: results are a snapshot and may vary with server, ISP load, device, Wi-Fi conditions, or ICMP filtering. Use repeated runs and change one variable at a time.',styles['Italic']))
    doc.build(story); buffer.seek(0); return buffer.getvalue()
