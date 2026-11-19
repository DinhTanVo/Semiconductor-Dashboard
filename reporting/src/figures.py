"""Plotly figures with semantic colors and disclosed statistical scopes."""
import textwrap
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import norm
from reporting.config import settings as c
from reporting.src.analysis import imr
C=c.COLORS

def polish(f,title,height=370):
    f.update_layout(title=dict(text=title,x=.025,font_size=17),height=height,font=dict(family='Arial, sans-serif',size=12,color='#29405b'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=65,r=35,t=65,b=65),colorway=[C['blue'],C['teal'],C['amber']],legend=dict(orientation='h',y=-.22,font_size=11),hovermode='closest')
    f.update_xaxes(showline=False,zeroline=False,automargin=True,gridcolor='#edf2f7',nticks=7)
    f.update_yaxes(showline=False,zeroline=False,automargin=True,gridcolor='#edf2f7')
    return f

def empty(title):
    f=go.Figure();f.add_annotation(x=.5,y=.5,xref='paper',yref='paper',text='No matching observations. Adjust the filters.',showarrow=False,font_color=C['grey']);f.update_xaxes(visible=False);f.update_yaxes(visible=False);return polish(f,title,280)

def bars(df,category,value,title,unit='',highlight=None,color=None):
    if df.empty:return empty(title)
    df=df.sort_values(value);colors=[C['blue'] if str(v)==str(highlight) else (color or C['grey']) for v in df[category]]
    f=go.Figure(go.Bar(y=df[category].astype(str).tolist(),x=df[value].tolist(),orientation='h',marker_color=colors,hovertemplate='%{y}<br>%{x:.3f}<extra></extra>'))
    f.update_xaxes(title=unit,rangemode='tozero');return polish(f,title,max(330,120+len(df)*24))

def yield_trend(p):
    if p.empty:return empty('Package Assembly Yield')
    df=p.assign(day=p.assembly_complete_time.dt.normalize()).groupby('day').agg(passed=('assembly_pass','sum'),total=('package_id','size'),period=('period',lambda z:' / '.join(dict.fromkeys(z)))).reset_index();df['yield']=df.passed/df.total
    f=go.Figure(go.Scatter(x=df.day.tolist(),y=df['yield'].tolist(),mode='lines+markers',name='Daily assembly yield',line=dict(color=C['blue'],width=1.7),marker=dict(size=4,symbol='circle'),customdata=df[['passed','total','period']].to_numpy().tolist(),hovertemplate='%{x|%d %b %Y}<br>Yield %{y:.2%}<br>%{customdata[0]} / %{customdata[1]} packages<br>Period: %{customdata[2]}<extra></extra>'))
    for period,col in zip(c.PERIODS,[C['teal'],C['amber'],C['blue']]):
        g=p[p.period.eq(period)]
        if len(g):
            f.add_vrect(x0=g.assembly_complete_time.min().normalize(),x1=g.assembly_complete_time.max().normalize(),fillcolor=col,opacity=.08,line_width=0)
            f.add_trace(go.Scatter(x=[None],y=[None],mode='markers',marker=dict(symbol='square',size=11,color=col,opacity=.45),name=period+' period',hoverinfo='skip'))
    f.update_yaxes(title='Package assembly yield',tickformat='.1%',range=[max(0,float(df['yield'].min())-.015),1.005]);f.update_xaxes(title='Assembly completion date')
    polish(f,'Package Assembly Yield (zoomed axis)',420);f.update_layout(legend=dict(orientation='h',y=-.28,font_size=10),margin=dict(l=70,r=30,t=60,b=110))
    return f

def pareto_figure(df):
    if df.empty:return empty('Defect Event Pareto')
    labels=['<br>'.join(textwrap.wrap(v,12)) for v in df.defect_name]
    f=go.Figure(go.Bar(x=labels,y=df.events.tolist(),name='Events',marker_color=C['blue']))
    f.add_trace(go.Scatter(x=labels,y=df.cumulative_pct.tolist(),name='Cumulative %',yaxis='y2',mode='lines+markers',line=dict(color=C['amber'],width=2),marker_size=5))
    f.update_layout(yaxis2=dict(overlaying='y',side='right',range=[0,105],title='Cumulative %',showgrid=False));f.update_yaxes(title='Events',rangemode='tozero');f.update_xaxes(tickangle=0)
    f.update_layout(yaxis2_title='Cumulative %');f.update_xaxes(tickangle=0,tickfont_size=10)
    return polish(f,'Defect Event Pareto',400)

