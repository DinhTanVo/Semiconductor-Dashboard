import numpy as np
import pandas as pd
import pytest
from src import figures as live
from reporting.src import figures as report
@pytest.mark.parametrize('engine',[live,report])
@pytest.mark.parametrize('values,expected',[([1,2,6],3),([4,4],4),([1,float('nan'),float('inf'),3],2)])
def test_selected_mean(engine,values,expected):
 f=engine.histogram(pd.DataFrame({'value':values,'unit':['um']*len(values)}),-10,10)
 assert f.layout.meta['selected_mean']==pytest.approx(expected)
 assert any(s.x0==pytest.approx(expected) and s.line.color==engine.C['teal'] for s in f.layout.shapes)
 assert any('Mean' in t.name for t in f.data)
@pytest.mark.parametrize('engine',[live,report])
def test_no_mean_for_invalid_data(engine):
 f=engine.histogram(pd.DataFrame({'value':[float('nan'),float('inf')]}))
 assert not f.layout.shapes
