"""Explicit deterministic synthetic generation; never invoked by the web app."""
import argparse,time
from pathlib import Path
import numpy as np
import pandas as pd
from config import settings as c

def generate(base=c.ROOT,overwrite=False,bias_sigma=2.5):
    raw=Path(base)/'data/raw';ref=Path(base)/'data/reference'
    paths=[(raw if n in c.RAW_NAMES else ref)/f'{n}.csv' for n in c.RAW_NAMES+c.REF_NAMES]
    if any(p.exists() for p in paths) and not overwrite:raise FileExistsError('Existing or partial data; use --overwrite explicitly')
    started=time.perf_counter();rng=np.random.default_rng(c.SEED)
    steps=pd.DataFrame(c.STEPS,columns=['process_id','process_name','stage','unit_level','parameter','unit','target','sigma','lsl','usl']);steps['sequence']=np.arange(1,13)
    eq=[]
    for i,s in enumerate(steps.itertuples()):
        for machine in range(1 if i<8 else 2):
            equipment=f'E{i+1:02}' if i<8 else f'E{i+1:02}{chr(65+machine)}'
            kind='chamber' if i<8 else 'head' if i==8 else 'station' if i<11 else 'test_site';suffix={'chamber':'C','head':'H','station':'S','test_site':'T'}[kind]
            for j in [1,2]:eq.append(dict(subdivision_id=f'{equipment}-{suffix}{j}',equipment_id=equipment,subdivision_type=kind,process_id=s.process_id))
    eq=pd.DataFrame(eq)
    lots=pd.DataFrame(dict(lot_id=[f'L{i+1:03}' for i in range(c.N_LOTS)],product=[c.PRODUCTS[i%4] for i in range(c.N_LOTS)],start_time=pd.date_range('2026-01-05',periods=c.N_LOTS,freq='18h')))
    lots['period']=np.select([lots.index<40,lots.index<90],c.PERIODS[:2],default=c.PERIODS[2]);lots['material_batch']=[f'MAT{i//5+1:03}' for i in range(c.N_LOTS)]
    w=lots.loc[lots.index.repeat(c.WAFERS_PER_LOT)].reset_index(drop=True);w.insert(0,'wafer_id',[f'W{i+1:05}' for i in range(len(w))]);w['wafer_slot']=np.tile(np.arange(1,26),c.N_LOTS);w.start_time+=pd.to_timedelta((w.wafer_slot-1)*15,unit='m')
    def physical(frame):
        frame=frame.reset_index(drop=True).copy();frame['subdivision_id']=''
        for step,g in frame.groupby('process_id',sort=False):frame.loc[g.index,'subdivision_id']=rng.choice(eq.loc[eq.process_id.eq(step),'subdivision_id'],len(g))
        meta=eq.set_index('subdivision_id');frame['equipment_id']=frame.subdivision_id.map(meta.equipment_id)
        lot=frame.lot_id.str[1:].astype(int).to_numpy();dist=(lot>40)&(lot<91);progress=np.clip((lot-40)/50,0,1)
        drift=frame.subdivision_id.eq('E09A-H2').to_numpy()*dist*progress*6
        spread=np.where(frame.subdivision_id.eq('E10A-S2')&dist,3.,1.)
        bias=frame.subdivision_id.eq('E11A-S2').to_numpy()*dist*bias_sigma
        frame['latent_value']=frame.target+frame.sigma*(rng.normal(size=len(frame))*spread+drift)
        frame['measurement_bias']=frame.sigma*bias;frame['measurement_noise']=frame.sigma*rng.normal(0,.1,len(frame))
        frame['value']=frame.latent_value+frame.measurement_bias+frame.measurement_noise
        frame['risk']=drift+spread-1
        frame['passed']=(rng.random(len(frame))>np.clip(.0015+.025*frame.risk,0,1)).astype(int)
        frame['end_time']=frame.start_time+pd.Timedelta(hours=2)
        frame['shift']=np.where(frame.start_time.dt.hour<12,'Day','Night');frame['recipe_revision']='R1'
        return frame
    fab=w[['wafer_id','lot_id','product','period','material_batch','start_time']].merge(steps[steps.unit_level.eq('wafer')],how='cross');fab['package_id']='';fab.start_time+=pd.to_timedelta((fab.sequence-1)*2,unit='h');fab=physical(fab)
    w['fab_pass']=w.wafer_id.map(fab.groupby('wafer_id').passed.min());w['fab_complete_time']=w.start_time+pd.Timedelta(hours=16);w['dies_tested']=500;w['good_dies']=rng.binomial(500,.96,len(w))
    eligible=w[w.fab_pass.eq(1)].reset_index(drop=True);p=eligible.iloc[rng.choice(len(eligible),c.N_PACKAGES,replace=True)][['wafer_id','lot_id','product','period','material_batch','fab_complete_time']].reset_index(drop=True)
    p.insert(0,'package_id',[f'PK{i+1:06}' for i in range(len(p))]);p['die_site']=p.groupby('wafer_id').cumcount()+1;p['start_time']=p.fab_complete_time+pd.Timedelta(hours=24)+pd.to_timedelta(p.die_site*2,unit='m');p=p.drop(columns='fab_complete_time')
    assy=p[['package_id','wafer_id','lot_id','product','period','material_batch','start_time']].merge(steps[steps.stage.eq('Assembly')],how='cross');assy.start_time+=pd.to_timedelta((assy.sequence-9)*2,unit='h');assy=physical(assy)
    p['assembly_pass']=p.package_id.map(assy.groupby('package_id').passed.min());p['assembly_complete_time']=p.start_time+pd.Timedelta(hours=6)
    final=p[p.assembly_pass.eq(1)][['package_id','wafer_id','lot_id','product','period','material_batch','assembly_complete_time']].rename(columns={'assembly_complete_time':'start_time'}).merge(steps[steps.stage.eq('Test')],how='cross');final=physical(final)
    final['risk']=final.package_id.map(assy.groupby('package_id').risk.max());final['passed']=(rng.random(len(final))>np.clip(.025+.035*final.risk,0,1)).astype(int)
    runs=pd.concat([fab,assy,final],ignore_index=True);runs.insert(0,'run_id',[f'R{i+1:07}' for i in range(len(runs))]);runs['measurement_system_id']='MS-'+runs.process_id
    pn=pd.to_numeric(runs.package_id.str[2:],errors='coerce').fillna(0).astype(int)
    selected=runs.unit_level.eq('wafer')|(runs.process_id.isin(['S09','S10'])&pn.mod(2).eq(0))|(runs.process_id.isin(['S11','S12'])&pn.mod(4).eq(0))
    m=runs.loc[selected,['run_id','parameter','unit','end_time','value','latent_value','measurement_bias','measurement_noise','measurement_system_id']].rename(columns={'end_time':'timestamp'}).copy();m.insert(0,'measurement_id',[f'M{i+1:07}' for i in range(len(m))])
    catalog=pd.DataFrame([('D01','Film anomaly','S01'),('D02','Pattern bridge','S02'),('D03','Etch nonuniformity','S03'),('D04','Placement anomaly','S09'),('D05','Underfill void','S10'),('D06','Warpage anomaly','S11'),('D07','Electrical failure symptom','S12')],columns=['defect_code','defect_name','process_id'])
    possible=runs[runs.process_id.isin(catalog.process_id)];weights=1+5*possible.risk
    idx=rng.choice(possible.index,1200,replace=False,p=weights/weights.sum());d=runs.loc[idx,['run_id','process_id','end_time']].rename(columns={'end_time':'timestamp'}).reset_index(drop=True);d.insert(0,'defect_id',[f'DF{i+1:05}' for i in range(len(d))]);d['defect_code']=d.process_id.map(catalog.set_index('process_id').defect_code);d=d.drop(columns='process_id')
    first=runs[runs.process_id.eq('S12')][['package_id','run_id','end_time','passed','subdivision_id']].rename(columns={'end_time':'timestamp','passed':'test_pass'});first['attempt']=1
    failed=first[first.test_pass.eq(0)];ret=failed[rng.random(len(failed))<.7].copy();ret['attempt']=2;ret.timestamp+=pd.Timedelta(hours=4);ret['test_pass']=(rng.random(len(ret))<.35).astype(int)
    tests=pd.concat([first,ret],ignore_index=True);tests.insert(0,'test_id',[f'T{i+1:07}' for i in range(len(tests))]);tests['failure_bin']=np.where(tests.test_pass.eq(1),'PASS','Electrical / functional screen')
    ev=pd.DataFrame([dict(event_id=f'EV{i+1:03}',subdivision_id=sub,timestamp=lots.loc[90,'start_time']+pd.Timedelta(hours=40),event_type=kind) for i,(sub,kind) in enumerate([('E09A-H2','Alignment calibration'),('E10A-S2','Dispense maintenance'),('E11A-S2','Measurement calibration')])])
    cols=['run_id','wafer_id','package_id','lot_id','process_id','equipment_id','subdivision_id','start_time','end_time','passed','period','shift','recipe_revision','material_batch','measurement_system_id']
    tables=dict(lots=lots,wafers=w,packages=p,process_runs=runs[cols],measurements=m,defects=d,test_results=tests,equipment_events=ev,process_steps=steps,equipment=eq,defect_catalog=catalog)
    raw.mkdir(parents=True,exist_ok=True);ref.mkdir(parents=True,exist_ok=True)
    for name,df in tables.items():df.to_csv((raw if name in c.RAW_NAMES else ref)/f'{name}.csv',index=False);print(f'{name}: {len(df):,}')
    print(f'Generation: {time.perf_counter()-started:.2f}s; seed {c.SEED}');return tables

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--overwrite',action='store_true');args=parser.parse_args()
    if not args.overwrite and all(((c.RAW if n in c.RAW_NAMES else c.REF)/f'{n}.csv').exists() for n in c.KEYS):
        from src.data import load_data
        for name,df in load_data().items():print(name,len(df))
        print('Validated existing CSVs; no regeneration.')
    else:generate(overwrite=args.overwrite)