def histogram(m,lsl=None,usl=None,cap=None):
    """Selected-scope histogram with independently labeled specification and mean lines."""
    import pandas as pd
    if m.empty or 'value' not in m:return empty('Selected Parameter Distribution')
    values=pd.to_numeric(m['value'],errors='coerce').to_numpy(dtype=float)
    values=values[np.isfinite(values)]
    if not len(values):return empty('Selected Parameter Distribution')
    mean=float(values.mean());unit=str(m.unit.iloc[0]) if 'unit' in m else 'a.u.'
    f=go.Figure(go.Histogram(x=values.tolist(),nbinsx=30,histnorm='probability density',marker_color='#83b5eb',name='Observed',showlegend=True))
    if cap and cap.get('cp') is not None and cap.get('std'):
        grid=np.linspace(min(values.min(),lsl if lsl is not None else values.min()),max(values.max(),usl if usl is not None else values.max()),200)
        f.add_trace(go.Scatter(x=grid.tolist(),y=norm.pdf(grid,mean,cap['std']).tolist(),name='Normal fit (overall SD)',line_color=C['navy']))
    for v,label in [(lsl,'LSL'),(usl,'USL')]:
        if v is not None:
            f.add_vline(x=v,line_color=C['amber'],line_dash='dash',annotation_text=f'{label} {v:g}',annotation_position='top')
            f.add_trace(go.Scatter(x=[None],y=[None],mode='lines',name=f'{label} {v:g} {unit}',line=dict(color=C['amber'],dash='dash')))
    f.add_vline(x=mean,line_color=C['teal'],line_width=2.5,annotation_text=f'Mean = {mean:.3f} {unit}',annotation_position='top',annotation_yshift=-22)
    f.add_trace(go.Scatter(x=[None],y=[None],mode='lines',name=f'Mean {mean:.3f} {unit}',line=dict(color=C['teal'],width=2.5)))
    if lsl is not None and usl is not None and usl>lsl:
        f.update_xaxes(range=[min(lsl,float(values.min()))-(usl-lsl)*.06,max(usl,float(values.max()))+(usl-lsl)*.06])
    f.update_xaxes(title=unit);f.update_yaxes(title='Probability density')
    f=polish(f,'Selected Parameter Distribution',400)
    f.update_layout(meta=dict(selected_mean=mean,valid_n=len(values)),margin=dict(l=70,r=35,t=85,b=105))
    f.add_annotation(x=1,y=-.34,xref='paper',yref='paper',text=f'n = {len(values):,} | Mean = {mean:.3f} {unit}',showarrow=False,xanchor='right',font_size=11)
    return f

