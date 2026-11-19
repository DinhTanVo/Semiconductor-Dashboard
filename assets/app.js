'use strict';
let currentPage='overview';let state={};let notes={};let requestId=0;
window.mountCharts=async function(root=document){
 const plots=[...root.querySelectorAll('[data-figure]')];
 for(const el of plots){
  const data=document.getElementById(el.dataset.figure);if(!data)continue;
  const figure=JSON.parse(data.textContent);
  await Plotly.newPlot(el,figure.data,figure.layout,{responsive:true,displaylogo:false,modeBarButtonsToRemove:['lasso2d','select2d']});
 }
};
function saveNotes(){document.querySelectorAll('[data-note]').forEach(e=>notes[e.dataset.note]=e.value)}
async function showPage(page,scroll=true){
 saveNotes();currentPage=page;const id=++requestId;const root=document.getElementById('tab-content');root.classList.add('loading');document.getElementById('status').textContent='Updating analysis...';
 try{
  const response=await fetch('/api/page',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({page,state})});
  const data=await response.json();if(!response.ok)throw new Error(data.error||'Unable to update analysis');if(id!==requestId)return;
  root.querySelectorAll('.js-plotly-plot').forEach(p=>Plotly.purge(p));root.innerHTML=data.body;
  root.querySelectorAll('[data-state]').forEach(e=>state[e.dataset.state]=e.value);
  root.querySelectorAll('[data-note]').forEach(e=>e.value=notes[e.dataset.note]||'');
  document.querySelectorAll('.nav [data-page]').forEach(b=>{b.classList.toggle('active',b.dataset.page===page);b.setAttribute('aria-current',b.dataset.page===page?'page':'false')});
  await mountCharts(root);if(document.querySelector('#data-explorer'))await loadData();document.getElementById('status').textContent='Analysis updated.';if(scroll)window.scrollTo({top:0,behavior:'instant'});
 }catch(e){document.getElementById('status').textContent=e.message;console.error(e)}finally{root.classList.remove('loading')}
}
document.addEventListener('change',e=>{
 if(e.target.matches('[data-state]')){if(e.target.id.startsWith('x-')){state[e.target.id]=e.target.value;dataPage=1;loadData();return;}const key=e.target.dataset.state;state[key]=e.target.value;if(key==='e-stage'){delete state['e-process'];delete state['e-equipment'];delete state['e-sub']}if(key==='e-process'){delete state['e-equipment'];delete state['e-sub']}if(key==='e-equipment')delete state['e-sub'];if(key==='s-process'){delete state['s-sub'];delete state['scope-equipment']}showPage(currentPage,false)}
});
document.addEventListener('input',e=>{if(e.target.matches('[data-note]'))notes[e.target.dataset.note]=e.target.value});
document.addEventListener('click',e=>{
 const sort=e.target.closest('[data-sort]');if(sort){dataDescending=dataSort===sort.dataset.sort?!dataDescending:false;dataSort=sort.dataset.sort;dataPage=1;loadData();return}
 const tab=e.target.closest('[data-page]');if(tab){showPage(tab.dataset.page);return}
 const button=e.target.closest('[data-action]');if(!button)return;
 const action=button.dataset.action;
 if(action==='eda-full'){Object.keys(state).filter(k=>k.startsWith('e-')).forEach(k=>delete state[k]);showPage('eda',false);return}
 if(action==='model-fit'){document.querySelector('.model-svg').style.width='100%';return}
 if(action==='model-zoom'){const el=document.querySelector('.model-svg');el.style.width=(el.getBoundingClientRect().width*1.25)+'px';return}
 if(action.startsWith('data-')){if(action==='data-prev')dataPage=Math.max(1,dataPage-1);if(action==='data-next')dataPage++;if(action==='data-csv'){downloadData();return}loadData();return}
 if(action==='reset'){state={};showPage(currentPage);return}
 if(action==='to-spc'||action==='to-root'){
  const process=state['y-process']&&state['y-process']!=='All'?state['y-process']:'S09';
  state['scope-product']=state['y-product']||'All';state['scope-lot']=state['y-lot']||'All';state['scope-start']=state['y-start']||'';state['scope-end']=state['y-end']||'';
  state['scope-equipment']=state['y-equipment']||'All';
  if(action==='to-spc'){state['s-process']=process;delete state['s-sub'];state['s-study']='All periods';state['s-view']='First signal';showPage('spc')}
  else{state['r-process']=process;state['r-lot']=state['y-lot']||'All';showPage('root')}return;
 }
 if(action==='download-notes'){
  saveNotes();const blob=new Blob([JSON.stringify({project:'Semiconductor quality investigation',exported_utc:new Date().toISOString(),scope:state,notes},null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='investigation_notes.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
 }
});
document.addEventListener('toggle',e=>{if(e.target.tagName==='DETAILS'&&e.target.open){setTimeout(()=>e.target.querySelectorAll('.js-plotly-plot').forEach(p=>Plotly.Plots.resize(p)),50)}},true);
let dataPage=1,dataSort='',dataDescending=false;
function dataPayload(){return {state,table:state['x-table']||'measurements',scope:state['x-scope']||'selected',search:state['x-search']||'',size:state['x-size']||25,page:dataPage,sort:dataSort,descending:dataDescending}}
async function loadData(){
 const target=document.querySelector('#explorer-table');if(!target)return;
 try{let response=await fetch('/api/data',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(dataPayload())});let data=await response.json();if(!response.ok){if(dataSort){dataSort='';return loadData()}throw new Error(data.error)}dataPage=data.page;
 document.querySelector('#explorer-status').textContent=`Rows ${data.start}–${data.end} of ${data.total.toLocaleString()} | Page ${data.page} of ${data.pages} | ${state['x-scope']==='full'?'Full table':'Selected EDA scope'}`;
 const table=document.createElement('table'),head=document.createElement('thead'),hr=document.createElement('tr');for(const col of data.columns){let th=document.createElement('th'),b=document.createElement('button');b.type='button';b.className='table-sort';b.dataset.sort=col;b.textContent=col+(dataSort===col?(dataDescending?' ↓':' ↑'):'');th.appendChild(b);hr.appendChild(th)}head.appendChild(hr);table.appendChild(head);let body=document.createElement('tbody');for(const row of data.rows){let tr=document.createElement('tr');for(const col of data.columns){let td=document.createElement('td');td.textContent=row[col]===null?'':String(row[col]);tr.appendChild(td)}body.appendChild(tr)}table.appendChild(body);target.replaceChildren(table);
 }catch(e){document.querySelector('#explorer-status').textContent=e.message}
}
async function downloadData(){const response=await fetch('/api/csv',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(dataPayload())});if(!response.ok)return;const blob=await response.blob(),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=(state['x-table']||'measurements')+'_'+(state['x-scope']||'selected')+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
showPage('overview');
