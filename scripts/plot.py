"""Render figures solely from saved real summaries and selected case tables."""
from pathlib import Path
import os,argparse,json
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'data/interim/mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
COLORS={'raw':'#384860','sg11':'#17807a','sg21':'#c15d23'}
LABELS={'raw':'Raw','sg11':'SG11','sg21':'SG21'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);a=p.parse_args()
    r=ROOT/'results'/a.run_id;out=ROOT/'figures'/a.run_id;out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':120,'savefig.dpi':160})
    def save(fig,name):fig.savefig(out/name,bbox_inches='tight',metadata={'Software':'P5 deterministic plotting'});plt.close(fig)
    s=pd.read_csv(r/'summary.csv');q=json.loads((ROOT/'results/data/quality.json').read_text());run=json.loads((r/'run.json').read_text())
    fig,ax=plt.subplots(figsize=(9,10));ax.axis('off')
    boxes=[f"Official original TXT\n{q['raw_rows']:,} vehicle-frames",f"Strict local 07:50–08:05\n{q['window_rows']:,} frames",f"Verify pair geometry\n{q['valid_pair_rows']:,} valid pairs",f"Continuous segments + common trim\n{run['processed_segments']:,} segments analyzed",'Raw / SG11 / SG21\nPositions → velocities + net gaps',f"Common method-valid support\n{run['common_valid_frames']:,} frames",'TTC = gap / positive closing speed\n<1.5 s and <3.0 s','All low frames → events ≥3 frames\nFrame Jaccard + 1:1 time overlap']
    for i,label in enumerate(boxes):
        y=.95-i*.125
        ax.text(.5,y,label,ha='center',va='center',fontsize=11,bbox=dict(boxstyle='round,pad=.7',fc='#e9f1f1',ec='#17807a'),transform=ax.transAxes)
        if i<7:ax.annotate('',xy=(.5,y-.085),xytext=(.5,y-.043),xycoords='axes fraction',arrowprops=dict(arrowstyle='->',color='#384860'))
    ax.set_title('Shared observations, consistent geometry, descriptive sensitivity',pad=20);save(fig,'01_workflow.png')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for j,thr in enumerate([1.5,3.]):
        v=s[s.threshold==thr];bars=axes[j].bar([LABELS[x] for x in v.method],v.events_ge3,color=[COLORS[x] for x in v.method]);axes[j].bar_label(bars,padding=3);axes[j].set_title(f'TTC < {thr:g} s');axes[j].set_ylabel('Events (≥3 consecutive frames)');axes[j].set_ylim(0,max(1,v.events_ge3.max()*1.22))
    fig.suptitle('Event counts on identical valid frame support');fig.tight_layout();save(fig,'04_event_counts.png')
    ecdf=pd.read_csv(r/'ttc_ecdf.csv');fig,ax=plt.subplots(figsize=(8,4.5))
    for name,g in ecdf.groupby('method',sort=False):ax.plot(g.ttc_s,g.cdf,label=LABELS[name],color=COLORS[name])
    for x in [1.5,3]:ax.axvline(x,color='gray',ls=':',lw=.8)
    ax.set(xlabel='TTC (s; display limited to 0–30 s)',ylabel='Conditional cumulative fraction',title='Finite TTC on common valid support');ax.legend();fig.tight_layout();save(fig,'05_ttc_distribution.png')
    c=pd.read_csv(r/'consistency.csv');fig,axes=plt.subplots(1,2,figsize=(9,4))
    for ax,thr in zip(axes,[1.5,3.]):
        matrix=np.eye(3);names=list(COLORS)
        for row in c[c.threshold==thr].itertuples():i=names.index(row.method_a);j=names.index(row.method_b);matrix[i,j]=matrix[j,i]=row.frame_jaccard
        ax.imshow(matrix,vmin=0,vmax=1,cmap='YlGnBu');ax.set_xticks(range(3),[LABELS[n] for n in names]);ax.set_yticks(range(3),[LABELS[n] for n in names]);ax.set_title(f'Low-frame Jaccard: <{thr:g} s')
        for i in range(3):
            for j in range(3):ax.text(j,i,'N/A' if np.isnan(matrix[i,j]) else f'{matrix[i,j]:.3f}',ha='center',va='center',color='white' if matrix[i,j]>.65 else 'black')
    fig.tight_layout();save(fig,'06_frame_consistency.png')
    for case in json.loads((r/'case_selection.json').read_text()):
        d=pd.read_csv(r/('case_'+case['case']+'.csv'));t=(d.global_time-d.global_time.iloc[0])/1000
        fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True)
        for name in COLORS:
            axes[0].plot(t,d[name+'_follower_y'],color=COLORS[name],label=LABELS[name]+' follower');axes[0].plot(t,d[name+'_leader_y'],color=COLORS[name],ls='--',alpha=.75)
            axes[1].plot(t,d[name+'_gap'],color=COLORS[name],label=LABELS[name])
            vals=d[name+'_ttc'].where(d.common_valid & np.isfinite(d[name+'_ttc']))
            axes[2].plot(t,vals,color=COLORS[name],lw=1.2,label=LABELS[name])
        axes[0].set_ylabel('Front position (m)');axes[0].legend(fontsize=9,ncol=3);axes[0].set_title(f"{case['case'].replace('_',' ')} | follower {int(d.vehicle_id.iloc[0])}, leader {int(d.preceding.iloc[0])}, segment {case['segment']}\nDashed: leader; solid: follower; case selected after analysis")
        axes[1].set_ylabel('Net gap (m)');axes[1].axhline(0,color='gray',ls=':')
        axes[2].set(xlabel='Elapsed time from displayed segment interior (s)',ylabel='TTC (s)',ylim=(0,6))
        axes[2].axhline(1.5,color='black',ls=':',label='1.5 s');axes[2].axhline(3,color='gray',ls='--',label='3 s');axes[2].legend(ncol=5,fontsize=9)
        fig.text(.5,.005,'TTC display is restricted to 0–6 s; nonclosing/invalid values are not drawn. Calculations use untruncated values.',ha='center',fontsize=8)
        fig.tight_layout(rect=(0,.025,1,1));save(fig,'02_03_case_'+case['case']+'.png')
    # Genuine rejected observations: no TTC is assigned to these values.
    invalid=pd.read_csv(ROOT/'data/processed/invalid_pairs.csv.gz');bad=invalid[invalid.reason.isin(['nonpositive_raw_gap','leader_not_ahead'])]
    if len(bad):
        sizes=bad.groupby(['vehicle_id','preceding']).size().sort_values(ascending=False);f,l=sizes.index[0];d=bad[(bad.vehicle_id==f)&(bad.preceding==l)].sort_values('frame_id');gap=(d.leader_local_y-d.leader_length-d.local_y)*(1200/3937)
        fig,ax=plt.subplots(figsize=(8,4));ax.scatter(d.frame_id,gap,s=12,color='#b13e42');ax.axhline(0,color='gray',ls=':');ax.set(xlabel='Original Frame_ID (points only; no gap interpolation)',ylabel='Recorded net gap (m)',title=f'Rejected overlap observations: follower {f}, leader {l}');fig.tight_layout();save(fig,'07_invalid_gap_example.png')
        (r/'invalid_case.json').write_text(json.dumps({'follower':int(f),'leader':int(l),'rejected_frames':len(d),'min_gap_m':float(gap.min()),'max_gap_m':float(gap.max()),'selection':'pair with most nonpositive-gap observations; illustrative only'},indent=2)+'\n')
    print(f'Figures rendered from {a.run_id} to {out.relative_to(ROOT)}')
if __name__=='__main__':main()