def control_figures(frame,a,left,right,unit):
    if frame.empty:return empty('Individuals Control Chart'),empty('Moving Range Control Chart')
    seq=np.arange(1,len(frame)+1);visible=(seq>left)&(seq<=right);bad=a['ooc']&visible
    custom=np.column_stack([frame.timestamp.dt.strftime('%d %b %Y %H:%M'),frame.lot_id]).tolist()
    f=go.Figure(go.Scatter(x=seq[visible].tolist(),y=a['values'][visible].tolist(),mode='lines+markers',marker=dict(size=2 if right-left>500 else 4.2,symbol='circle'),name='Measurement',line=dict(color=C['blue'],width=1.3),customdata=np.array(custom)[visible].tolist(),hovertemplate='Observation %{x}<br>%{customdata[0]} | %{customdata[1]}<br>%{y:.3f}<extra></extra>'))
    f.add_trace(go.Scatter(x=seq[bad].tolist(),y=a['values'][bad].tolist(),mode='markers',name='Beyond I limit',marker=dict(color=C['red'],size=5.5 if right-left>500 else 8,symbol='diamond',line=dict(color='white',width=.4))))
    ms=seq[1:];mv=(ms>left)&(ms<=right);mb=a['mr_ooc']&mv
    mr=go.Figure(go.Scatter(x=ms[mv].tolist(),y=a['mr'][mv].tolist(),mode='lines+markers',marker=dict(size=2 if right-left>500 else 4.2,symbol='circle'),name='Moving range',line=dict(color=C['teal'],width=1.1)))
    mr.add_trace(go.Scatter(x=ms[mb].tolist(),y=a['mr'][mb].tolist(),mode='markers',name='Beyond MR limit',marker=dict(color=C['red'],size=5.5 if right-left>500 else 8,symbol='diamond',line=dict(color='white',width=.4))))
    for fig,limits,title,height in [(f,[('CL',a['cl']),('UCL',a['ucl']),('LCL',a['lcl'])],'Individuals Control Chart',390),(mr,[('MR CL',a['mr_cl']),('MR UCL',a['mr_ucl']),('MR LCL',0)],'Moving Range Control Chart',260)]:
        if a['status']=='ok':
            for label,v in limits:fig.add_hline(y=v,line_color=C['teal'] if label.endswith('CL') and 'UCL' not in label and 'LCL' not in label else C['red'],line_dash='dash',line_width=1)
            fig.add_annotation(x=1,y=1.08,xref='paper',yref='paper',text=' | '.join(f'{k} {v:.2f}' for k,v in limits),showarrow=False,xanchor='right',font_size=10)
        if left<a['baseline_n']:
            fig.add_vrect(x0=left+.5,x1=min(right,a['baseline_n'])+.5,fillcolor=C['teal'],opacity=.07,line_width=0)
            fig.add_trace(go.Scatter(x=[None],y=[None],mode='markers',marker=dict(symbol='square',size=10,color=C['teal'],opacity=.4),name='Baseline estimation window',hoverinfo='skip'))
        if left<a['baseline_n']<right:fig.add_vline(x=a['baseline_n']+.5,line_dash='dot',line_color=C['grey'])
        fig.update_xaxes(title='Chronological observation sequence',range=[left+.5,right+.5]);fig.update_yaxes(title=unit);polish(fig,title,height);fig.update_layout(margin=dict(l=65,r=30,t=70,b=70),legend_y=-.32)
        fig.update_layout(margin=dict(l=65,r=30,t=70,b=90),showlegend=True)
    mr.update_yaxes(rangemode='tozero');return f,mr

def variation(m):
    if m.empty:return empty('Parameter by Subdivision and Period')
    f=go.Figure()
    for period,col in zip(c.PERIODS,[C['teal'],C['amber'],C['blue']]):
        x=m[m.period.eq(period)];f.add_trace(go.Box(x=x.subdivision_id.tolist(),y=x.value.tolist(),name=period,marker_color=col,boxpoints=False))
    f.update_layout(boxmode='group');f.update_xaxes(title='Equipment subdivision');f.update_yaxes(title=m.unit.iloc[0]);return polish(f,'Parameter by Subdivision and Period',390)

def timeline(m,events):
    if m.empty:return empty('Selected-stream Daily Mean')
    g=m.assign(day=m.timestamp.dt.normalize()).groupby('day').agg(mean=('value','mean'),n=('value','size')).reset_index()
    f=go.Figure(go.Scatter(x=g.day.tolist(),y=g['mean'].tolist(),mode='lines+markers',marker_size=4,line_color=C['blue'],customdata=g.n.tolist(),hovertemplate='%{x|%d %b}<br>Daily mean %{y:.3f}<br>n=%{customdata}<extra></extra>'))
    for e in events.itertuples():f.add_vline(x=e.timestamp,line_dash='dot',line_color=C['amber']);f.add_annotation(x=e.timestamp,y=1.04,yref='paper',text=e.event_type,showarrow=False,font_size=10)
    f.update_yaxes(title='Daily mean ('+m.unit.iloc[0]+')');f.update_xaxes(title='Measurement date');return polish(f,'Selected-stream Daily Mean (not an I chart)',360)
