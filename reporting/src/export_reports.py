"""V6: one complete tab per tall PDF page + a separate eight-page case study."""
import argparse,base64,html,json,os,re,tempfile,hashlib,math
from pathlib import Path
from datetime import datetime,timezone
from io import BytesIO
import pandas as pd
from playwright.sync_api import sync_playwright
from pypdf import PdfReader,PdfWriter
from reportlab.pdfgen import canvas
from plotly.offline import get_plotlyjs
from reporting.config import settings as c
from reporting.src.data import load_data,enrich
from reporting.src import analysis as a,figures as f
from reporting.tabs.views import render as render_base,H
from reporting.src.explore import data_view
from bs4 import BeautifulSoup

def render(page,t,r,m,d,state=None):
    body=render_base(page,t,r,m,d,state)
    soup=BeautifulSoup(body,'html.parser')
    explorer=soup.select_one('#data-explorer')
    if explorer is not None:
        df=data_view(t,r,m,state or {},'measurements','selected','','',False)
        cols=[c for c in ['measurement_id','run_id','timestamp','value','unit'] if c in df.columns]
        fragment=BeautifulSoup('<div class="explorer-preview"><p>Rows 1–10 of '+format(len(df),',')+' | Selected scope</p>'+df[cols].head(10).to_html(index=False,border=0,escape=True)+'</div>','html.parser')
        explorer.append(fragment)
    nav='<nav class="report-tabs">'+''.join('<a href="#'+key+'">'+label+'</a>' for key,label in [('overview','Manufacturing Overview'),('eda','Data Overview &amp; EDA'),('yield','Yield &amp; Defect Analysis'),('spc','SPC &amp; Capability'),('root','Root Cause Investigation')])+'</nav>'
    return nav+'<div class="actions"><button class="secondary">Reset filters</button><a href="portfolio_summary.pdf">Portfolio PDF</a><a href="full_dashboard_report.pdf">Full dashboard PDF</a></div>'+str(soup)


FULL_CSS='''
@page{margin:28px 40px 42px}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}html,body{padding:0!important;margin:0!important;background:#f1f5fa!important}body{width:1320px!important;font:14px/1.65 Arial,sans-serif!important}h1,h2,h3,h4,p,div,section,figure,details,table,tr{break-before:auto!important;break-after:auto!important;break-inside:auto!important;page-break-before:auto!important;page-break-after:auto!important;page-break-inside:auto!important}.report-head{padding:26px 30px;background:#102b49;color:white;border-top:4px solid #2475db;border-radius:8px;margin-bottom:20px}.report-head h1{font-size:27px;color:white;margin:0 0 8px}.report-head .author-byline{color:#d8eaff}.report-scope{padding:16px 20px;background:#e7f0fc;border-left:3px solid #2475db;margin:20px 0;font-size:12px}.chart-card{height:auto!important;overflow:visible!important}.print-chart{display:block;width:100%;height:auto}.two-grid{grid-template-columns:1fr 1fr!important;align-items:stretch!important}.three-grid,.trace-grid{grid-template-columns:repeat(3,minmax(0,1fr))!important}.process-row{grid-template-columns:1fr 1fr!important}.schema-grid{display:none!important}.model-svg{width:100%!important;min-width:0!important;max-height:none!important}.model-viewport{overflow:visible!important}.model-sheet{break-before:auto!important;break-after:auto!important}.filter-panel{display:block!important}.actions,.page-pager,.explorer-controls,.model-toolbar{display:flex!important;flex-wrap:wrap;gap:10px}button{display:inline-block!important}input,select{font:inherit;max-width:100%}.filter-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.explorer-preview{font-size:10px;overflow:hidden}.explorer-preview table{font-size:10px}.report-tabs{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}.report-tabs a{padding:9px 12px;background:white;border:1px solid #d8e3ef;border-radius:5px;color:#2475db;text-decoration:none}details{display:block!important}summary{display:block;font-weight:bold;color:#2475db}.form-grid{grid-template-columns:1fr 1fr!important}.print-field{min-height:75px;padding:15px;background:#f8fbff;border:1px solid #d8e3ef;border-radius:5px;white-space:pre-wrap}.table-wrap{overflow:visible!important;max-height:none!important}table{font-size:12px}.quick-nav{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0}.quick-nav a{padding:12px 16px;background:white;border:1px solid #cbdcf0;border-radius:5px;text-decoration:none}.report-section{margin:35px 0;scroll-margin-top:20px}.scope{font-size:12px}.eyebrow{display:none!important}.stage-copy .eyebrow{display:block!important}.period-note{font-size:12px}.bga-diagram{width:100%}
'''
MOUNT='''async()=>{for(const el of document.querySelectorAll('[data-figure]')){const obj=JSON.parse(document.getElementById(el.dataset.figure).textContent);await Plotly.newPlot(el,obj.data,obj.layout,{staticPlot:true,displayModeBar:false})}document.querySelectorAll('details').forEach(d=>d.open=true);await new Promise(r=>setTimeout(r,200));for(const p of document.querySelectorAll('.js-plotly-plot'))await Plotly.Plots.resize(p)}'''
CONVERT='''async()=>{for(const el of [...document.querySelectorAll('.js-plotly-plot')]){const card=el.closest('.chart-card'),two=!!card.closest('.two-grid');const w=two?800:1320,h=Math.max(310,Math.min(520,el._fullLayout.height));const layout=JSON.parse(JSON.stringify(el.layout));layout.width=w;layout.height=h;layout.autosize=false;layout.font={family:'Arial',size:14,color:'#29405b'};layout.margin={l:two?95:80,r:55,t:70,b:110};layout.title={...layout.title,font:{size:18},x:.025};const temp=document.createElement('div');document.body.appendChild(temp);await Plotly.newPlot(temp,el.data,layout,{staticPlot:true});const src=await Plotly.toImage(temp,{format:'png',width:w,height:h,scale:1.7});Plotly.purge(temp);temp.remove();const img=document.createElement('img');img.src=src;img.className='print-chart';img.alt=el._fullLayout.title.text||'Analysis chart';Plotly.purge(el);card.innerHTML='';card.appendChild(img)}for(const field of [...document.querySelectorAll('textarea')]){const div=document.createElement('div');div.className='print-field';div.textContent=field.value||'Not recorded - editable template.';field.replaceWith(div)}document.querySelectorAll('script[type="application/json"]').forEach(e=>e.remove());await Promise.all([...document.images].map(i=>i.decode()))}'''

