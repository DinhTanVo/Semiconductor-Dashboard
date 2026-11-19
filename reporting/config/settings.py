from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'data/raw';REF=ROOT/'data/reference';OUTPUT=ROOT/'output'
TITLE='Semiconductor Manufacturing & Quality Analytics'
AUTHOR='Vo Tan Dinh | Engineering, Data & Process Improvement'
SEED=7241;N_LOTS=120;WAFERS_PER_LOT=25;N_PACKAGES=24000
PERIODS=['Reference','Disturbance','Post-action'];REFERENCE_END=40;ACTION_LOT=91
PRODUCTS=['Compute A','Compute B','Connectivity C','Control D']
BASELINE_N=40;MIN_SPC_N=20;MIN_CAP_N=30;D2=1.128;D4=3.267;ALPHA=.01;DISPLAY_N=250
HOST='127.0.0.1';PORT=8050
STEPS=[('S01','Film deposition','Fabrication','wafer','Film thickness','nm',100,1.2,92,108),('S02','Photolithography','Fabrication','wafer','Critical dimension','nm',40,.4,37,43),('S03','Etching','Fabrication','wafer','Etch depth','nm',120,1.2,112,128),('S04','Ion implantation','Fabrication','wafer','Dose','1e13 ions/cm2',5,.05,4.6,5.4),('S05','Annealing','Fabrication','wafer','Sheet resistance','ohm/sq',50,.5,46,54),('S06','CMP','Fabrication','wafer','Planarity','nm',20,.3,18,22),('S07','Metallization','Fabrication','wafer','Metal thickness','nm',200,2,186,214),('S08','Wafer inspection','Fabrication','wafer','Overlay','nm',3,.1,2.3,3.7),('S09','Flip-chip attach','Assembly','package','X placement offset','um',0,1.5,-10,10),('S10','Underfill','Assembly','package','Void area fraction','%',1,.18,0,3),('S11','Package integrity','Assembly','package','Warpage','um',50,4,20,80),('S12','Final electrical test','Test','package','Leakage current','nA',10,.4,7,13)]
RAW_NAMES=['lots','wafers','packages','process_runs','measurements','defects','test_results','equipment_events']
REF_NAMES=['process_steps','equipment','defect_catalog']
KEYS=dict(lots='lot_id',wafers='wafer_id',packages='package_id',process_runs='run_id',measurements='measurement_id',defects='defect_id',test_results='test_id',equipment_events='event_id',process_steps='process_id',equipment='subdivision_id',defect_catalog='defect_code')
COLORS=dict(blue='#2475db',teal='#00a99d',amber='#e8903b',red='#d94d59',navy='#102b49',grey='#73879a')
