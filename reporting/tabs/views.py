"""Presentation content. The approved V2-style hierarchy is kept on Overview."""
import html,json,itertools
import numpy as np
import pandas as pd
from reporting.config import settings as c
from reporting.src import analysis as a,figures as f
H=html.escape
_counter=itertools.count()
PAGES=[('overview','01 Manufacturing Overview'),('eda','02 Data & Scope'),('yield','03 Yield & Defects'),('spc','04 SPC & Capability'),('root','05 Root Cause')]

def heading(n,title,subtitle):
    return f'<div class="section-head"><h2>{H(title)}</h2><p>{H(subtitle)}</p></div>'

def panel(body,cls=''):return f'<div class="panel {cls}">{body}</div>'
def notice(body):return f'<div class="notice">{body}</div>'
def details(title,body):return f'<details class="panel method"><summary>{H(title)}</summary><div>{body}</div></details>'
def kpi(label,value,note=''):return f'<div class="kpi"><div class="kpi-label">{H(label)}</div><div class="kpi-value">{H(str(value))}</div><small>{H(note)}</small></div>'
def pct(x):return 'N/A' if x is None else f'{x:.2%}'
def num(x,d=3):return 'N/A' if x is None or not np.isfinite(x) else f'{x:.{d}f}'
def table(df):
    if df.empty:return '<p class="muted">No supported rows in this scope.</p>'
    return '<div class="table-wrap">'+df.to_html(index=False,border=0,escape=True,na_rep='N/A',float_format=lambda x:f'{x:.3f}')+'</div>'
def chart(fig,key=None):
    key=key or 'chart-'+str(next(_counter));data=fig.to_json().replace('</','<\\/')
    return f'<div class="chart-card"><div class="chart" id="{key}" data-figure="{key}-data"></div><script type="application/json" id="{key}-data">{data}</script></div>'
def select(key,label,options,value='All',all_option=False):
    options=list(options);options=([('All','All')]+options) if all_option else options
    choices=[]
    for option in options:
        v,text=option if isinstance(option,tuple) else (option,option)
        choices.append(f'<option value="{H(str(v),quote=True)}"'+(' selected' if str(v)==str(value) else '')+f'>{H(str(text))}</option>')
    return f'<div><label for="{key}">{H(label)}</label><select id="{key}" data-state="{key}">'+''.join(choices)+'</select></div>'
def input_(key,label,value,typ='number',extra=''):
    return f'<div><label for="{key}">{H(label)}</label><input id="{key}" data-state="{key}" type="{typ}" value="{H(str(value),quote=True)}" {extra}></div>'
def flow(items,note):
    body=''.join(f'<div class="flow-step"><span>0{i+1}</span><strong>{H(title)}</strong><small>{H(desc)}</small></div>' for i,(title,desc) in enumerate(items))
    return f'<div class="stage-visual"><div class="visual-label">Simplified process view</div><div class="flow">{body}</div><small>{H(note)}</small></div>'
def bga():
    return '<div class="bga-diagram"><div class="bga-mold">Encapsulation / protection</div><div class="bga-die">Silicon die</div><div class="bga-bumps">Flip-chip bumps + underfill</div><div class="bga-substrate">Package substrate: routing &amp; support</div><div class="bga-balls">'+('<span>●</span>'*8)+'</div><div class="muted">Solder balls: package-to-PCB joints</div><div class="bga-pcb">PCB</div><small class="muted">Illustrative flip-chip BGA cross-section; not to scale.</small></div>'