def header(title,subtitle=''):
    return f'<header class="report-head"><h1>{H(title)}</h1>'+ (f'<div>{H(subtitle)}</div>' if subtitle else '')+f'<div class="author-byline">{H(c.AUTHOR)}</div></header>'

def document(body):
    css=(c.ROOT/'reporting/assets/style.css').read_text();js=(c.ROOT/'assets/plotly.min.js').read_text()
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+H(c.TITLE)+'</title><style>'+css+'\n'+FULL_CSS+'</style><script>'+js+'</script></head><body>'+body+'</body></html>'

def tall_page(browser,body,target,notes):
    page=browser.new_page(viewport={'width':1400,'height':1000});page.set_content(document(body),wait_until='load',timeout=60000);page.evaluate(MOUNT)
    for key,value in notes.items():
        if page.locator('#'+key).count():page.locator('#'+key).fill(value)
    page.evaluate(CONVERT);page.emulate_media(media='print');page.wait_for_timeout(100)
    height=page.evaluate('Math.ceil(Math.max(document.body.scrollHeight,document.body.getBoundingClientRect().height))')+100
    if height>18000:raise ValueError('Tab exceeds supported single-page export height; do not silently split')
    footer=f'<div style="width:100%;font:10px Arial;color:#526d88;padding:0 40px">{H(c.AUTHOR)}</div>'
    page.pdf(path=str(target),width='1400px',height=f'{height}px',print_background=True,prefer_css_page_size=False,display_header_footer=True,header_template='<span></span>',footer_template=footer,margin={'top':'28px','bottom':'42px','left':'40px','right':'40px'})
    snapshot=page.content();page.close()
    reader=PdfReader(str(target))
    if len(reader.pages)!=1:raise ValueError(f'Expected one tab per PDF page: {target.name} has {len(reader.pages)}')
    return snapshot,height

def merge(parts,target):
    writer=PdfWriter()
    for title,path in parts:writer.append(str(path),outline_item=title)
    total=len(writer.pages)
    for i,page in enumerate(writer.pages):
        overlay=BytesIO();cv=canvas.Canvas(overlay,pagesize=(float(page.mediabox.width),float(page.mediabox.height)));cv.setFont('Helvetica',9);cv.setFillColorRGB(.32,.42,.52);cv.drawRightString(float(page.mediabox.width)-30,15,f'{i+1} / {total}');cv.save();overlay.seek(0);page.merge_page(PdfReader(overlay).pages[0])
    writer.add_metadata({'/Title':'Full Dashboard Report','/Author':'Vo Tan Dinh','/Subject':'Manufacturing quality analysis; simulated data'})
    with open(target,'wb') as out:writer.write(out)
    import fitz
    doc=fitz.open(target)
    destinations=[('Manufacturing Overview',1),('Data Overview & EDA',2),('Yield & Defect Analysis',3),('SPC & Capability',4),('Root Cause Investigation',5)]
    for page in doc:
        for label,destination in destinations:
            for rect in page.search_for(label):
                if rect.y0<360 or page.number==0:
                    page.insert_link({'kind':fitz.LINK_GOTO,'from':rect,'page':destination,'to':fitz.Point(0,0)})
    doc.saveIncr();doc.close()

