"""Strict grain and conditional genealogy validation."""
from pathlib import Path
import pandas as pd
import numpy as np
from config import settings as c

def validate(t):
    for name,key in c.KEYS.items():
        if name not in t or key not in t[name] or t[name].empty or not t[name][key].is_unique:raise ValueError('Invalid table grain: '+name)
        if t[name].isna().any().any():raise ValueError('Missing required values: '+name)
    def fk(child,col,parent):
        if not t[child][col].isin(t[parent][c.KEYS[parent]]).all():raise ValueError('Invalid FK '+child+'.'+col)
    for a in [('wafers','lot_id','lots'),('packages','wafer_id','wafers'),('packages','lot_id','lots'),('process_runs','wafer_id','wafers'),('process_runs','lot_id','lots'),('process_runs','process_id','process_steps'),('process_runs','subdivision_id','equipment'),('measurements','run_id','process_runs'),('defects','run_id','process_runs'),('defects','defect_code','defect_catalog'),('test_results','package_id','packages'),('test_results','run_id','process_runs'),('equipment_events','subdivision_id','equipment')]:fk(*a)
    w=t['wafers'].set_index('wafer_id');p=t['packages'].set_index('package_id');r=t['process_runs'];s=t['process_steps'].set_index('process_id');eq=t['equipment'].set_index('subdivision_id');rr=r.set_index('run_id')
    if not p.lot_id.eq(p.wafer_id.map(w.lot_id)).all() or p.reset_index().duplicated(['wafer_id','die_site']).any():raise ValueError('Invalid package genealogy')
    if not p.wafer_id.map(w.fab_pass).eq(1).all() or not p.die_site.between(1,p.wafer_id.map(w.good_dies)).all():raise ValueError('Invalid die selection')
    if not r.lot_id.eq(r.wafer_id.map(w.lot_id)).all():raise ValueError('Run lot mismatch')
    pkg=r.process_id.map(s.unit_level).eq('package')
    if not r.loc[~pkg,'package_id'].eq('').all() or not r.loc[pkg,'package_id'].isin(p.index).all():raise ValueError('Invalid conditional package context')
    if not r.loc[pkg,'wafer_id'].eq(r.loc[pkg,'package_id'].map(p.wafer_id)).all():raise ValueError('Package/wafer mismatch')
    if not r.equipment_id.eq(r.subdivision_id.map(eq.equipment_id)).all() or not r.process_id.eq(r.subdivision_id.map(eq.process_id)).all():raise ValueError('Equipment context mismatch')
    if not s.lsl.lt(s.usl).all() or not s.sigma.gt(0).all():raise ValueError('Invalid specs')
    for name,col in [('wafers','fab_pass'),('packages','assembly_pass'),('process_runs','passed'),('test_results','test_pass')]:
        if not t[name][col].isin([0,1]).all():raise ValueError('Invalid pass flag')
    if not w.good_dies.between(0,w.dies_tested).all():raise ValueError('Invalid die count')
    if not r.end_time.gt(r.start_time).all():raise ValueError('Invalid duration')
    order=r.assign(entity=np.where(pkg,r.package_id,r.wafer_id),seq=r.process_id.map(s.sequence)).sort_values(['entity','seq']);prev=order.end_time.groupby(order.entity).shift()
    if order.duplicated(['entity','process_id']).any() or (order.start_time.lt(prev)&prev.notna()).any():raise ValueError('Invalid process chronology')
    if not p.start_time.ge(p.wafer_id.map(w.fab_complete_time)).all():raise ValueError('Package precedes wafer completion')
    m=t['measurements'];d=t['defects'];tests=t['test_results']
    if not m.run_id.is_unique or not np.isfinite(m[['value','latent_value','measurement_bias','measurement_noise']]).all().all() or not np.allclose(m.value,m.latent_value+m.measurement_bias+m.measurement_noise):raise ValueError('Invalid measurement decomposition')
    for col in ['parameter','unit']:
        if not m[col].eq(m.run_id.map(rr.process_id).map(s[col])).all():raise ValueError('Measurement metadata mismatch')
    if not m.timestamp.eq(m.run_id.map(rr.end_time)).all():raise ValueError('Measurement timing')
    cat=t['defect_catalog'].set_index('defect_code')
    if not d.defect_code.map(cat.process_id).eq(d.run_id.map(rr.process_id)).all() or not d.timestamp.eq(d.run_id.map(rr.end_time)).all():raise ValueError('Defect context')
    if not w.fab_pass.eq(w.index.map(r[r.process_id.map(s.stage).eq('Fabrication')].groupby('wafer_id').passed.min())).all():raise ValueError('Fab yield flag mismatch')
    if not p.assembly_pass.eq(p.index.map(r[r.process_id.map(s.stage).eq('Assembly')].groupby('package_id').passed.min())).all():raise ValueError('Assembly yield flag mismatch')
    if tests.duplicated(['package_id','attempt']).any() or not tests.attempt.isin([1,2]).all():raise ValueError('Test attempt grain')
    if not tests.package_id.eq(tests.run_id.map(rr.package_id)).all() or not tests.run_id.map(rr.process_id).eq('S12').all():raise ValueError('Test context')
    first=tests[tests.attempt.eq(1)];ret=tests[tests.attempt.eq(2)];f=first.set_index('package_id')
    if set(first.package_id)!=set(p.index[p.assembly_pass.eq(1)]) or not first.test_pass.eq(first.run_id.map(rr.passed)).all():raise ValueError('First-pass cohort mismatch')
    if not ret.package_id.isin(f.index[f.test_pass.eq(0)]).all() or not ret.timestamp.gt(ret.package_id.map(f.timestamp)).all():raise ValueError('Invalid retest')
    return True

def load_data(base=c.ROOT):
    t={}
    for name in c.KEYS:
        path=Path(base)/'data'/('raw' if name in c.RAW_NAMES else 'reference')/f'{name}.csv'
        if not path.exists():raise FileNotFoundError('Run python -m src.generate_data; missing '+str(path))
        df=pd.read_csv(path,keep_default_na=False)
        for col in ['start_time','end_time','timestamp','fab_complete_time','assembly_complete_time']:
            if col in df:df[col]=pd.to_datetime(df[col],errors='raise')
        t[name]=df
    validate(t);return t

def enrich(t):
    r=t['process_runs'].merge(t['process_steps'],on='process_id',validate='many_to_one').merge(t['lots'][['lot_id','product']],on='lot_id',validate='many_to_one')
    cols=['run_id','wafer_id','package_id','lot_id','process_id','process_name','stage','equipment_id','subdivision_id','period','lsl','usl','target','sigma','product']
    m=t['measurements'].merge(r[cols],on='run_id',validate='many_to_one')
    d=t['defects'].merge(r[cols],on='run_id',validate='many_to_one').merge(t['defect_catalog'][['defect_code','defect_name']],on='defect_code',validate='many_to_one')
    return r,m,d
