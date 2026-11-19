import pytest
from src.explore import eda_scope,data_view
from src.model import NODES,model_html
from app import data_response
from bs4 import BeautifulSoup
from config import settings as c

def test_model_schema(data):
    assert {x[0] for x in NODES}==set(data)
    svg=BeautifulSoup(model_html(),'html.parser');assert len(svg.select('[data-entity]'))==11
    assert 'package_id*' in svg.get_text() and '0..1' in svg.get_text()

@pytest.mark.parametrize('stage,expected',[('Fabrication','S01'),('Assembly','S09'),('Test','S12')])
def test_stage_cascade(context,stage,expected):
    t,r,m,d=context;rr,x,opts=eda_scope(t,r,m,{'e-stage':stage,'e-process':'invalid'})
    assert opts['process']==expected and x.stage.eq(stage).all()

def test_subdivision_and_period(context):
    t,r,m,d=context;rr,x,opts=eda_scope(t,r,m,{'e-process':'S09','e-equipment':'E09A','e-sub':'E09A-H2','e-period':'Disturbance'})
    assert len(x)==1267 and x.subdivision_id.eq('E09A-H2').all() and x.period.eq('Disturbance').all()

def test_invalid_subdivision_resets(context):
    t,r,m,d=context;rr,x,opts=eda_scope(t,r,m,{'e-process':'S01','e-equipment':'E09A','e-sub':'E09A-H2'})
    assert opts['equipment']=='All' and opts['sub']=='All' and x.process_id.eq('S01').all()

@pytest.mark.parametrize('name',list(c.KEYS))
def test_selected_data_view(context,name):
    t,r,m,d=context;df=data_view(t,r,m,{'e-process':'S09'},name)
    assert len(df)<=len(t[name])

def test_search_sort_full(context):
    t,r,m,d=context;df=data_view(t,r,m,{},'measurements','full','MS-S09','value',True)
    assert len(df)==12000 and df.value.is_monotonic_decreasing
    assert data_view(t,r,m,{},'measurements','full','NO_SUCH_VALUE').empty

def test_pagination_and_csv():
    p={'table':'measurements','state':{},'size':10,'page':2};x=data_response(p)
    assert x['start']==11 and x['end']==20 and len(x['rows'])==10 and x['total']==12000
    assert len(data_response(p,True).decode('utf-8-sig').splitlines())==12001
    p['page']=10**10;assert data_response(p)['page']==1200

def test_offline_quick_navigation():
    soup=BeautifulSoup((c.OUTPUT/'preview_report.html').read_text(),'html.parser')
    assert len(soup.select('.quick-nav a'))==5
    for key in ['overview','eda','yield','spc','root','appendix']:assert soup.select_one('#'+key)
    assert len(soup.select('#appendix .report-head'))==4
