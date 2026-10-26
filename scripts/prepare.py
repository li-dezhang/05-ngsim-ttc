"""Official TXT integrity, strict time window, pair validation and segmentation."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import json,hashlib
import pandas as pd
import numpy as np
from src.ngsim.core import COLS,FT,match_pairs,pair_reasons,segment_ids
def main():
    r=ROOT/'results/data';r.mkdir(parents=True,exist_ok=True);local=ROOT/'data/processed';local.mkdir(exist_ok=True)
    manifest=json.loads((ROOT/'data/manifest.json').read_text())
    for f in manifest['files']:assert hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest()==f['sha256']
    d=pd.read_csv(ROOT/'data/raw/trajectories-0750am-0805am.txt',sep=r'\s+',header=None,names=COLS)
    assert len(d.columns)==18 and d.index.equals(pd.RangeIndex(len(d)))
    assert not d.duplicated(['vehicle_id','frame_id']).any()
    assert (d.global_time-d.frame_id*100).nunique()==1
    d=d.sort_values(['vehicle_id','frame_id']).reset_index(drop=True);g=d.groupby('vehicle_id')
    raw_dt=g.global_time.diff();raw_df=g.frame_id.diff()
    s=pd.Timestamp('2005-06-15 07:50',tz='America/Los_Angeles').value//1_000_000;e=s+900_000
    in_window=d.global_time.ge(s)&d.global_time.lt(e);selected=d.loc[in_window].copy()
    p=match_pairs(selected);p['reason']=pair_reasons(p)
    exclusions=[dict(stage='time_window',reason='outside_0750_0805',n=int((~in_window).sum()))]
    exclusions += [dict(stage='pair_validation',reason=k,n=int(v)) for k,v in p.reason.value_counts().items() if k!='valid']
    invalid=p[p.reason!='valid'];invalid[['vehicle_id','frame_id','preceding','lane','local_y','leader_local_y','leader_length','reason']].to_csv(local/'invalid_pairs.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    p=p[p.reason=='valid'].copy().sort_values(['vehicle_id','frame_id']).reset_index(drop=True);p['segment']=segment_ids(p)
    segments=p.groupby('segment').agg(follower=('vehicle_id','first'),leader=('preceding','first'),lane=('lane','first'),n=('frame_id','size'),start_frame=('frame_id','first'),end_frame=('frame_id','last')).reset_index()
    segments['eligible_length']=segments.n.ge(23);segments.to_csv(r/'segments.csv',index=False)
    columns=['segment','vehicle_id','preceding','frame_id','global_time','lane','local_y','leader_local_y','length','leader_length','reported_speed','leader_reported_speed','space_headway']
    np.savez_compressed(local/'pairs.npz',**{c:p[c].to_numpy() for c in columns})
    quality=dict(raw_rows=len(d),raw_vehicles=int(d.vehicle_id.nunique()),raw_unique_frames=int(d.frame_id.nunique()),raw_start=str(pd.to_datetime(d.global_time.min(),unit='ms',utc=True).tz_convert('America/Los_Angeles')),raw_end=str(pd.to_datetime(d.global_time.max(),unit='ms',utc=True).tz_convert('America/Los_Angeles')),window_rows=len(selected),window_vehicles=int(selected.vehicle_id.nunique()),window_unique_frames=int(selected.frame_id.nunique()),duplicate_keys=0,missing_values=int(d.isna().sum().sum()),irregular_time_steps=int((raw_dt.notna()&raw_dt.ne(100)).sum()),irregular_frame_steps=int((raw_df.notna()&raw_df.ne(1)).sum()),backward_steps=int(g.local_y.diff().lt(0).sum()),variable_vehicle_lengths=int(g.length.nunique().gt(1).sum()),lane_changes=int((g.lane.diff().notna()&g.lane.diff().ne(0)).sum()),leader_changes=int((g.preceding.diff().notna()&g.preceding.diff().ne(0)).sum()),valid_pair_rows=len(p),pair_segments=len(segments),eligible_segments=int(segments.eligible_length.sum()),short_segment_rows=int(segments.loc[~segments.eligible_length,'n'].sum()),boundary_rows=int(segments.eligible_length.sum()*22),headway_max_abs_residual_ft=float((p.leader_local_y-p.local_y-p.space_headway).abs().max()),metres_per_foot=FT)
    exclusions += [dict(stage='support',reason='short_segment',n=quality['short_segment_rows']),dict(stage='support',reason='common_boundary_trim',n=quality['boundary_rows'])]
    pd.DataFrame(exclusions).to_csv(r/'exclusions.csv',index=False)
    pd.DataFrame([quality]).to_csv(r/'sample_counts.csv',index=False);(r/'quality.json').write_text(json.dumps(quality,indent=2)+'\n')
    d.describe().to_csv(r/'field_statistics.csv')
    dictionary=json.loads((ROOT/'data/raw/portal_metadata.json').read_text())
    pd.DataFrame([dict(field=c['fieldName'],description=c.get('description','')) for c in dictionary['columns'] if c['fieldName'] in ['vehicle_id','frame_id','global_time','local_x','local_y','v_length','v_vel','v_acc','lane_id','preceding','following','space_headway','time_headway']]).to_csv(r/'dictionary_extract.csv',index=False)
    print(json.dumps(quality,indent=2));print(pd.DataFrame(exclusions).to_string(index=False))
if __name__=='__main__':main()
