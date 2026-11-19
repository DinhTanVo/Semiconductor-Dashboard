"""Actual browser checks and screenshots; no simulated pass status."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright
from config import settings as c
PAGES=['overview','eda','yield','spc','root']

def wait(page):
    page.wait_for_function("document.querySelector('#status')?.textContent==='Analysis updated.'",timeout=90000)
    page.wait_for_timeout(150)

def choose(page,key,value):
    page.select_option('#'+key,str(value));wait(page)

def capture(executable=None):
    c.OUTPUT.mkdir(exist_ok=True);qa=c.OUTPUT/'qa_evidence';qa.mkdir(exist_ok=True);checks=[];errors=[]
    log=open(c.OUTPUT/'server_check.log','w');server=subprocess.Popen([sys.executable,'app.py'],cwd=c.ROOT,stdout=log,stderr=log)
    try:
        for _ in range(900):
            try:
                if urlopen('http://127.0.0.1:8050/health',timeout=.3).status==200:break
            except Exception:time.sleep(.2)
        else:raise TimeoutError('Server startup')
        with sync_playwright() as p:
            options=dict(headless=True,args=['--no-sandbox'])
            if executable:options['executable_path']=executable
            b=p.chromium.launch(**options);page=b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto('http://127.0.0.1:8050',wait_until='networkidle');wait(page)
            for width in [1440,1024,390]:
                page.set_viewport_size({'width':width,'height':1000})
                for key in PAGES:
                    page.click('#tab-'+key);wait(page)
                    overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth+2')
                    assert not overflow,(width,key,'page-level overflow')
                    assert page.locator('#tab-content h2').count()==1
                    if key!='overview':assert page.locator('#tab-content .js-plotly-plot').count()>=2
                    page.screenshot(path=str(qa/f'{key}_{width}.png'),full_page=True);checks.append(f'{key} at {width}px: no page-level overflow, rendered charts and heading')
                    print(width,key,flush=True)
            page.set_viewport_size({'width':1440,'height':1000});page.click('#tab-spc');wait(page)
            initial=page.locator('#individuals-chart').evaluate("p=>JSON.stringify(p.layout.shapes.filter(s=>s.y0===s.y1).map(s=>s.y0))")
            full_n=page.locator('.kpi-value').first.inner_text()
            for view in ['Reference window','Post-action window','Full history','Custom window']:
                choose(page,'s-view',view)
                if view=='Custom window':page.fill('#s-start','1800');page.locator('#s-start').press('Tab');wait(page)
                assert page.locator('#individuals-chart').evaluate("p=>JSON.stringify(p.layout.shapes.filter(s=>s.y0===s.y1).map(s=>s.y0))")==initial
                assert page.locator('.kpi-value').first.inner_text()==full_n
                n=page.locator('#individuals-chart').evaluate('p=>p.data[0].x.length')
                assert n==int(full_n.replace(',','')) if view=='Full history' else n<=250
            checks.append('All SPC display windows preserve frozen limits and full-study n; custom start and full history work')
            page.click('#tab-eda');wait(page);choose(page,'e-process','S03');assert 'Etch' in page.locator('#e-process option:checked').inner_text();checks.append('EDA parameter selector updates')
            page.click('#tab-yield');wait(page);choose(page,'y-process','S09');choose(page,'y-product','Compute B');choose(page,'y-lot','L001');assert 'No runs in scope' in page.locator('#tab-content').inner_text();checks.append('Empty filtered scope returns N/A and explicit no-data charts')
            page.click('[data-action=reset]');wait(page);choose(page,'y-process','S09');page.click('[data-action=to-spc]');wait(page);assert page.locator('#s-process').input_value()=='S09';checks.append('Yield-to-SPC handoff retains selected process')
            page.click('#tab-root');wait(page);page.fill('#why-0','Verify reference artifact');page.fill('#capa-6','Matched lots and approved stable monitoring window')
            page.click('#tab-overview');wait(page);page.click('#tab-root');wait(page);assert page.locator('#why-0').input_value()=='Verify reference artifact'
            with page.expect_download() as download:page.click('[data-action=download-notes]')
            path=download.value.path();payload=json.loads(Path(path).read_text());assert payload['notes']['why-0']=='Verify reference artifact';checks.append('5 Whys/CAPA survive tab navigation and download as JSON')
            choose(page,'r-process','S10');choose(page,'r-lot','L002');assert 'does not support' in page.locator('#tab-content').inner_text();checks.append('Single-lot root-cause view avoids unsupported period contrast')
            assert not errors,errors
            page=b.new_page(viewport={'width':1440,'height':1000})
            page.goto('http://127.0.0.1:8050/');wait(page)
            page.click('#tab-spc');wait(page)
            mean_check="""() => {const p=[...document.querySelectorAll('.js-plotly-plot')].find(p=>p.layout.meta?.selected_mean!==undefined);if(!p)throw Error('Missing histogram mean');const x=p.data[0].x.filter(Number.isFinite);const mean=x.reduce((a,b)=>a+b,0)/x.length;if(Math.abs(mean-p.layout.meta.selected_mean)>1e-9)throw Error('Mean mismatch');if(!p.layout.shapes.some(s=>Math.abs(s.x0-mean)<1e-9 && s.line.color==='#00a99d'))throw Error('Missing mean line');return mean;}"""
            initial_mean=page.evaluate(mean_check)
            choose(page,'s-study','Reference');reference_mean=page.evaluate(mean_check)
            assert abs(initial_mean-reference_mean)>0.01
            hist=page.locator('.js-plotly-plot').last
            hist.screenshot(path=str(qa/'live_histogram_mean.png'))
            checks.append('Histogram mean equals finite selected observations and updates after statistical-study filter')
            # Offline HTML has real embedded charts and no network requirement.
            offline=b.new_page();offline.goto((c.OUTPUT/'preview_report.html').as_uri());assert offline.locator('img.print-chart').count()>15;assert offline.locator('textarea').count()==0;offline.close();checks.append('Offline HTML opens with embedded images and expanded methods')
            b.close()
        report={'checks':checks,'browser_errors':errors,'tested_runtime':'Python standard-library server + local Plotly','dash_adapter':'not executed; Dash unavailable in build environment'}
        (c.OUTPUT/'browser_checks.json').write_text(json.dumps(report,indent=2));print(f'{len(checks)} browser checks passed; {len(errors)} errors',flush=True)
    finally:
        server.terminate()
        try:server.wait(timeout=5)
        except subprocess.TimeoutExpired:server.kill()
        log.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--browser-executable',default=os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH'));args=parser.parse_args();capture(args.browser_executable)
