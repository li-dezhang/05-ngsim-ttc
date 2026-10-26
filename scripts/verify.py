"""Independently check saved frame/event accounting, then regenerate CSVs and PNGs."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,datetime
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--compare-to');a=p.parse_args()
    r=ROOT/'results'/a.run_id;fig=ROOT/'figures'/a.run_id
    z=np.load(ROOT/'data/processed'/f'{a.run_id}.npz');common=z['common_valid'];seg=z['segment'];frames=z['frame_id']
    summary=pd.read_csv(r/'summary.csv');events=pd.read_csv(r/'events.csv')
    checks=0
    for row in summary.itertuples():
        values=z[row.method+'_ttc'];low=common&(values<row.threshold);selected=np.flatnonzero(low)
        runs=[];run=[]
        for i in selected:
            if run and (seg[i]!=seg[run[-1]] or frames[i]!=frames[run[-1]]+1):
                if len(run)>=3:runs.append(run)
                run=[]
            run.append(i)
        if len(run)>=3:runs.append(run)
        actual=events[(events.method==row.method)&(events.threshold==row.threshold)]
        expected=[(int(seg[x[0]]),int(frames[x[0]]),int(frames[x[-1]]),len(x)) for x in runs]
        observed=list(actual[['segment','start_frame','end_frame','frames']].itertuples(index=False,name=None))
        assert expected==observed
        assert row.events_ge3==len(runs) and row.low_frames==len(selected)
        assert row.common_frames==common.sum() and row.finite_ttc==np.isfinite(values[common]).sum()
        assert row.retained_event_frames==sum(map(len,runs))
        assert np.isclose(row.low_fraction_common,low.sum()/common.sum())
        assert np.isclose(row.total_event_exposure_s,sum(map(len,runs))*.1)
        checks+=1
    for row in pd.read_csv(r/'consistency.csv').itertuples():
        x=common&(z[row.method_a+'_ttc']<row.threshold);y=common&(z[row.method_b+'_ttc']<row.threshold)
        assert row.intersection_low_frames==(x&y).sum() and row.union_low_frames==(x|y).sum()
        assert np.isclose(row.frame_jaccard,(x&y).sum()/(x|y).sum(),equal_nan=True)
        assert row.disappeared_a+row.matched_events==row.events_a and row.new_b+row.matched_events==row.events_b
        checks+=1
    def fingerprints():
        return {str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in [*r.glob('*.csv'),*fig.glob('*.png')]}
    before=fingerprints()
    with (r/'rescore.txt').open('w') as out:
        subprocess.run([sys.executable,'scripts/evaluate.py','--run-id',a.run_id],cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,check=True)
        subprocess.run([sys.executable,'scripts/plot.py','--run-id',a.run_id],cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,check=True)
    after=fingerprints();assert before==after,'Regenerated CSV/image differs'
    comparison=None
    if a.compare_to:
        prior=np.load(ROOT/'data/processed'/f'{a.compare_to}.npz');assert set(prior.files)==set(z.files)
        for k in z.files:np.testing.assert_array_equal(z[k],prior[k])
        for f in r.glob('*.csv'):
            other=ROOT/'results'/a.compare_to/f.name
            assert other.read_bytes()==f.read_bytes(),f.name
        comparison={'run':a.compare_to,'array_columns_equal':len(z.files),'csv_equal':len(list(r.glob('*.csv')))}
    record={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'independent_summary_checks':checks,'regenerated_files_identical':len(after),'full_repeat_comparison':comparison,'sha256':after}
    (r/'verification.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
if __name__=='__main__':main()