def overview(t,r,m,d,s):
    stages=[('Wafer Fabrication','Build transistors and interconnects on silicon.','Silicon wafers undergo repeated cycles of thin-film deposition, photolithography, etching, ion implantation and chemical mechanical planarization (CMP). These processes create and connect the transistor structures that form integrated circuits.','Critical Dimension (CD) and overlay; film thickness and uniformity; defect density and wafer yield.','A processed wafer containing integrated circuits, ready for wafer-level electrical testing.',[('Wafer preparation','Clean and prepare the silicon surface.'),('Film deposition','Add insulating, conductive or semiconductor layers.'),('Pattern & etch','Transfer patterns and remove selected material.'),('Doping & planarization','Modify properties and flatten the surface.')],'Operations repeat across layers; this is not a strictly linear sequence.'),('Assembly & Packaging','Separate functional dies, establish electrical connections and protect the silicon chip.','The processed wafer is diced into individual dies. Selected dies are attached to a package substrate, electrically interconnected through wire bonding or flip-chip technology, and protected using underfill, encapsulation or a thermal management structure, depending on package design.','Die placement accuracy and alignment; bond quality and interconnection integrity; underfill/encapsulation quality and package warpage.','An assembled semiconductor package with external electrical connections.',[('Wafer dicing','Separate selected dies from the wafer.'),('Die attach','Mount the die on the package structure.'),('Interconnection','Wire bonds or flip-chip bumps connect the die.'),('Protection & finishing','Add materials and thermal structures as required.')],'Wire bonding and flip-chip are alternative interconnect routes.'),('Testing & Inspection','Verify functionality and electrical performance, with reliability assessments according to the product/test plan.','Packaged devices undergo automated electrical and functional testing. Engineers evaluate performance against product specifications, screen manufacturing failures and conduct reliability assessments under defined conditions where required.','Functional pass/fail rate; power, frequency and electrical performance; failure rate, reliability evidence and final-test yield.','Screened products meeting applicable release requirements.',[('Electrical testing','Check electrical and functional behavior.'),('Performance screening','Evaluate speed, power and operating limits.'),('Burn-in & reliability','Apply defined stress where required.'),('Final inspection','Confirm applicable release requirements.')],'Wafer probing precedes dicing. Stress and reliability checks follow the product/test plan.')]
    out=heading('01 / MANUFACTURING OVERVIEW','Manufacturing Overview','Understand the route, then connect process measurements to quality outcomes.')
    for i,(title,purpose,body,monitor,output,items,note) in enumerate(stages):
        text=f'<div class="stage-copy"><div class="eyebrow">STAGE 0{i+1}</div><h3>{title}</h3><p class="lead">{purpose}</p><p>{body}</p><strong>Engineers monitor</strong><p>{monitor}</p><strong>Output</strong><p>{output}</p></div>'
        visual=flow(items,note);out+=f'<div class="process-row panel {"reverse" if i==1 else ""}">'+(text+visual if i==1 else visual+text)+'</div>'
    out+='<h3>Possible defects by manufacturing stage</h3><div class="three-grid">'
    defs=[('Wafer Fabrication','DIE FUNCTIONALITY & YIELD',['Particle contamination: pattern defects.','Pattern bridging: unintended electrical shorts.','Etch nonuniformity: dimensional variation.','Film defects: voids, cracks or poor adhesion.'],'Optical inspection, CD-SEM, film metrology and wafer testing.'),('Assembly & Packaging','PACKAGE INTEGRITY & CONNECTIVITY',['Die cracking: stress damages the silicon.','Bonding defects: incomplete electrical paths.','Delamination: separation between materials.','Voids: risks to joint or thermal integrity.'],'Optical inspection, X-ray, acoustic microscopy and electrical testing.'),('Testing & Inspection','PRODUCT QUALITY & RELIABILITY',['Functional failure: operating requirements not met.','Electrical failure: current, voltage or timing outside limits.','Intermittent failure: inconsistent behavior.','Stress-related failure: degradation under defined tests.'],'ATE, functional testing and reliability testing.')]
    for title,impact,items,detect in defs:out+=panel(f'<h3>{title}</h3><div class="impact">{impact}</div><ul>'+''.join(f'<li>{x}</li>' for x in items)+f'</ul><small><b>Detection:</b> {detect}</small>','defect-card')
    out+='</div><p class="muted">Educational examples extend beyond the seven simulated event categories. Failures detected during testing are not proof that testing caused the defect.</p>'
    out+='<h3>Ball Grid Array (BGA)</h3><div class="process-row panel">'+bga()+'''<div class="stage-copy"><h3>Two Electrical Interfaces</h3><p>BGA connects a semiconductor package to a PCB through an array of solder balls. The package substrate routes electrical signals between the silicon die and the external board.</p><ul><li><strong>Die-to-substrate:</strong> Flip-chip bumps connect the silicon die to the substrate.</li><li><strong>Package-to-board:</strong> Solder balls connect the substrate to the PCB.</li></ul><p>The substrate provides electrical routing and mechanical support, while the package protects the silicon die.</p></div></div>'''
    out+='<h3>Surface Mount Technology (SMT)</h3>'+panel('<p>SMT mounts packaged components onto a PCB. Paste printing, placement and reflow form the solder joints; inspection checks the resulting assembly.</p><div class="smt-flow">'+'<b>→</b>'.join(f'<span>{x}</span>' for x in ['Paste printing','SPI','Placement','Reflow','AOI','X-ray where appropriate'])+'</div><p class="muted">Semiconductor packaging connects and protects the die. PCB-level SMT mounts the package onto the board and is not simulated in this dataset.</p>')
    return out

