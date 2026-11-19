"""Local portfolio server. Optional Dash host; standard-library fallback is tested.

Run python app.py. No startup data generation, network data access or authentication.
"""
import argparse,json,mimetypes,sys
from functools import lru_cache
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from config import settings as c
from src.data import load_data,enrich
from tabs.views import render,PAGES,H

@lru_cache(maxsize=1)
def context():
    t=load_data();return (t,*enrich(t))

def shell():
    nav=''.join(f'<button id="tab-{key}" data-page="{key}">{H(label)}</button>' for key,label in PAGES)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{H(c.TITLE)}</title><link rel="stylesheet" href="/assets/style.css"><script src="/assets/plotly.min.js"></script></head><body><header class="masthead"><div><div class="eyebrow">Process intelligence / educational portfolio</div><h1>{H(c.TITLE)}</h1><div class="subtitle">Process Monitoring, Yield Analysis &amp; Quality Investigation</div></div><div class="badge"><strong>SIMULATED DATA</strong>120 lots · 24,000 packages · 12 processes</div></header><div class="disclaimer">Independent portfolio project. All manufacturing data is simulated; specifications and limits are illustrative. Not an Intel application.</div><nav class="nav" aria-label="Dashboard pages">{nav}</nav><main><div class="context"><strong>The engineering question:</strong> When yield changes, where should the investigation begin? This portfolio connects production outcomes, process behavior and verification planning.</div><div class="actions"><button class="secondary" data-action="reset">Reset filters</button><a href="/output/portfolio_summary.pdf">Portfolio PDF</a><a href="/output/full_dashboard_report.pdf">Full dashboard PDF</a></div><p class="mobile-note">Charts scroll within their cards on narrow screens.</p><div id="tab-content"></div><div id="status" class="status" role="status" aria-live="polite"></div></main><footer>{H(c.AUTHOR)}</footer><script src="/assets/app.js"></script></body></html>'''

def page_response(payload):
    if not isinstance(payload,dict):raise ValueError('Invalid request')
    page=payload.get('page','overview');state=payload.get('state',{})
    if not isinstance(state,dict) or len(state)>40 or any(not isinstance(v,(str,int,float)) or len(str(v))>100 for v in state.values()):raise ValueError('Invalid filter state')
    t,r,m,d=context()
    for key in ['e-process','s-process','r-process']:
        if key in state and state[key] not in set(t['process_steps'].process_id):raise ValueError('Unknown process')
    return {'body':render(page,t,r,m,d,state)}

def data_response(payload,csv=False):
    from src.explore import data_view
    t,r,m,d=context();state=payload.get('state',{})
    if not isinstance(state,dict):raise ValueError('Invalid state')
    df=data_view(t,r,m,state,payload.get('table','measurements'),payload.get('scope','selected'),str(payload.get('search',''))[:100],payload.get('sort',''),bool(payload.get('descending',False)))
    if csv:return df.to_csv(index=False).encode('utf-8-sig')
    size=min(100,max(10,int(payload.get('size',25))));pages=max(1,(len(df)+size-1)//size);page=min(pages,max(1,int(payload.get('page',1))));start=(page-1)*size
    import json
    return dict(columns=list(df.columns),rows=json.loads(df.iloc[start:start+size].to_json(orient='records',date_format='iso')),total=len(df),page=page,pages=pages,size=size,start=start+1 if len(df) else 0,end=min(start+size,len(df)))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=urlparse(self.path).path
        if path in ['/','/dashboard']:
            self.send_bytes(shell().encode(),'text/html; charset=utf-8');return
        if path=='/health':self.send_bytes(b'{"status":"ok"}','application/json');return
        if not path.startswith(('/assets/','/output/')):self.send_error(404);return
        target=(c.ROOT/path.lstrip('/')).resolve()
        if c.ROOT not in target.parents or not target.is_file():self.send_error(404);return
        self.send_bytes(target.read_bytes(),mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
    def do_POST(self):
        path=urlparse(self.path).path
        if path not in ['/api/page','/api/data','/api/csv']:self.send_error(404);return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<20000:raise ValueError('Invalid request length')
            payload=json.loads(self.rfile.read(length))
            if path=='/api/csv':self.send_bytes(data_response(payload,True),'text/csv; charset=utf-8');return
            result=page_response(payload) if path=='/api/page' else data_response(payload);self.send_bytes(json.dumps(result).encode(),'application/json')
        except (ValueError,KeyError,TypeError) as e:self.send_bytes(json.dumps({'error':str(e)}).encode(),'application/json',400)
    def send_bytes(self,body,content_type,status=200):
        self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    def log_message(self,fmt,*args):print(fmt%args,flush=True)

def create_dash_app():
    """Optional Dash hosting adapter. Same tested renderer/API; requires dash."""
    from dash import Dash,html
    from flask import Response,request,send_from_directory
    app=Dash(__name__,title=c.TITLE)
    app.layout=html.Iframe(src='/dashboard',style={'width':'100%','height':'100vh','border':'0'},title=c.TITLE)
    @app.server.route('/dashboard')
    def dashboard():return Response(shell(),mimetype='text/html')
    @app.server.route('/api/page',methods=['POST'])
    def api():
        try:return page_response(request.get_json())
        except (ValueError,KeyError,TypeError) as e:return {'error':str(e)},400
    @app.server.route('/api/data',methods=['POST'])
    def data_api():return data_response(request.get_json())
    @app.server.route('/api/csv',methods=['POST'])
    def csv_api():return Response(data_response(request.get_json(),True),mimetype='text/csv')
    @app.server.route('/output/<path:name>')
    def output(name):return send_from_directory(c.OUTPUT,name)
    return app

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--dash',action='store_true',help='Optional Dash host (install requirements-dash.txt)');parser.add_argument('--port',type=int,default=c.PORT);args=parser.parse_args()
    context()
    if args.dash:create_dash_app().run(host=c.HOST,port=args.port,debug=False)
    else:
        print(f'Local dashboard: http://{c.HOST}:{args.port} (Ctrl+C to stop)',flush=True)
        try:ThreadingHTTPServer((c.HOST,args.port),Handler).serve_forever()
        except KeyboardInterrupt:pass
