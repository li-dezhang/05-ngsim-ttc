"""Apply the three prespecified methods to identical continuous pair segments."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import argparse,json,time,datetime,hashlib,platform
import numpy as np
import pandas as pd
from src.ngsim.core import FT,METHODS,process_segment,ttc
def main():
    arg=argparse.ArgumentParser();arg.add_argument('--run-id',required=True);arg.add_argument('--pilot',action='store_true');a=arg.parse_args()
    out=ROOT/'results'/a.run_id;out.mkdir(parents=True,exist_ok=False)
    started=datetime.datetime.now(datetime.timezone.utc).isoformat();start=time.perf_counter();z=np.load(ROOT/'data/processed/pairs.npz');p={k:z[k] for k in z.files}
    cuts=np.r_[0,np.flatnonzero(np.diff(p['segment'])!=0)+1,len(p['segment'])]
    chunks=[];processed=0
    for left,right in zip(cuts[:-1],cuts[1:]):
        if right-left<23:continue
        if a.pilot and processed>=20:break
        sl=slice(left,right);inner=slice(left+11,right-11)
        t=(p['global_time'][sl]-p['global_time'][left])/1000
        row={c:p[c][inner] for c in ['segment','vehicle_id','preceding','frame_id','global_time','lane']}
        row['reported_follower_speed']=p['reported_speed'][inner]*FT;row['reported_leader_speed']=p['leader_reported_speed'][inner]*FT
        common=np.ones(right-left-22,dtype=bool)
        for name,window in METHODS.items():
            derived=process_segment(p['local_y'][sl]*FT,p['leader_local_y'][sl]*FT,p['leader_length'][sl]*FT,t,window)
            values,valid=ttc(derived['gap'],derived['follower_speed'],derived['leader_speed'])
            common&=valid
            row.update({name+'_'+k:v for k,v in derived.items()});row[name+'_ttc']=values;row[name+'_valid']=valid
        row['common_valid']=common;chunks.append(row);processed+=1
    if not chunks:raise ValueError('No eligible real segments')
    data={k:np.concatenate([r[k] for r in chunks]) for k in chunks[0]}
    path=ROOT/'data/processed'/f'{a.run_id}.npz';np.savez_compressed(path,**data)
    quality=[]
    for name in METHODS:
        gap=data[name+'_gap'];vf=data[name+'_follower_speed'];vl=data[name+'_leader_speed'];af=data[name+'_follower_acc'];al=data[name+'_leader_acc']
        delta=data[name+'_follower_y']-data['raw_follower_y']
        quality.append(dict(method=name,candidate_frames=len(gap),method_valid=int(data[name+'_valid'].sum()),nonpositive_gap=int((gap<=0).sum()),negative_speed=int(((vf<0)|(vl<0)).sum()),speed_over_55=int(((vf>55)|(vl>55)).sum()),acceleration_over_15=int(((np.abs(af)>15)|(np.abs(al)>15)).sum()),follower_speed_min=float(vf.min()),follower_speed_max=float(vf.max()),follower_acc_abs_p99=float(np.quantile(np.abs(af),.99)),position_change_rms_m=float(np.sqrt(np.mean(delta**2))),position_change_abs_max_m=float(np.max(np.abs(delta))),speed_reported_rmse=float(np.sqrt(np.mean((vf-data['reported_follower_speed'])**2)))))
    pd.DataFrame(quality).to_csv(out/'method_quality.csv',index=False)
    record={'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'platform':platform.platform(),'python':platform.python_version(),'pilot':a.pilot,'processed_segments':processed,'candidate_frames':len(data['frame_id']),'common_valid_frames':int(data['common_valid'].sum()),'common_excluded':int((~data['common_valid']).sum()),'seconds':time.perf_counter()-start,'local_frame_file':str(path.relative_to(ROOT)),'raw_txt_sha256':hashlib.sha256((ROOT/'data/raw/trajectories-0750am-0805am.txt').read_bytes()).hexdigest(),'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for folder in ['src','scripts'] for f in (ROOT/folder).rglob('*.py')}}
    (out/'run.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2));print(pd.DataFrame(quality).to_string(index=False))
if __name__=='__main__':main()
