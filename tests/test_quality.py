import copy,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from pypdf import PdfReader
from config import settings as c
from src import analysis as a
from src.data import validate
from tabs.views import render

@pytest.mark.parametrize('name',c.KEYS)
def test_primary_grains(data,name):
    assert data[name][c.KEYS[name]].is_unique

@pytest.mark.parametrize('name,expected',[('lots',120),('wafers',3000),('packages',24000),('measurements',59898),('defects',1200)])
def test_dataset_sizes(data,name,expected):assert len(data[name])==expected

def test_integrity(data):assert validate(data)

def test_yield_reconciliation(context):
    t,r,m,d=context;met=a.metrics(t,r);p=a.periods(t['packages'])
    assert p.passed.tolist()==[7925,9702,5939]
    assert p.total.tolist()==[7964,10061,5975]
    assert p.failed.sum()==434
    assert met['assembly']['rate']==pytest.approx(23566/24000)
    assert a.period_delta(t['packages'])==pytest.approx(100*(9702/10061-7925/7964))

def test_zero_denominator():assert a.rate(0,0) is None

def test_empty_filters(context):
    t,r,m,d=context;rr=a.filter_runs(r,product='Compute B',lot='L001');met=a.metrics(t,rr)
    assert rr.empty and met['assembly']['rate'] is None
    assert a.period_delta(met['packages']) is None

def test_retest_denominator(context):
    t,r,m,d=context;met=a.metrics(t,r);ret=t['test_results'][t['test_results'].attempt.eq(2)]
    assert met['retest']['total']==len(ret)
    assert met['retest']['passed']==ret.test_pass.sum()

def test_event_rate_exposure(context):
    t,r,m,d=context;rr=r[r.process_id.eq('S09')];dd=d[d.run_id.isin(rr.run_id)];rates=a.event_rates(dd,rr,'subdivision_id')
    assert rates.runs.sum()==len(rr) and rates.events.sum()==len(dd)
    assert np.allclose(rates.events_per_100_runs,100*rates.events/rates.runs)

def test_pareto(context):
    p=a.pareto(context[3]);assert p.events.sum()==1200 and p.cumulative_pct.iloc[-1]==100

def test_frozen_limits_formula():
    x=np.random.default_rng(2).normal(size=100);z=a.imr(x);mr=np.abs(np.diff(x[:40])).mean()
    assert z['cl']==pytest.approx(x[:40].mean());assert z['sigma']==pytest.approx(mr/1.128)
    assert z['mr_ucl']==pytest.approx(3.267*mr)

@pytest.mark.parametrize('values,status',[([], 'insufficient samples'),([1]*10,'insufficient samples'),([1]*100,'zero variation')])
def test_spc_edge_cases(values,status):assert a.imr(values)['status']==status

@pytest.mark.parametrize('values',[[1,float('nan')],[1,float('inf')]])
def test_nonfinite_rejected(values):
    with pytest.raises(ValueError):a.imr(values)

@pytest.mark.parametrize('limits',[(1,1),(2,1),(float('nan'),2)])
def test_invalid_specs(limits):
    with pytest.raises(ValueError):a.capability([1,2,3],*limits)

def test_benchmark_formula():
    x,z=a.benchmark();assert z['cp'] is not None and z['cpk'] is not None
    assert z['cp']==pytest.approx(10/(6*z['sigma']))
    assert z['cpk']==pytest.approx(min(106-x.mean(),x.mean()-96)/(3*z['sigma']))

def test_unstable_withheld(context):
    m=context[2];x=m[m.subdivision_id.eq('E09A-H2')].sort_values(['timestamp','measurement_id']);z=a.capability(x.value,-10,10)
    assert z['cp'] is None and z['status']=='detected instability'

@pytest.mark.parametrize('view',['First signal','Reference window','Post-action window','Full history','Custom window'])
def test_display_invariance(context,view):
    x=context[2];x=x[x.subdivision_id.eq('E09A-H2')].sort_values(['timestamp','measurement_id']);z=a.imr(x.value);before=(z['cl'],z['ucl'],z['lcl']);left,right=a.display_bounds(x,z,view,1800)
    assert 0<=left<right<=len(x)
    assert right-left<=250 if view!='Full history' else right-left==len(x)
    assert before==(z['cl'],z['ucl'],z['lcl'])

def test_display_extremes(context):
    x=context[2];x=x[x.subdivision_id.eq('E09A-H2')];z=a.imr(x.value)
    assert a.display_bounds(x,z,'Custom window',-999)[0]==0
    assert a.display_bounds(x,z,'Custom window',10**30)[1]==len(x)
    assert a.display_bounds(x.iloc[:0],a.imr([]),'First signal')==(0,0)
    with pytest.raises(ValueError):a.display_bounds(x,z,'invalid')

@pytest.mark.parametrize('page',['overview','eda','yield','spc','root'])
def test_page_renderer(context,page):
    body=render(page,*context);assert '<h2>' in body
    if page!='overview':assert 'application/json' in body

def test_approved_overview_text(context):
    body=render('overview',*context)
    for text in ['Build transistors and interconnects on silicon.','Engineers monitor','Screened products meeting applicable release requirements.','Two Electrical Interfaces','Die-to-substrate:','Package-to-board:','Surface Mount Technology']:
        assert text in body
    assert 'Process description' not in body

def test_no_silent_regeneration(data):
    from src.generate_data import generate
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in c.RAW.glob('*.csv')}
    with pytest.raises(FileExistsError):generate()
    assert before=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in c.RAW.glob('*.csv')}

def test_seed_reproducibility(tmp_path,data):
    from src.generate_data import generate
    generate(tmp_path)
    for name in c.KEYS:
        folder='raw' if name in c.RAW_NAMES else 'reference';expected=c.ROOT/'data'/folder/(name+'.csv');actual=tmp_path/'data'/folder/(name+'.csv')
        assert hashlib.sha256(actual.read_bytes()).digest()==hashlib.sha256(expected.read_bytes()).digest()

@pytest.mark.parametrize('name,pages',[('portfolio_summary',8),('full_dashboard_report',10)])
def test_pdf_deliverables(name,pages):
    pdf=PdfReader(str(c.OUTPUT/(name+'.pdf')));assert len(pdf.pages)==pages
    for page in pdf.pages:
        text=page.extract_text() or '';assert c.AUTHOR in text and len(text)>60
        if name=='portfolio_summary': assert float(page.mediabox.width)>float(page.mediabox.height)

def test_full_pdf_scope():
    text=' '.join(p.extract_text() for p in PdfReader(str(c.OUTPUT/'full_dashboard_report.pdf')).pages)
    for value in ['Manufacturing Overview','Data Overview & EDA','Yield & Defect Analysis','SPC & Process Capability','Root Cause Investigation','Effectiveness criteria','Not recorded','Metric definitions','Post-action display','Full history']:
        assert value in text

def test_summary_context():
    text=PdfReader(str(c.OUTPUT/'portfolio_summary.pdf')).pages[0].extract_text();assert 'The problem' in text and 'What this portfolio demonstrates' in text
