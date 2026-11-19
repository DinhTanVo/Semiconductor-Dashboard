"""Eight-page narrative case study, not a dashboard screenshot collage."""
from io import BytesIO
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.utils import ImageReader
from reporting.config import settings as c
from reporting.src import analysis as a,figures as f
W,H=landscape(A4);NAVY='#102b49';BLUE='#2475db';TEAL='#008e83';AMBER='#bc762d';INK='#29405b';MUTED='#5c7690';BG='#f2f6fb'

class CaseStudy:
    def __init__(self,path):
        self.cv=canvas.Canvas(str(path),pagesize=(W,H));self.cv.setTitle('Semiconductor Process Quality Analytics | Vo Tan Dinh');self.cv.setAuthor('Vo Tan Dinh');self.cv.setSubject('A simulated engineering investigation: context, evidence and verification');self.page=0
    def box(self,x,y,w,h,fill='#ffffff',border='#d8e3ef',radius=7):
        self.cv.setFillColor(HexColor(fill));self.cv.setStrokeColor(HexColor(border));self.cv.roundRect(x,H-y-h,w,h,radius,stroke=1,fill=1)
    def text(self,text,x,y,w,size=11,color=INK,bold=False,max_h=None,leading=None):
        text=str(text).replace('—','-').replace('–','-').replace('→',' > ').replace('µ','u')
        p=Paragraph(text,ParagraphStyle('p',fontName='Helvetica-Bold' if bold else 'Helvetica',fontSize=size,leading=leading or size*1.4,textColor=HexColor(color)))
        _,h=p.wrap(w,2000)
        if max_h is not None and h>max_h:raise ValueError(f'Portfolio page {self.page} overflow: {text[:70]} ({h:.1f}>{max_h})')
        p.drawOn(self.cv,x,H-y-h);return h
    def start(self,number,label,title,context):
        self.page+=1;self.cv.bookmarkPage('page_'+str(self.page));self.cv.addOutlineEntry(label,'page_'+str(self.page),level=0);self.cv.setFillColor(HexColor(BG));self.cv.rect(0,0,W,H,fill=1,stroke=0);self.cv.setFillColor(HexColor(BLUE));self.cv.rect(0,H-6,W,6,fill=1,stroke=0)
        self.text(f'{number} / {label.upper()}',34,23,W-68,9,BLUE,True)
        self.text(title,34,46,W-68,24,NAVY,True,max_h=65,leading=28)
        self.text(context,34,111,W-68,11,MUTED,max_h=35)
        self.cv.setStrokeColor(HexColor('#d3dfed'));self.cv.line(34,35,W-34,35)
        self.text(escape(c.AUTHOR),34,H-26,W-110,8.5,MUTED)
        self.text(f'{self.page} / 8',W-65,H-26,40,8.5,MUTED)
    def image(self,data,x,y,w,h):
        self.cv.drawImage(ImageReader(BytesIO(data)),x,H-y-h,width=w,height=h,mask='auto')
    def card(self,x,y,w,title,body,h=100,accent=BLUE):
        self.box(x,y,w,h);self.cv.setFillColor(HexColor(accent));self.cv.rect(x,y and H-y-h or 0,3,h,fill=1,stroke=0)
        self.text(title,x+15,y+12,w-30,12,NAVY,True,max_h=35)
        self.text(body,x+15,y+43,w-30,10.5,INK,max_h=h-51)
    def table(self,headers,rows,widths,y,font=11):
        style=ParagraphStyle('stack_cell',fontName='Helvetica',fontSize=font,leading=font*1.4,textColor=HexColor(INK))
        cell=lambda t:Paragraph(t,style)
        data=[[cell('<b>'+escape(t)+'</b>') for t in headers]]+[[cell(t) for t in row] for row in rows]
        table=Table(data,colWidths=widths)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e5eef9')),('BACKGROUND',(0,1),(-1,-1),HexColor('#ffffff')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),13),('RIGHTPADDING',(0,0),(-1,-1),13),('TOPPADDING',(0,0),(-1,-1),13),('BOTTOMPADDING',(0,0),(-1,-1),13),('LINEBELOW',(0,0),(-1,-1),.6,HexColor('#d8e3ef'))]))
        _,height=table.wrap(W-68,1000)
        if y+height>H-55:raise ValueError('New portfolio table exceeds page')
        table.drawOn(self.cv,34,H-y-height)
        return y+height
    def end(self):self.cv.showPage()

