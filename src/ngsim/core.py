"""Consistent pair geometry, smoothing and event definitions."""
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching
FT=1200/3937
METHODS={'raw':0,'sg11':11,'sg21':21}
COLS='vehicle_id frame_id total_frames global_time local_x local_y global_x global_y length width v_class reported_speed reported_acc lane preceding following space_headway time_headway'.split()
def match_pairs(d):
    if d.duplicated(['vehicle_id','frame_id']).any():raise ValueError('Duplicate vehicle/frame')
    leader=d[['vehicle_id','frame_id','global_time','local_y','length','lane','following','reported_speed']].rename(columns={c:'leader_'+c for c in ['global_time','local_y','length','lane','following','reported_speed']})
    return d.merge(leader,left_on=['preceding','frame_id'],right_on=['vehicle_id','frame_id'],how='left',suffixes=('','_lookup'),validate='many_to_one')
def pair_reasons(p):
    reason=np.full(len(p),'valid',dtype=object)
    def mark(mask,label):reason[(reason=='valid')&np.asarray(mask)]=label
    mark(p.preceding.eq(0),'no_leader')
    mark(p.leader_local_y.isna(),'missing_leader_same_frame')
    mark(p.global_time.ne(p.leader_global_time),'timestamp_mismatch')
    mark(p.lane.ne(p.leader_lane)|~p.lane.isin(range(1,9)),'lane_mismatch')
    mark(p.leader_following.ne(p.vehicle_id),'nonreciprocal_relationship')
    mark(~np.isfinite(p[['local_x','local_y','leader_local_y','length','leader_length','reported_speed','leader_reported_speed']]).all(axis=1),'missing_or_nonfinite')
    mark(~(p.length*FT).between(1,30)|~(p.leader_length*FT).between(1,30),'invalid_length')
    mark(~(p.reported_speed*FT).between(0,55)|~(p.leader_reported_speed*FT).between(0,55),'invalid_reported_speed')
    front=p.leader_local_y-p.local_y;gap=(front-p.leader_length)*FT
    mark(front.le(0),'leader_not_ahead')
    mark(gap.le(0),'nonpositive_raw_gap')
    mark((front-p.space_headway).abs().gt(.0200001),'headway_inconsistent')
    return reason
def segment_ids(p):
    change=(p.vehicle_id.ne(p.vehicle_id.shift())|p.preceding.ne(p.preceding.shift())|p.lane.ne(p.lane.shift())|p.frame_id.diff().ne(1)|p.global_time.diff().ne(100))
    return change.cumsum().to_numpy(dtype=np.int64)-1
def process_segment(follower,leader,length,t,window):
    follower,leader,length,t=map(np.asarray,[follower,leader,length,t])
    if len(t)<23 or (window and len(t)<window):raise ValueError('Short segment')
    if not np.allclose(np.diff(t),.1,rtol=0,atol=1e-9):raise ValueError('Irregular segment')
    if window:
        follower=savgol_filter(follower,window,2,mode='interp')
        leader=savgol_filter(leader,window,2,mode='interp')
    # Stable central difference: stationary identical positions must give exactly zero.
    # np.gradient with floating irregular-spacing coefficients introduced cancellation.
    vf=np.full(len(t),np.nan);vl=vf.copy()
    vf[1:-1]=(follower[2:]-follower[:-2])/(t[2:]-t[:-2])
    vl[1:-1]=(leader[2:]-leader[:-2])/(t[2:]-t[:-2])
    af=np.full(len(t),np.nan);al=af.copy()
    af[1:-1]=np.diff(follower,n=2)/.01;al[1:-1]=np.diff(leader,n=2)/.01
    sl=slice(11,-11)
    return {k:np.asarray(v)[sl] for k,v in dict(follower_y=follower,leader_y=leader,gap=leader-length-follower,follower_speed=vf,leader_speed=vl,follower_acc=af,leader_acc=al).items()}
def ttc(gap,vf,vl):
    gap,vf,vl=np.broadcast_arrays(gap,vf,vl)
    valid=np.isfinite(gap)&np.isfinite(vf)&np.isfinite(vl)&(gap>0)&(vf>=0)&(vl>=0)&(vf<=55)&(vl<=55)
    closing=vf-vl;out=np.full(gap.shape,np.nan)
    out[valid&(closing<=0)]=np.inf
    np.divide(gap,closing,out=out,where=valid&(closing>0))
    return out,valid
def event_runs(segment,frame,low,min_frames=3):
    segment,frame,low=map(np.asarray,[segment,frame,low])
    ids=np.flatnonzero(low)
    if not len(ids):return []
    split=np.r_[0,np.flatnonzero((np.diff(frame[ids])!=1)|(np.diff(segment[ids])!=0))+1,len(ids)]
    events=[]
    for a,b in zip(split[:-1],split[1:]):
        ix=ids[a:b]
        if len(ix)>=min_frames:events.append({'segment':int(segment[ix[0]]),'start_frame':int(frame[ix[0]]),'end_frame':int(frame[ix[-1]]),'frames':len(ix),'duration_s':len(ix)*.1,'elapsed_span_s':(frame[ix[-1]]-frame[ix[0]])*.1})
    return events
def overlap_matches(a,b):
    """Maximum cardinality matching: each event can contribute at most once."""
    matches=[];edges_total=0;ambiguous_a=0;ambiguous_b=0
    if a.empty or b.empty:return matches,0,0,0
    for seg in sorted(set(a.segment)&set(b.segment)):
        aa=a[a.segment==seg];bb=b[b.segment==seg]
        edges=(aa.start_frame.to_numpy()[:,None]<=bb.end_frame.to_numpy()[None,:])&(bb.start_frame.to_numpy()[None,:]<=aa.end_frame.to_numpy()[:,None])
        edges_total+=int(edges.sum());ambiguous_a+=int((edges.sum(axis=1)>1).sum());ambiguous_b+=int((edges.sum(axis=0)>1).sum())
        match=maximum_bipartite_matching(csr_matrix(edges),perm_type='column')
        matches.extend((int(aa.index[i]),int(bb.index[j])) for i,j in enumerate(match) if j>=0)
    return matches,edges_total,ambiguous_a,ambiguous_b