def technical_schema(t):
    relationships={'lots':'Parent of wafers (1:N); product and period context.','wafers':'FK lot_id. Parent of tracked packages and wafer runs.','packages':'FK wafer_id, lot_id. Unique source wafer + die_site.','process_runs':'FK wafer_id, lot_id, process_id, subdivision_id; package_id only for package runs.','measurements':'FK run_id. Sampled 0..1 observation per run.','defects':'FK run_id, defect_code. Multiple events can refer to a unit.','test_results':'FK package_id, run_id, subdivision_id. One package/attempt; retests use original final-test run.','equipment_events':'FK subdivision_id. Timestamped intervention.','process_steps':'Process reference: stage, unit level, parameter and illustrative specifications.','equipment':'PK subdivision_id; FK process_id. equipment_id groups subdivisions.','defect_catalog':'FK process_id. Educational event definitions.'}
    out='<div class="schema-grid">'
    for name,df in t.items():out+=f'<div class="schema-box"><strong>{name}</strong><small>PK {c.KEYS[name]} · {len(df):,} rows</small><p>{relationships[name]}</p></div>'
    out+='</div>'
    for name,df in t.items():out+=f'<details class="dictionary-entry"><summary>{name}.csv: fields</summary><p>{H(", ".join(df.columns))}</p></details>'
    return out+'<p>Conditional blank package_id is intentional on wafer runs. Redundant ancestry, unit context, measurement metadata and chronology are validated. Audit-only latent values, bias and noise are excluded from observational conclusions.</p>'

def eda(t,r,m,d,s):
    from reporting.src.explore import eda_scope
    from reporting.src.model import model_html
    rr,x,opts=eda_scope(t,r,m,s)
    process=opts['process'];spec=t['process_steps'].set_index('process_id').loc[process]
    out=heading('02 / DATA OVERVIEW & EDA','Data Overview & EDA','Choose the comparison scope first, then assess coverage and process behavior.')
    controls=select('e-product','Product',c.PRODUCTS,s.get('e-product','All'),True)+select('e-stage','Manufacturing stage',sorted(t['process_steps'].stage.unique()),s.get('e-stage','All'),True)+select('e-process','Process / parameter',opts['process_options'],process)+select('e-equipment','Equipment',opts['equipment_options'],opts['equipment'],True)+select('e-sub','Subdivision',opts['sub_options'],opts['sub'],True)+select('e-period','Period',c.PERIODS,s.get('e-period','All'),True)+input_('e-start','Measurement date: from',s.get('e-start',str(m.timestamp.min().date())),'date')+input_('e-end','Measurement date: through',s.get('e-end',str(m.timestamp.max().date())),'date')
    out+=panel('<div class="filters eda-filters">'+controls+'</div><div class="actions"><button data-action="eda-full" class="secondary">View full dataset scope</button></div>','filter-panel')
    out+='<div class="kpi-grid">'+kpi('Selected measurements',f'{len(x):,}',f'{len(m):,} in full dataset')+kpi('Selected source lots',x.lot_id.nunique())+kpi('Selected subdivisions',x.subdivision_id.nunique())+kpi('Integrity','Passed','Full-dataset validation')+'</div>'
    out+=notice(f'Selected scope: {H(spec.process_name)} / {H(spec.parameter)}; {len(x):,} measurements. Stage coverage below is full-dataset context; the other charts use the selected scope.')
    stage=m.groupby('stage').size().rename('observations').reset_index()
    out+='<div class="two-grid">'+chart(f.bars(stage,'stage','observations','Full Dataset | Measurement Coverage by Stage','Observations',highlight=spec.stage))+chart(f.histogram(x,spec.lsl,spec.usl))+'</div>'
    counts=x.groupby('subdivision_id').size().rename('observations').reset_index()
    out+='<div class="two-grid">'+chart(f.bars(counts,'subdivision_id','observations','Selected Scope | Samples by Subdivision','Measurements'))+chart(f.variation(x))+'</div>'
    lo=int(counts.observations.min()) if len(counts) else 0;hi=int(counts.observations.max()) if len(counts) else 0
    impact=f'The largest group has {hi/lo:.2f} times the observations of the smallest; compare exposure-adjusted rates, not raw event counts.' if lo else 'The selected scope contains no measurements; broaden the filters before comparing groups.'
    if len(counts)==1:impact='Only one subdivision is selected. Broaden the subdivision filter to compare groups; this view supports within-stream inspection only.'
    out+=panel(f'<h3>Comparison readiness</h3><p><b>Evidence:</b> {len(x):,} measurements across {len(counts)} subdivisions; group sizes {lo:,}–{hi:,}.</p><p><b>Impact:</b> {impact}</p><p><b>Next check:</b> compare the same parameter within matched product/period groups. Sample coverage alone does not establish representativeness.</p>','conclusion')
    out+=details('Technical schema and data dictionary',model_html()+technical_schema(t))
    out+=details('Explore underlying data','<div id="data-explorer"><div class="explorer-controls">'+select('x-table','Dataset',list(t),'measurements')+input_('x-search','Search all displayed fields','','search')+select('x-size','Rows per page',['10','25','50','100'],'25')+select('x-scope','Data scope',[('selected','Selected EDA scope'),('full','Full table')],'selected')+'</div><div class="actions"><button data-action="data-prev">Previous rows</button><button data-action="data-next">Next rows</button><button data-action="data-csv">Download CSV</button></div><div id="explorer-status" role="status"></div><div id="explorer-table" class="table-wrap"></div></div>')
    daily=m.assign(day=m.timestamp.dt.normalize()).groupby('day').size().rename('observations').reset_index();daily['day']=daily.day.dt.strftime('%d %b')
    import plotly.graph_objects as go
    fig=f.polish(go.Figure(go.Bar(x=daily.day.tolist(),y=daily.observations.tolist(),marker_color=c.COLORS['grey'])),'Daily Measurement Availability | Full Dataset',300);fig.update_xaxes(nticks=8);fig.update_yaxes(title='Observations')
    out+=details('Data completeness over time (supporting check)',chart(fig)+'<p>Full-dataset availability is a completeness check, not evidence of process quality. Edge-day counts reflect partial coverage.</p>')
    return out