def create_portfolio(t,r,m,d,browser,target):
    from reporting.src.export_reports import chart_png
    p=t['packages'];periods=a.periods(p).set_index('period');delta=a.period_delta(p)
    attach=m[m.process_id.eq('S09')];stream=attach[attach.subdivision_id.eq('E09A-H2')].sort_values(['timestamp','measurement_id']);z=a.imr(stream.value);cap=a.capability(stream.value,-10,10);left,right=a.display_bounds(stream,z,'Custom window',1800)
    i,mr=f.control_figures(stream,z,left,right,'um')
    images={'yield':chart_png(browser,f.yield_trend(p),1600,530),'i':chart_png(browser,i,1600,430),'mr':chart_png(browser,mr,1600,330),'variation':chart_png(browser,f.variation(attach),1600,560)}
    means=stream.groupby('period').value.mean();counts=stream.groupby('period').size();shift=means['Disturbance']-means['Reference'];postshift=means['Post-action']-means['Reference'];rates=a.event_rates(d[d.process_id.eq('S09')],r[r.process_id.eq('S09')],'subdivision_id').set_index('subdivision_id')
    q=CaseStudy(target);gap=16;cw=(W-68-2*gap)/3
    # 1: problem and purpose before statistics.
    q.start('01','Project at a glance','Semiconductor Process Quality Analytics','A simulated engineering case: from yield variation to a focused, verifiable investigation.')
    q.text('Vo Tan Dinh',34,151,W-68,17,NAVY,True)
    q.text('Engineering, Data &amp; Process Improvement',34,177,W-68,11,MUTED)
    q.box(34,213,370,126);q.text('The problem',50,228,338,14,NAVY,True)
    q.text('A decline in yield shows that performance has changed. It does not identify the process, equipment or mechanism responsible.',50,258,338,12,max_h=70)
    q.box(420,213,W-454,126);q.text('The objective',436,228,W-486,14,NAVY,True)
    q.text('Connect production outcomes with process measurements and equipment history, then define the evidence needed before corrective action.',436,258,W-486,12,max_h=70)
    q.text('The investigation path',34,363,W-68,13,NAVY,True)
    q.text('Understand the process  >  Locate the loss  >  Assess stability  >  Compare causes  >  Verify',34,390,W-68,11,BLUE,True,max_h=32)
    q.box(34,425,W-68,75,'#e7f0fc','#d3e2f4');q.text('What this portfolio demonstrates',50,437,W-100,12,NAVY,True)
    q.text('Manufacturing context, correct analysis grain, statistical reasoning and an evidence-based action plan. Project direction, analytical requirements and iterative review by Vo Tan Dinh. ',50,461,W-100,10.5,max_h=34)
    q.text('Independent project. All data is simulated; specifications and limits are illustrative.',34,524,W-68,9,MUTED,max_h=14);q.end()
    # 2: identify the process focus and what data can/cannot answer.
    q.start('02','Process & investigation scope','Focus the investigation on the right process','The route spans fabrication, package assembly and final testing. This case follows a placement-quality signal in assembly.')
    stages=[('Wafer fabrication','Build and connect transistors; screen wafers before die selection.'),('Assembly & packaging','Attach and interconnect selected dies; protect the package.'),('Testing & inspection','Check electrical and functional performance against the test plan.')]
    for j,(title,body) in enumerate(stages):q.card(34+j*(cw+gap),158,cw,title,body,111,TEAL if j==1 else BLUE)
    q.box(34,292,370,151);q.text('Investigation focus',50,307,338,13,NAVY,True)
    q.text('Flip-chip attach / X placement offset',50,337,338,12,TEAL,True)
    q.text('Compare bonding heads, then inspect E09A-H2 across the reference, disturbance and post-action periods. A placement signal is not automatically an electrical failure.',50,366,338,11,max_h=65)
    q.box(420,292,W-454,151);q.text('Data that supports the case',436,307,W-486,13,NAVY,True)
    q.text(f'120 lots · 3,000 wafers · 24,000 tracked packages<br/>{len(attach):,} attach measurements across four heads<br/>Unit genealogy, process screens, defect events and test attempts',436,337,W-486,11,max_h=82)
    q.text('Traceability: lot / wafer / package  >  process run / measurement  >  observed quality outcome',34,469,W-68,11,BLUE,True,max_h=35)
    q.text('Scope boundary: tracked packages are a selected cohort, not every die. Wafer, assembly and test yields retain separate denominators.',34,512,W-68,10.5,MUTED,max_h=35);q.end()
    # 3: one headline finding and one main chart.
    q.start('03','Where performance changed','Assembly yield declined during the disturbance period',f'The observed difference is {delta:+.2f} percentage points versus reference. Unequal cohort sizes are shown explicitly below.')
    q.image(images['yield'],34,158,W-68,225)
    for j,period in enumerate(c.PERIODS):
        row=periods.loc[period];q.box(34+j*(cw+gap),401,cw,89)
        q.text(period,49+j*(cw+gap),412,cw-30,11,NAVY,True)
        q.text(f'{row["yield"]:.2%}',49+j*(cw+gap),434,cw-30,21,TEAL if j==0 else AMBER if j==1 else BLUE,True)
        q.text(f'{int(row.failed):,} failed / {int(row.total):,} packages',49+j*(cw+gap),465,cw-30,10,MUTED)
    q.text('Interpretation: prioritize the disturbance cohort for process review. Colored windows are fixed simulation periods, not proof of a causal intervention effect.',34,510,W-68,10.5,max_h=34);q.end()
    # 4: I/MR with the same visible sequence and a clear capability implication.
    q.start('04','What the process signal shows','The selected head does not behave like its baseline',f'E09A-H2 / X placement offset. Full study n={len(stream):,}; display observations {left+1}–{right}. Limits use the first 40 study points.')
    q.image(images['i'],34,155,W-68,180);q.image(images['mr'],34,341,W-68,137)
    q.box(34,491,W-68,55,'#e7f0fc','#d3e2f4')
    q.text(f'{int(z["ooc"].sum()):,} Individuals signals in the full study. Cp/Cpk withheld: detected instability.',49,501,W-98,11,NAVY,True,max_h=18)
    q.text('Red diamonds mark observations beyond control limits, not defective packages. Next: compare heads and independently verify metrology.',49,523,W-98,10,MUTED,max_h=17);q.end()
    # 5: compare, quantify, then state the missing causal evidence.
    q.start('05','Which explanation deserves investigation','The disturbance shift is concentrated on E09A-H2','Like-for-like placement measurements are compared by head and period. The pattern prioritizes a hypothesis; it does not confirm a cause.')
    q.image(images['variation'],34,155,W-68,230)
    q.box(34,399,370,105);q.text('Observed evidence',50,412,338,12,NAVY,True)
    q.text(f'Mean shift: {shift:+.2f} um versus reference.<br/>Reference n={int(counts["Reference"]):,}; disturbance n={int(counts["Disturbance"]):,}.<br/>Post-action shift: {postshift:+.2f} um.',50,439,338,11,max_h=57)
    q.box(420,399,W-454,105);q.text('Alternative explanations',436,412,W-486,12,NAVY,True)
    q.text('Equipment condition, measurement bias, product mix and time effects remain plausible. Use a reference artifact and matched-lot comparisons before assigning a physical mechanism.',436,439,W-486,11,max_h=57)
    q.text(f'Impact boundary: {int((1-p.assembly_pass).sum()):,} assembly-failing packages in the 24,000-package cohort are not all attributable to this head. Post-action improvement alone is not effectiveness verification.',34,518,W-68,10.5,MUTED,max_h=31);q.end()
    # 6: proposed verification, not empty forms or invented completed CAPA.
    q.start('06','What should happen next','Turn the evidence into a controlled verification plan','The analysis defines where to investigate. Release decisions and corrective-action approval require independent engineering evidence.')
    rows=[('Containment','Define the head, time window and package cohort. Hold or independently screen suspect units under an approved plan.','Traceable cohort and documented disposition.'),('Cause verification','Check fixture/calibration history. Cross-check placement metrology, then compare matched products/lots.','Independent measurement agrees; alternatives are evaluated.'),('Effectiveness','Approve a new monitoring window after the action. Review stability and quality outcomes with fixed denominators.','Sustained results meet predefined, approved criteria.')]
    styles=ParagraphStyle('cell',fontName='Helvetica',fontSize=10.5,leading=15,textColor=HexColor(INK))
    cell=lambda text:Paragraph(text,styles)
    data=[[cell('<b>Step</b>'),cell('<b>Proposed action</b>'),cell('<b>Evidence required</b>')]]+[[cell(x) for x in row] for row in rows]
    tab=Table(data,colWidths=[105,385,W-68-490]);tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e5eef9')),('BACKGROUND',(0,1),(-1,-1),HexColor('#ffffff')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12),('LINEBELOW',(0,0),(-1,-1),.6,HexColor('#d6e2ef'))]));_,th=tab.wrap(W-68,400)
    if th>270:raise ValueError('Verification table too tall')
    tab.drawOn(q.cv,34,H-157-th)
    y=157+th+22;q.box(34,y,W-68,85);q.text('Contribution and limits',50,y+12,W-100,12,NAVY,True)
    q.text('Project direction, analytical requirements and iterative review by Vo Tan Dinh. This case demonstrates structured reasoning with simulated data, not production semiconductor experience or verified business savings.',50,y+38,W-100,10.5,max_h=40)
    q.text('Full dashboard: filters, data model, source-data exploration and detailed methods. The application runs locally; no hosting account is required.',34,y+101,W-68,10,MUTED,max_h=30);q.end()
    # 7: tools and their actual roles, verified against runtime and export modules.
    q.start('07','Technology Stack','How the project is built','A local application, reproducible data and tested analytical methods support the investigation.')
    rows=[
      ('<b>Application</b>','Python, HTML, CSS,<br/>JavaScript','Runs the local dashboard and supports navigation, filters and data exploration.'),
      ('<b>Data &amp; statistical analysis</b>','pandas, NumPy, SciPy','Prepares manufacturing data and calculates yield, control limits and process capability.'),
      ('<b>Visualization</b>','Plotly','Creates interactive charts for trends, distributions and equipment comparisons.'),
      ('<b>Data storage</b>','CSV','Stores reproducible simulated data with traceable relationships between production records.'),
      ('<b>Reporting &amp; validation</b>','Playwright, pytest,<br/>ReportLab, pypdf, PyMuPDF','Captures the interface, generates reports and tests analytical calculations and application behavior.')]
    bottom=q.table(['Layer','Technologies','Purpose'],rows,[164,202,W-68-366],158,10.7)
    q.text('Reporting roles: Playwright renders the interface; ReportLab creates the portfolio; pypdf assembles reports; PyMuPDF supports PDF links and quality checks.',34,bottom+16,W-68,9.5,MUTED,max_h=40)
    q.end()
    # 8: engineering principles tied to demonstrated project work.
    q.start('08','Applied Engineering Knowledge','The engineering knowledge behind the analysis','These methods connect manufacturing context, statistical evidence and a structured verification plan.')
    rows=[
      ('<b>Semiconductor processes</b>','Connects fabrication, assembly, packaging and testing to relevant measurements and failure modes.'),
      ('<b>Manufacturing data traceability</b>','Links lots, wafers, packages and process records while preserving the correct analytical grain.'),
      ('<b>Yield &amp; defect analysis</b>','Separates yield, screen failures and defect-event rates using explicit denominators.'),
      ('<b>Statistical Process Control</b>','Uses I-MR charts and frozen baseline limits to investigate changes in process behavior.'),
      ('<b>Process capability</b>','Interprets Cp/Cpk alongside stability, variation and distribution assumptions.'),
      ('<b>Root cause &amp; corrective action</b>','Organizes evidence, competing hypotheses, 5 Whys and CAPA verification without treating correlation as proof.')]
    bottom=q.table(['Area','Application in this project'],rows,[218,W-68-218],153,10.5)
    q.end()
    q.cv.save()
    print('Portfolio redesigned: eight narrative pages with native text and shared analytical figures.',flush=True)
