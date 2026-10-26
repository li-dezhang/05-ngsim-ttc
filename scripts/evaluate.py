"""Recompute frame, event and overlap summaries from saved processed arrays."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import argparse,itertools,json
import numpy as np
import pandas as pd
from src.ngsim.core import METHODS,event_runs,overlap_matches
EVENT_COLUMNS=['method','threshold','event_id','segment','follower','leader','start_frame','end_frame','frames','duration_s','elapsed_span_s','min_ttc']
def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);a=p.parse_args();r=ROOT/'results'/a.run_id
    z=np.load(ROOT/'data/processed'/f'{a.run_id}.npz');d={k:z[k] for k in z.files};common=d['common_valid'];seg=d['segment'];frame=d['frame_id']
    meta={int(s):(int(f),int(l)) for s,f,l in zip(seg,d['vehicle_id'],d['preceding'])}
    finite_common=common.copy()
    for name in METHODS:finite_common&=np.isfinite(d[name+'_ttc'])
    cuts=np.r_[0,np.flatnonzero(np.diff(seg)!=0)+1,len(seg)]
    bounds={int(seg[a]):(a,b) for a,b in zip(cuts[:-1],cuts[1:])}
    summary=[];events=[];distributions=[];ecdf=[]
    masks={}
    for name in METHODS:
        values=d[name+'_ttc'];finite=values[common&np.isfinite(values)]
        for scope,mask in [('method_finite_on_common_valid',common&np.isfinite(values)),('common_finite_all_methods',finite_common)]:
            v=values[mask];q=np.quantile(v,[.01,.05,.25,.5,.75,.95,.99]) if len(v) else [np.nan]*7
            distributions.append(dict(method=name,scope=scope,n=len(v),**dict(zip(['p01','p05','p25','p50','p75','p95','p99'],q))))
        for threshold in [1.5,3.0]:
            low=common&(values<threshold);masks[name,threshold]=low
            all_runs=event_runs(seg,frame,low,min_frames=1);es=event_runs(seg,frame,low,min_frames=3)
            for i,e in enumerate(es):
                left,right=bounds[e['segment']];start=left+int(e['start_frame']-frame[left]);stop=left+int(e['end_frame']-frame[left])+1
                mask=slice(start,stop)
                events.append(dict(method=name,threshold=threshold,event_id=i,follower=meta[e['segment']][0],leader=meta[e['segment']][1],min_ttc=float(values[mask].min()),**e))
            durations=[e['duration_s'] for e in es]
            summary.append(dict(method=name,threshold=threshold,common_frames=int(common.sum()),common_segments=int(np.unique(seg[common]).size),finite_ttc=int(len(finite)),nonclosing_frames=int(np.isinf(values[common]).sum()),low_frames=int(low.sum()),low_fraction_common=float(low.sum()/common.sum()),low_fraction_finite=float(low.sum()/len(finite)) if len(finite) else np.nan,all_low_runs=len(all_runs),events_ge3=len(es),retained_event_frames=sum(e['frames'] for e in es),mean_duration_s=float(np.mean(durations)) if durations else np.nan,median_duration_s=float(np.median(durations)) if durations else np.nan,total_event_exposure_s=float(sum(durations))))
        ordered=np.sort(finite)
        for x in np.linspace(0,30,301):ecdf.append(dict(method=name,ttc_s=x,cdf=float(np.searchsorted(ordered,x,side='right')/len(ordered)) if len(ordered) else np.nan))
    event_df=pd.DataFrame(events,columns=EVENT_COLUMNS);event_df.to_csv(r/'events.csv',index=False)
    comparisons=[]
    for threshold in [1.5,3.0]:
        for aa,bb in itertools.combinations(METHODS,2):
            ma,mb=masks[aa,threshold],masks[bb,threshold];intersection=int((ma&mb).sum());union=int((ma|mb).sum())
            ea=event_df[(event_df.method==aa)&(event_df.threshold==threshold)];eb=event_df[(event_df.method==bb)&(event_df.threshold==threshold)]
            matches,edges,split_a,merge_b=overlap_matches(ea,eb);n=len(matches)
            comparisons.append(dict(threshold=threshold,method_a=aa,method_b=bb,intersection_low_frames=intersection,union_low_frames=union,frame_jaccard=intersection/union if union else np.nan,events_a=len(ea),events_b=len(eb),matched_events=n,match_fraction_a=n/len(ea) if len(ea) else np.nan,match_fraction_b=n/len(eb) if len(eb) else np.nan,disappeared_a=len(ea)-n,new_b=len(eb)-n,overlap_edges=edges,split_candidates_a=split_a,merge_candidates_b=merge_b))
    pd.DataFrame(summary).to_csv(r/'summary.csv',index=False);pd.DataFrame(distributions).to_csv(r/'ttc_distribution.csv',index=False);pd.DataFrame(ecdf).to_csv(r/'ttc_ecdf.csv',index=False);pd.DataFrame(comparisons).to_csv(r/'consistency.csv',index=False)
    # Choose reproducible illustrative segments: strongest frame disagreement at 1.5,
    # then largest threshold change under SG21. Not a representative random sample.
    selection=[]
    for label,indicator in [('smoothing_disagreement',masks['raw',1.5]^masks['sg21',1.5]),('threshold_change',masks['sg21',3.0]&~masks['sg21',1.5])]:
        counts=pd.Series(seg[indicator]).value_counts()
        if len(counts):
            candidates=counts[counts==counts.max()].index;chosen=int(min(candidates));selection.append(dict(case=label,segment=chosen,criterion_count=int(counts.max())))
    short=event_runs(seg,frame,masks['raw',1.5],min_frames=1)
    short=[e for e in short if e['frames']<3]
    if short:
        counts=pd.Series([e['segment'] for e in short]).value_counts();chosen=int(min(counts[counts==counts.max()].index))
        selection.append(dict(case='short_raw_spikes',segment=chosen,criterion_count=int(counts.max())))
    for case in selection:
        mask=seg==case['segment']
        pd.DataFrame({k:v[mask] for k,v in d.items()}).to_csv(r/('case_'+case['case']+'.csv'),index=False)
    (r/'case_selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    print(pd.DataFrame(summary).to_string(index=False));print(pd.DataFrame(comparisons).to_string(index=False))
if __name__=='__main__':main()