def yield_page(t,r,m,d,s):
    rr=a.filter_runs(r,s.get('y-product','All'),s.get('y-process','All'),s.get('y-equipment','All'),s.get('y-lot','All'),s.get('y-start'),s.get('y-end'));dd=d[d.run_id.isin(rr.run_id)];met=a.metrics(t,rr);p=met['packages'];periods=a.periods(p);delta=a.period_delta(p);loss=a.screen_losses(rr)
    out=heading('03 / YIELD & DEFECT ANALYSIS','Yield & Defect Analysis','Locate the loss, then inspect the process behind it.')
    filters=select('y-product','Product',c.PRODUCTS,s.get('y-product','All'),True)+select('y-process','Process',[(x.process_id,x.process_name) for x in t['process_steps'].itertuples()],s.get('y-process','All'),True)+select('y-equipment','Equipment',sorted(r.equipment_id.unique()),s.get('y-equipment','All'),True)+select('y-lot','Lot',t['lots'].lot_id,s.get('y-lot','All'),True)+input_('y-start','Run-end date: from',s.get('y-start',str(r.end_time.min().date())),'date')+input_('y-end','Run-end date: through',s.get('y-end',str(r.end_time.max().date())),'date')
    out+=panel('<div class="filters">'+filters+'</div>','filter-panel')
    finding=f'Package assembly yield changed {delta:+.2f} percentage points from reference to disturbance.' if delta is not None else 'The selection does not contain both package comparison periods; a change estimate is unavailable.'
    top=loss.iloc[0] if len(loss) else None;focus=f'{top.process_name}: {top.failure_rate:.2%} failed screens ({int(top.failed):,}/{int(top.total):,} runs).' if top is not None else 'No runs in scope.'
    out+=f'<div class="insight"><h3>Observed performance</h3><p>{finding}</p><p>{focus}</p><small>Next: inspect the relevant equipment subdivision. Period contrasts are descriptive, not causal estimates.</small></div>'
    out+='<div class="kpi-grid">'
    for label,key in [('Fab wafer yield','fab'),('Package assembly yield','assembly'),('Final-test first-pass','final'),('Retest recovery','retest')]:
        z=met[key];out+=kpi(label,pct(z['rate']),f"{z['passed']:,} / {z['total']:,} distinct units")
    out+='</div>'+notice(f'Scope: {len(met["wafers"]):,} touched wafers; {len(p):,} tracked packages; {len(dd):,} events / {len(rr):,} observed runs. No cross-stage yield multiplication is implied.')
    out+=chart(f.yield_trend(p),'yield-trend')+'<p class="period-note">Reference, disturbance and post-action are predefined simulation periods. The colored windows do not establish causality or verified corrective-action effectiveness.</p>'
    lf=f.bars(loss,'process_name','failure_rate','Process Screen Failure Rate','Failed screens / observed runs',highlight=top.process_name if top is not None else None);lf.update_xaxes(tickformat='.1%')
    out+='<div class="two-grid">'+chart(lf)+chart(f.pareto_figure(a.pareto(dd)))+'</div>'
    selected=s.get('y-process','All')
    if selected!='All':out+=chart(f.bars(a.event_rates(dd,rr,'equipment_id'),'equipment_id','events_per_100_runs','Selected-process Events per 100 Runs','Events / 100 observed runs'))
    impact=''
    for row in periods.to_dict('records'):impact+=f'<p><b>{row["period"]}:</b> {row["failed"]:,} failed / {row["total"]:,} packages ({row["failed"]/row["total"]:.2%} failure rate).</p>'
    out+=panel('<h3>Observed loss and investigation priority</h3>'+impact+f'<p><b>Impact:</b> {finding} This is not an estimate of units saved or financial loss.</p><p><b>Next check:</b> {focus} Compare the same process across equipment and periods before assigning a cause.</p>','conclusion')
    display=periods.copy();display['yield']=display['yield'].map(lambda v:f'{v:.2%}');out+=panel('<h3>Package assembly period comparison</h3>'+table(display))
    out+=details('Metric definitions and filter scope','<p>Reference: source lots 1–40; disturbance: 41–90; post-action: 91–120. These are fixed simulation windows.</p><p>Fab yield = passing wafers / touched completed wafers. Assembly yield = packages passing all assembly screens / touched tracked packages. Final first-pass = passing attempt-1 packages / selected final-test packages. Retest recovery = passing attempt-2 packages / retested packages, not all first-pass failures.</p><p>Inclusive date filters use run-end time. Touched units define the cohort; whole-route unit flags are then used. Final metrics include attempts linked to selected final-test runs even if a retest timestamp is later. Assembly failures are held out of final testing. Events are not defective-unit counts; process failures can repeat on a unit.</p>')
    out+='<div class="actions"><button data-action="to-spc">Investigate in SPC</button><button data-action="to-root">Open Root Cause</button></div>'
    return out

