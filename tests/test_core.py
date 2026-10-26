"""Synthetic fixtures validate definitions; they are not empirical trajectories."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from src.ngsim.core import match_pairs,pair_reasons,process_segment,ttc,event_runs,overlap_matches,FT,segment_ids
class Tests(unittest.TestCase):
    def pair(self):
        return pd.DataFrame({'vehicle_id':[1,2],'preceding':[2,0],'following':[0,1],'frame_id':[10,10],'global_time':[1000,1000],'lane':[1,1],'local_x':[2.,2.],'local_y':[10.,30.],'length':[10.,5.],'reported_speed':[15.,10.],'space_headway':[20.,0.]})
    def test_pair(self):
        p=match_pairs(self.pair());self.assertEqual(p.leader_local_y.iloc[0],30);self.assertEqual(pair_reasons(p)[0],'valid')
    def test_no_leader(self):self.assertEqual(pair_reasons(match_pairs(self.pair()))[1],'no_leader')
    def test_different_frame(self):
        d=self.pair();d.loc[1,'frame_id']=11;self.assertEqual(pair_reasons(match_pairs(d))[0],'missing_leader_same_frame')
    def test_gap_length(self):
        p=match_pairs(self.pair());self.assertEqual((p.leader_local_y-p.leader_length-p.local_y).iloc[0],15)
    def test_nonclosing(self):
        values,valid=ttc([10,10,0],[5,4,8],[5,5,1]);self.assertTrue(np.isinf(values[:2]).all());self.assertTrue(np.isnan(values[2]));self.assertFalse(valid[2])
    def test_units_derivative(self):
        t=np.arange(50)*.1;f=t*10*FT;l=f+30*FT;d=process_segment(f,l,np.full(50,5*FT),t,0)
        np.testing.assert_allclose(d['follower_speed'],10*FT);np.testing.assert_allclose(d['gap'],25*FT)
    def test_common_support(self):
        t=np.arange(50)*.1
        self.assertEqual([len(process_segment(t,t+20,np.ones(50),t,w)['gap']) for w in [0,11,21]],[28]*3)
    def test_stationary_exact_zero(self):
        t=np.arange(200)*.1
        for w in [0,11,21]:
            d=process_segment(np.full(200,317.123456),np.full(200,330.123456),np.ones(200),t,w)
            np.testing.assert_array_equal(d['follower_speed'],np.zeros(178))
    def test_short(self):
        for w in [0,11,21]:
            with self.assertRaises(ValueError):process_segment(np.arange(20),np.arange(20)+10,np.ones(20),np.arange(20)*.1,w)
    def test_event_count(self):
        e=event_runs([0]*9,list(range(9)),[1,1,1,0,1,1,0,1,1]);self.assertEqual(len(e),1);self.assertAlmostEqual(e[0]['duration_s'],.3)
    def test_threshold(self):
        values,_=ttc(np.array([1.,2.,4.]),np.full(3,2.),np.ones(3));self.assertTrue(np.all((values<1.5)<=(values<3.0)))
    def test_breaks(self):
        self.assertEqual(len(event_runs([0,0,0,1,1,1],[0,1,2,3,4,5],[True]*6)),2)
        self.assertEqual(len(event_runs([0]*6,[0,1,2,4,5,6],[True]*6)),2)
    def test_one_to_one_overlap(self):
        a=pd.DataFrame({'segment':[1],'start_frame':[1],'end_frame':[10]})
        b=pd.DataFrame({'segment':[1,1],'start_frame':[1,7],'end_frame':[4,10]})
        m,edges,_,_=overlap_matches(a,b);self.assertEqual(len(m),1);self.assertEqual(edges,2)
    def test_lane_change(self):
        p=self.pair().iloc[[0,0,0]].copy();p['frame_id']=[1,2,3];p['global_time']=[100,200,300];p['lane']=[1,1,2];self.assertEqual(segment_ids(p).tolist(),[0,0,1])
    def test_gaps_not_smoothed(self):
        t=np.r_[np.arange(25)*.1,np.arange(25)*.1+4]
        with self.assertRaises(ValueError):process_segment(t,t+10,np.ones(50),t,21)
if __name__=='__main__':unittest.main()