def chart_png(browser,fig,width=1500,height=520):
    page=browser.new_page(viewport={'width':width,'height':height});page.set_content('<div id="plot"></div>');page.add_script_tag(content=get_plotlyjs());data=json.loads(fig.to_json());data['layout'].update(width=width,height=height,font=dict(family='Arial',size=19,color='#29405b'),title=dict(text=fig.layout.title.text,x=.025,font_size=23),margin=dict(l=110,r=55,t=65,b=110),legend=dict(orientation='h',y=-.27,font_size=15))
    url=page.evaluate('''async a=>{await Plotly.newPlot('plot',a.data,a.layout,{staticPlot:true});return await Plotly.toImage('plot',{format:'png',width:a.layout.width,height:a.layout.height,scale:2})}''',data);page.close();return base64.b64decode(url.split(',',1)[1])

def export(executable=None,notes_json=None):
    t=load_data();r,m,d=enrich(t);stamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC');notes={}
    if notes_json:
        payload=json.loads(Path(notes_json).read_text());notes=payload.get('notes',payload)
        if not isinstance(notes,dict) or any(k not in [f'why-{i}' for i in range(5)]+[f'capa-{i}' for i in range(7)] or not isinstance(v,str) for k,v in notes.items()):raise ValueError('Invalid notes JSON')
    c.OUTPUT.mkdir(exist_ok=True);manifest=dict(exported_utc=stamp,format='one complete tab per variable-height PDF page',sections=[],notes='supplied JSON' if notes else 'blank template',dataset_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(c.RAW.glob('*.csv'))})
    sections=[('overview','Manufacturing Overview',{}),('eda','Data Overview & EDA',{}),('yield','Yield & Defect Analysis',{}),('spc','SPC & Process Capability',{}),('root','Root Cause Investigation',{})]
    appendix=[('spc','SPC Appendix | Reference display',{'s-view':'Reference window'}),('spc','SPC Appendix | Disturbance display',{'s-view':'Custom window','s-start':1800}),('spc','SPC Appendix | Post-action display',{'s-view':'Post-action window'}),('spc','SPC Appendix | Full history',{'s-view':'Full history'})]
    with sync_playwright() as p,tempfile.TemporaryDirectory(prefix='quality-v6-') as tmp:
        opts=dict(headless=True,args=['--no-sandbox'])
        if executable:opts['executable_path']=executable
        browser=p.chromium.launch(**opts);tmp=Path(tmp);parts=[];snapshots=[]
        cover=header('Full Dashboard Report')+f'<div class="report-scope">Exported {stamp}. Simulated data; specifications and limits are illustrative.</div><h2>Why this analysis?</h2><p>A change in yield shows that performance has moved, but not where the problem started. This project connects production outcomes, process measurements and equipment history to define a focused investigation.</p><div class="two-grid"><div class="panel"><h3>Contents</h3><p>1. Manufacturing Overview<br>2. Data Overview &amp; EDA<br>3. Yield &amp; Defect Analysis<br>4. SPC &amp; Process Capability<br>5. Root Cause Investigation</p></div><div class="panel"><h3>How to read this PDF</h3><p>Each tab occupies one variable-height page. Scroll and zoom to inspect the original website layout. The eight-page portfolio is the print-friendly summary.</p><p>The appendix retains reference, disturbance, post-action and full-history SPC displays.</p></div></div><h3>Export scope</h3><p>All products, lots and run-end dates unless stated otherwise. Default EDA/investigation process: flip-chip attach. Default SPC: E09A-H2, all periods, first-signal display. Technical schema, dictionary and methods are expanded. Full data remains available in the live website, not printed as thousands of rows.</p><p>5 Whys/CAPA reflect this export session: '+('supplied notes' if notes else 'blank template; no investigation answers invented')+'. Before/after contrasts are descriptive, not causal proof.</p>'
        path=tmp/'cover.pdf';snap,h=tall_page(browser,cover,path,notes);snapshots.append(snap);parts.append(('Context & Scope',path))
        for index,(key,title,state) in enumerate(sections+appendix):
            print('Exporting one-page tab:',title,flush=True);body=render(key,t,r,m,d,state)
            if key=='eda':body=body.replace('<div id="explorer-status" role="status"></div>','<p>Live website: search, sort, paginate and download selected/full table CSV. Source rows are not expanded into this report.</p>')
            if index>=5:
                from bs4 import BeautifulSoup
                soup=BeautifulSoup(body,'html.parser');items=[]
                for selector in ['.insight','.kpi-grid','.scope']:
                    el=soup.select_one(selector)
                    if el:items.append(str(el))
                items.extend(str(el) for el in soup.select('.chart-card')[:2]);body='<h2>'+H(title)+'</h2>'+''.join(items)
            scope='All products, lots and run-end dates; default page selections.'
            if key=='spc':scope='Flip-chip attach | E09A-H2 | All periods | display '+state.get('s-view','First signal')+(f' starting at {state["s-start"]}' if 's-start' in state else '')+'. Frozen limits unchanged by display.'
            if key=='root':scope+=' Assembly cohort threshold 98%. Notes '+('supplied' if notes else 'not recorded')+'.'
            body='<div id="'+key+'"></div>'+header(c.TITLE)+f'<div class="report-scope"><b>Scope:</b> {H(scope)}<br><b>Exported:</b> {stamp} | Simulated data.</div>'+body
            if key=='yield':body+='<p class="period-note">Colored windows are predefined simulation periods, not evidence of verified corrective-action effectiveness.</p>'
            path=tmp/f'{index:02}.pdf';snap,height=tall_page(browser,body,path,notes);snapshots.append(snap);parts.append((title,path));manifest['sections'].append(dict(title=title,scope=scope,pages=1,height_css_px=height))
        merge(parts,c.OUTPUT/'full_dashboard_report.pdf')
        from reporting.src.portfolio import create_portfolio
        create_portfolio(t,r,m,d,browser,c.OUTPUT/'portfolio_summary.pdf')
        browser.close()
    bodies=[re.search(r'<body[^>]*>(.*)</body>',doc,re.S).group(1) for doc in snapshots]
    keys=['overview','eda','yield','spc','root'];titles=[v[1] for v in sections]
    nav='<nav class="quick-nav" aria-label="Quick navigation">'+''.join(f'<a href="#{key}">{title}</a>' for key,title in zip(keys,titles))+'</nav>'
    main=''.join(f'<section class="report-section" id="{key}">{body}<p><a href="#top">Back to quick navigation</a></p></section>' for key,body in zip(keys,bodies[1:6]));appx='<section class="report-section" id="appendix"><h2>Appendix | Selected SPC states</h2>'+''.join(bodies[6:])+'</section>'
    css=(c.ROOT/'reporting/assets/style.css').read_text()+FULL_CSS+'body{width:auto!important;max-width:1400px;margin:auto!important;padding:25px!important}.report-section{margin:35px 0}.quick-nav{position:sticky;top:0;z-index:10;background:#f1f5fa;padding:12px 0}.model-svg{min-width:0!important}'
    offline='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Semiconductor Quality Analytics V6</title><style>'+css+'</style><body><div id="top">'+bodies[0]+nav+'</div><div class="notice"><a href="portfolio_summary.pdf">Portfolio summary PDF</a> | <a href="full_dashboard_report.pdf">Full dashboard PDF</a></div>'+main+appx+f'<footer>{H(c.AUTHOR)}</footer></body></html>'
    offline=re.sub(r'<script\b[^>]*>.*?</script>','',offline,flags=re.S);(c.OUTPUT/'preview_report.html').write_text(offline,encoding='utf-8')
    (c.OUTPUT/'dashboard.html').write_text(offline,encoding='utf-8')
    short=PdfReader(str(c.OUTPUT/'portfolio_summary.pdf'));full=PdfReader(str(c.OUTPUT/'full_dashboard_report.pdf'))
    assert len(short.pages)==8 and len(full.pages)==10
    for reader in [short,full]:
        for page in reader.pages:assert c.AUTHOR in page.extract_text()
    manifest.update(summary_pages=8,full_pages=10,footer_verified=True,live_deployment=False)
    (c.OUTPUT/'export_manifest.json').write_text(json.dumps(manifest,indent=2));print('Created 8-page portfolio and 10-page full report (cover + 5 complete tabs + 4 appendix states).',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--browser-executable',default=os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH'));parser.add_argument('--notes-json');args=parser.parse_args();export(args.browser_executable,args.notes_json)