def spc(t,r,m,d,s):
    process=s.get('s-process','S09');available=sorted(m.loc[m.process_id.eq(process),'subdivision_id'].unique());preferred=s.get('scope-equipment','All');matched=[v for v in available if v.startswith(preferred+'-')];available=matched or available;sub=s.get('s-sub',available[-3] if len(available)==4 else available[0]);sub=sub if sub in available else available[0]
    spec=t['process_steps'].set_index('process_id').loc[process];rr=a.filter_runs(r,s.get('scope-product','All'),process,'All',s.get('scope-lot','All'),s.get('scope-start'),s.get('scope-end'))
    x=m[m.run_id.isin(rr.run_id)&m.subdivision_id.eq(sub)].sort_values(['timestamp','measurement_id']);study=s.get('s-study','All periods')
    if study in c.PERIODS:x=x[x.period.eq(study)]
    cap=a.capability(x.value,spec.lsl,spec.usl);z=a.imr(x.value);view=s.get('s-view','First signal');left,right=a.display_bounds(x,z,view,s.get('s-start',1));i,mr=f.control_figures(x,z,left,right,spec.unit)
    total_i=int(z['ooc'].sum());total_mr=int(z['mr_ooc'].sum());vi=int(z['ooc'][left:right].sum());vm=int(z['mr_ooc'][max(0,left-1):max(0,right-1)].sum())
    stats=x.groupby('period',observed=True).agg(n=('value','size'),mean=('value','mean'),sd=('value','std')).reindex(c.PERIODS).dropna(subset=['n']).reset_index();means=stats.set_index('period')['mean'];shift=float(means['Disturbance']-means['Reference']) if {'Reference','Disturbance'}.issubset(means.index) else None
    out=heading('04 / SPC & CAPABILITY','SPC & Process Capability','Separate a readable display window from the full statistical study.')
    out+=panel('<div class="filters">'+select('s-process','Process / parameter',[(row.process_id,row.process_name+' | '+row.parameter) for row in t['process_steps'].itertuples()],process)+select('s-sub','Equipment subdivision',available,sub)+select('s-study','Statistical study',['All periods']+c.PERIODS,study)+select('s-view','Display window',['First signal','Reference window','Post-action window','Full history','Custom window'],view)+input_('s-start','Custom start observation',s.get('s-start',1),extra='min="1" step="1"')+'</div><p class="muted">250 consecutive observations by default. Changing display does not refit limits. Changing Statistical study starts a separate exploratory study.</p>','filter-panel')
    finding=f'Full study: {total_i:,} Individuals and {total_mr:,} MR signals across {len(x):,} observations.' if z['status']=='ok' else f'Limits unavailable: {z["status"]}; {len(x)} observations in scope.'
    shift_text=f'Disturbance mean shift: {shift:+.2f} {spec.unit} versus reference.' if shift is not None else 'A reference-versus-disturbance mean shift is unavailable for this scope.'
    out+=f'<div class="insight"><h3>Observed process behavior</h3><p>{finding}</p><p>{shift_text}</p><small>Signals refer to observations, not unique failed packages. Full-study limits remain frozen when the display changes.</small></div>'
    out+='<div class="kpi-grid">'+kpi('Full-study observations',f'{len(x):,}',f'Baseline: first {z["baseline_n"]} points')+kpi('Visible I / MR signals',f'{vi} / {vm}' if z['status']=='ok' else 'N/A',f'Observations {left+1 if right else 0}–{right}')+kpi('Cp','Withheld' if cap['cp'] is None else num(cap['cp']))+kpi('Cpk','Withheld' if cap['cpk'] is None else num(cap['cpk']))+'</div>'
    out+=f'<div class="scope" id="spc-scope">{H(spec.process_name)} | {H(sub)} | {H(study)} | display {left+1 if right else 0}–{right} of {len(x):,}. Limits use the full selected study, not just visible points.</div>'
    out+=chart(i,'individuals-chart')+chart(mr,'mr-chart')
    out+='<h3>Can this stream meet specifications?</h3>'+notice(f'<b>Capability: {H(cap["status"])}</b><br>Full-study mean {num(cap["mean"])} {spec.unit}; overall SD {num(cap["std"])}; within sigma {num(cap["sigma"])}. Specifications are illustrative, not control limits.')+chart(f.histogram(x,spec.lsl,spec.usl,cap),'capability-chart')
    out+=panel(f'<h3>Engineering implication</h3><p><b>Evidence:</b> {finding} {shift_text}</p><p><b>Impact:</b> '+('detected instability makes a single capability index unsuitable for this study. Signals define a review scope, not a defective-unit count.' if cap['status']=='detected instability' else 'review the reported sample size, distribution and measurement-system assumptions before using capability for a decision.')+'</p><p><b>Next check:</b> inspect the first-signal window and compare matched periods on the same subdivision. Independently verify metrology before assigning a physical cause.</p>','conclusion')
    out+=details('Method & assumptions',table(stats.round(3))+'<p>I-MR uses chronological observations, not daily averages. First 40 points estimate frozen limits; minimum 20. Within sigma = baseline mean MR / 1.128. I limits = baseline mean ± 3 × within sigma. MR UCL = 3.267 × baseline mean MR; MR LCL = 0.</p><p>Cp = (USL − LSL)/(6 × within sigma). Cpk = min(USL − mean, mean − LSL)/(3 × within sigma). Cp describes spread; Cpk also reflects centering. Overall sample SD is reported separately.</p><p>Capability requires 30 observations and is withheld for detected I/MR instability, zero variation or failed normality screening (alpha .01). Only beyond-3-sigma rules are implemented. No-signal and normality tests do not establish independence, stability or MSA adequacy.</p><p>Display navigation never changes the study, baseline or Cp/Cpk. The first displayed MR can use the immediate preceding observation outside the display. No gaps are bridged. A new Statistical study may refit its own illustrative baseline.</p>')
    bx,bc=a.benchmark();out+=details('Independent Cp/Cpk teaching example',f'<p>Separate fixed normal quantiles in deterministic shuffled order; not manufacturing observations and not evidence about the selected equipment. The same screening functions return <b>Cp {bc["cp"]:.3f}</b> and <b>Cpk {bc["cpk"]:.3f}</b>, n=100, LSL=96, USL=106 arbitrary units. No screening bypass or manufacturing resampling.</p>')
    return out

