"""Pure, reusable calculations shared by website and both PDFs."""
import numpy as np
import pandas as pd
from scipy.stats import normaltest
from reporting.config import settings as c

def rate(passed,total):return float(passed)/int(total) if total else None

def filter_runs(r,product='All',process='All',equipment='All',lot='All',start=None,end=None):
    x=r
    for col,val in [('product',product),('process_id',process),('equipment_id',equipment),('lot_id',lot)]:
        if val and val!='All':x=x[x[col].eq(val)]
    if start:x=x[x.end_time.ge(pd.Timestamp(start))]
    if end:x=x[x.end_time.lt(pd.Timestamp(end)+pd.Timedelta(days=1))]
    return x

def metrics(t,r):
    w=t['wafers'][t['wafers'].wafer_id.isin(r.wafer_id)];p=t['packages'][t['packages'].package_id.isin(r.package_id)];test=t['test_results'][t['test_results'].run_id.isin(r.run_id)]
    out=dict(wafers=w,packages=p,tests=test)
    for key,df,col in [('fab',w,'fab_pass'),('assembly',p,'assembly_pass'),('final',test[test.attempt.eq(1)],'test_pass'),('retest',test[test.attempt.eq(2)],'test_pass')]:
        out[key]=dict(passed=int(df[col].sum()),total=len(df),rate=rate(df[col].sum(),len(df)))
    return out

def periods(p):
    x=p.groupby('period',observed=True).agg(passed=('assembly_pass','sum'),total=('package_id','size')).reindex(c.PERIODS).dropna().reset_index()
    x['failed']=x.total-x.passed;x['yield']=x.passed/x.total
    for col in ['passed','total','failed']:x[col]=x[col].astype(int)
    return x

def period_delta(p):
    x=periods(p).set_index('period')['yield']
    return float(100*(x['Disturbance']-x['Reference'])) if {'Reference','Disturbance'}.issubset(x.index) else None

def screen_losses(r):
    x=r.groupby('process_name').agg(passed=('passed','sum'),total=('run_id','size')).reset_index();x['failed']=x.total-x.passed;x['failure_rate']=x.failed/x.total
    return x.sort_values('failure_rate',ascending=False)

def event_rates(d,r,group):
    if not d.run_id.isin(r.run_id).all():raise ValueError('Events outside exposure')
    a=r.groupby(group).size().rename('runs').to_frame();a=a.join(d.groupby(group).size().rename('events')).fillna({'events':0}).reset_index();a['events']=a.events.astype(int);a['events_per_100_runs']=100*a.events/a.runs
    return a.sort_values('events_per_100_runs',ascending=False)

def pareto(d):
    x=d.groupby('defect_name').size().sort_values(ascending=False).rename('events').reset_index();x['cumulative_pct']=100*x.events.cumsum()/x.events.sum() if len(x) else pd.Series(dtype=float)
    return x

def imr(values):
    x=np.asarray(values,dtype=float)
    if not np.isfinite(x).all():raise ValueError('Nonfinite values')
    n=len(x);b=min(c.BASELINE_N,n);mr=np.abs(np.diff(x));cl=float(x[:b].mean()) if n else None;mrbar=float(np.abs(np.diff(x[:b])).mean()) if b>1 else None
    status='insufficient samples' if n<c.MIN_SPC_N else 'zero variation' if not mrbar else 'ok'
    sigma=mrbar/c.D2 if mrbar else None;ucl=cl+3*sigma if sigma else None;lcl=cl-3*sigma if sigma else None;mu=c.D4*mrbar if mrbar else None
    bad=((x>ucl)|(x<lcl)) if status=='ok' else np.zeros(n,dtype=bool);mb=mr>mu if status=='ok' else np.zeros(len(mr),dtype=bool)
    return dict(values=x,mr=mr,baseline_n=b,cl=cl,mr_cl=mrbar,sigma=sigma,ucl=ucl,lcl=lcl,mr_ucl=mu,ooc=bad,mr_ooc=mb,status=status)

def capability(values,lsl,usl):
    if not np.isfinite([lsl,usl]).all() or lsl>=usl:raise ValueError('Invalid specifications')
    a=imr(values);x=a['values'];n=len(x);mean=float(x.mean()) if n else None;sd=float(x.std(ddof=1)) if n>1 else None
    p=float(normaltest(x).pvalue) if n>=8 and sd else None
    status='insufficient samples' if n<c.MIN_CAP_N else 'zero variation' if not sd or not a['sigma'] else 'detected instability' if a['ooc'].any() or a['mr_ooc'].any() else 'normality screening failed' if p is None or p<c.ALPHA else 'screening passed; assumptions require review'
    ok=status.startswith('screening passed');sigma=a['sigma']
    return dict(n=n,mean=mean,std=sd,sigma=sigma,normality_p=p,status=status,cp=(usl-lsl)/(6*sigma) if ok else None,cpk=min(usl-mean,mean-lsl)/(3*sigma) if ok else None)

def display_bounds(frame,a,view='First signal',start=1):
    n=len(frame);width=c.DISPLAY_N
    if view not in ['First signal','Reference window','Post-action window','Full history','Custom window']:raise ValueError('Unknown view')
    if not n:return 0,0
    if view=='Full history':return 0,n
    if view=='First signal':
        idx=np.r_[np.flatnonzero(a['ooc']),np.flatnonzero(a['mr_ooc'])+1];left=max(0,int(idx.min())-width//3) if len(idx) else 0
    elif view=='Post-action window':
        idx=np.flatnonzero(frame.period.eq('Post-action').to_numpy());left=max(0,int(idx[0])-width//5) if len(idx) else 0
    elif view=='Custom window':
        try:left=int(float(start))-1
        except (TypeError,ValueError,OverflowError):left=0
    else:left=0
    left=min(max(0,left),max(0,n-width));return left,min(n,left+width)

def benchmark():
    from scipy.stats import norm
    x=norm.ppf((np.arange(100)+.5)/100);x=x[np.random.default_rng(c.SEED).permutation(100)]+100
    return x,capability(x,96,106)
