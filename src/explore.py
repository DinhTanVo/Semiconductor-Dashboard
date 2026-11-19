"""One filter definition shared by EDA charts, data viewer and CSV export."""
import pandas as pd
from config import settings as c
from src.analysis import filter_runs

def eda_scope(t,r,m,state):
    steps=t['process_steps'];stage=state.get('e-stage','All')
    available=steps if stage=='All' else steps[steps.stage.eq(stage)]
    if available.empty:raise ValueError('Unknown manufacturing stage')
    process=state.get('e-process','S09')
    if process not in set(available.process_id):process=available.process_id.iloc[0]
    eq=sorted(r.loc[r.process_id.eq(process),'equipment_id'].unique());equipment=state.get('e-equipment','All')
    if equipment not in eq:equipment='All'
    rr=filter_runs(r,state.get('e-product','All'),process,equipment)
    sub_options=sorted(r.loc[r.process_id.eq(process)&(r.equipment_id.eq(equipment) if equipment!='All' else True),'subdivision_id'].unique());sub=state.get('e-sub','All')
    if sub not in sub_options:sub='All'
    if sub!='All':rr=rr[rr.subdivision_id.eq(sub)]
    period=state.get('e-period','All')
    if period!='All':rr=rr[rr.period.eq(period)]
    if state.get('e-start'):rr=rr[rr.end_time.ge(pd.Timestamp(state['e-start']))]
    if state.get('e-end'):rr=rr[rr.end_time.lt(pd.Timestamp(state['e-end'])+pd.Timedelta(days=1))]
    x=m[m.run_id.isin(rr.run_id)]
    return rr,x,dict(process=process,equipment=equipment,sub=sub,process_options=[(z.process_id,z.process_name+' | '+z.parameter) for z in available.itertuples()],equipment_options=eq,sub_options=sub_options)

def data_view(t,r,m,state,table='measurements',scope='selected',search='',sort='',descending=False):
    if table not in t:raise ValueError('Unknown table')
    if scope not in ['selected','full']:raise ValueError('Unknown data scope')
    df=t[table]
    if scope=='selected':
        rr,x,opts=eda_scope(t,r,m,state)
        if table=='process_runs':df=df[df.run_id.isin(rr.run_id)]
        elif table=='measurements':df=df[df.measurement_id.isin(x.measurement_id)]
        elif table in ['defects','test_results']:df=df[df.run_id.isin(rr.run_id)]
        elif table=='wafers':df=df[df.wafer_id.isin(rr.wafer_id)]
        elif table=='packages':df=df[df.package_id.isin(rr.package_id)]
        elif table=='lots':df=df[df.lot_id.isin(rr.lot_id)]
        elif table=='equipment_events':df=df[df.subdivision_id.isin(rr.subdivision_id)]
        elif table=='equipment':df=df[df.subdivision_id.isin(rr.subdivision_id)]
        elif table=='process_steps':df=df[df.process_id.eq(opts['process'])]
        elif table=='defect_catalog':df=df[df.process_id.eq(opts['process'])]
    if search:
        mask=pd.Series(False,index=df.index)
        for col in df:mask|=df[col].astype(str).str.contains(str(search)[:100],case=False,regex=False,na=False)
        df=df[mask]
    if sort:
        if sort not in df:raise ValueError('Unknown sort field')
        df=df.sort_values(sort,ascending=not descending,kind='stable')
    return df