def root(t,r,m,d,s):
    process=s.get('r-process','S09');lot=s.get('r-lot','All');rr=a.filter_runs(r,s.get('scope-product','All'),process,s.get('scope-equipment','All'),lot,s.get('scope-start'),s.get('scope-end'));x=m[m.run_id.isin(rr.run_id)];dd=d[d.run_id.isin(rr.run_id)];spec=t['process_steps'].set_index('process_id').loc[process]
    try:threshold=float(s.get('r-threshold',.98))
    except (ValueError,TypeError):threshold=-1
    out=heading('05 / ROOT CAUSE INVESTIGATION','Root Cause Investigation','Use evidence to prioritize hypotheses, not to manufacture certainty.')
    out+=panel('<div class="filters">'+select('r-process','Process',[(row.process_id,row.process_name) for row in t['process_steps'].itertuples()],process)+select('r-lot','Lot',t['lots'].lot_id,lot,True)+input_('r-threshold','Assembly yield cohort threshold',s.get('r-threshold',.98),extra='min="0" max="1" step="0.01"')+'</div>','filter-panel')
    if not 0<=threshold<=1:return out+notice('Enter a yield threshold between 0 and 1.')
    rates=a.event_rates(dd,rr,'subdivision_id');stats=x.groupby(['subdivision_id','period'],observed=True).agg(n=('value','size'),mean=('value','mean'),sd=('value','std')).reset_index();contrasts=[]
    for sub,g in stats.groupby('subdivision_id'):
        z=g.set_index('period')
        if {'Reference','Disturbance'}.issubset(z.index):contrasts.append((sub,float(z.loc['Disturbance','mean']-z.loc['Reference','mean']),int(z.loc['Reference','n']),int(z.loc['Disturbance','n'])))
    contrasts.sort(key=lambda v:abs(v[1]),reverse=True);top=contrasts[0] if contrasts else None;selected=top[0] if top else (str(x.subdivision_id.iloc[0]) if len(x) else '')
    ev=t['equipment_events'][t['equipment_events'].subdivision_id.eq(selected)];stream=x[x.subdivision_id.eq(selected)].sort_values(['timestamp','measurement_id']);p=t['packages'][t['packages'].package_id.isin(rr.package_id)];delta=a.period_delta(p)
    statement=f'{top[0]} shows the largest observed mean shift: {top[1]:+.2f} {spec.unit} (reference n={top[2]:,}; disturbance n={top[3]:,}).' if top else 'The selected scope does not support a reference-versus-disturbance comparison.'
    peak=rates.iloc[0] if len(rates) else None;rate_text=f'{peak.subdivision_id}: {peak.events_per_100_runs:.2f} events per 100 runs ({int(peak.events):,}/{int(peak.runs):,}).' if peak is not None else 'No event exposure in scope.'
    out+=f'<div class="insight"><h3>Problem and observed evidence</h3><p>{statement}</p><p>Highest selected-process event rate: {rate_text}</p><small>These associations prioritize a review. They do not confirm a physical root cause.</small></div>'
    failed=int((1-p.assembly_pass).sum());out+='<div class="kpi-grid">'+kpi('Lots in scope',rr.lot_id.nunique())+kpi('Parameter observations',f'{len(x):,}')+kpi('Selected-process events',len(dd))+kpi('Assembly-failing packages',f'{failed:,}',f'{len(p):,} touched tracked packages')+'</div>'
    out+=chart(f.variation(x))+chart(f.timeline(stream,ev))
    out+=panel(f'<h3>Impact and next verification</h3><p><b>Evidence:</b> {statement}</p><p><b>Observed cohort impact:</b> {failed:,} assembly-failing packages / {len(p):,} tracked packages in scope.'+(f' Disturbance yield differs from reference by {delta:+.2f} percentage points.' if delta is not None else '')+'</p><p><b>Boundary:</b> these are whole-route assembly outcomes, not failures proven to originate at the selected step.</p><p><b>Next check:</b> independently verify the measurement system, inspect equipment history and run a matched-product/lot comparison before confirming the mechanism.</p>','conclusion')
    out+=panel('<h3>Selected-process event exposure</h3>'+table(rates.round(3))+'<h4>Recorded interventions</h4>'+table(ev[['subdivision_id','timestamp','event_type']]))
    hyp=pd.DataFrame([['Equipment condition',statement,'Calibration artifact, fixture inspection and matched-lot comparison'],['Measurement-system bias','Observed shift may differ from physical change','Independent reference measurement / MSA'],['Material or time effects','Period and product mix may differ','Stratify by product, material batch and time']],columns=['Hypothesis','Observed evidence / limitation','Verification needed'])
    out+=panel('<h3>Competing hypotheses</h3>'+table(hyp))
    fish=''.join(f'<div><strong>{title}</strong><p>{body}</p></div>' for title,body in [('Machine','Alignment / fixture / wear'),('Method','Recipe / cleaning / handling'),('Material','Batch / substrate condition'),('Measurement','Bias / calibration / repeatability'),('People','Handover / training'),('Environment','Temperature / particles')])
    out+=details('Fishbone: candidate causes, not findings','<div class="fishbone">'+fish+'</div>')
    out+=panel('<h3>5 Whys | evidence before certainty</h3><p class="muted">Record alternatives and evidence needed. Five answers are a template, not proof.</p><div class="form-grid">'+''.join(f'<div><label for="why-{i}">Why {i+1}?</label><textarea id="why-{i}" data-note="why-{i}" placeholder="Evidence needed..."></textarea></div>' for i in range(5))+'</div>')
    labels=['Problem statement','Potential cause (hypothesis)','Supporting evidence','Containment','Corrective action','Verification method','Effectiveness criteria']
    out+=panel('<h3>CAPA | containment, correction and effectiveness</h3><div class="form-grid">'+''.join(f'<div><label for="capa-{i}">{label}</label><textarea id="capa-{i}" data-note="capa-{i}" placeholder="Record a specific, verifiable entry..."></textarea></div>' for i,label in enumerate(labels))+'</div><div class="actions"><button data-action="download-notes">Download investigation notes</button></div><p class="muted">Notes stay in this browser session. Download before closing; no database or automatic persistence is implied.</p>')
    import plotly.graph_objects as go
    lot_yield=p.groupby('lot_id').assembly_pass.mean()
    cohort=x.assign(cohort=np.where(x.lot_id.map(lot_yield).lt(threshold),'Below threshold','At/above threshold'))
    cf=go.Figure()
    for label,col in [('At/above threshold',c.COLORS['blue']),('Below threshold',c.COLORS['teal'])]:
        xx=cohort[cohort.cohort.eq(label)];cf.add_trace(go.Box(y=xx.value.tolist(),name=label,boxpoints=False,marker_color=col))
    cf.update_yaxes(title=spec.unit);f.polish(cf,'Measurements by Yield-defined Lot Cohort',360)
    lot_stats=x.groupby('lot_id').agg(Mean=('value','mean'),SD=('value','std')).join(a.event_rates(dd,rr,'lot_id').set_index('lot_id')['events_per_100_runs'].rename('Events / 100 runs')).dropna()
    if len(lot_stats)>=3:
        corr=lot_stats.corr();hf=go.Figure(go.Heatmap(z=corr.to_numpy().tolist(),x=corr.columns.tolist(),y=corr.index.tolist(),zmin=-1,zmax=1,colorscale='RdBu_r',text=corr.round(2).to_numpy().tolist(),texttemplate='%{text}',colorbar=dict(title='r')));f.polish(hf,f'Lot-level Associations | n={len(lot_stats)}',360)
    else:hf=f.empty('Lot-level Associations: at least 3 lots required')
    out+=details('Supporting cohort comparison and associations','<div class="two-grid">'+chart(cf)+chart(hf)+'</div><p>Groups are defined by observed assembly yield, not randomized treatment. Mean/SD/event-rate associations can reflect common time effects and do not establish causality.</p>')
    out+=details('Supporting evidence and cohort definitions',table(stats.round(3))+f'<p>Cohort threshold {threshold:.0%} applies to lot-level assembly yield of touched packages. It is an exploratory definition, not an approved release limit. Single-lot selections cannot support lot-level correlation. Correlation and before/after improvement do not prove causality.</p>')
    return out

RENDERERS=dict(overview=overview,eda=eda,yield_page=yield_page,spc=spc,root=root)
def render(page,t,r,m,d,state=None):
    fn=yield_page if page=='yield' else RENDERERS.get(page)
    if fn is None:raise ValueError('Unknown page')
    body=fn(t,r,m,d,state or {})
    keys=[key for key,_ in PAGES];idx=keys.index(page)
    prev=f'<button data-page="{keys[idx-1]}" class="secondary">Previous page</button>' if idx else '<span></span>'
    next_=f'<button data-page="{keys[idx+1]}">Next page</button>' if idx<len(keys)-1 else '<span></span>'
    return body+f'<div class="page-pager">{prev}<span>Page {idx+1} of 5</span>{next_}</div>' 
