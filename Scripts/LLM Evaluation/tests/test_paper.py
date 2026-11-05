import copy
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import scoring
import evaluate


def control():
    return {'task':'derive_control_dae','difficulty':'easy','control_units':['PI'],
            'inputs':['U'],'states':['X'],'outputs':['Y'],
            'differential_equations':['dX_dt=U'],'algebraic_equations':['Y=X'],'notes':''}


def network():
    buses=[]
    for i,t in [(1,3),(2,1)]:
        row={k:0.0 for k in scoring.BUS_FIELDS}
        row.update(Bus=i,Type=t,ACorDCorIC='AC',Apparatus=0,Number=0)
        row['Area No.']=0;buses.append(row)
    return {'Bus':buses,'Network':[{'FromBus':1,'ToBus':2,'R (pu)':0.1,'X (pu)':0.2,'Turn':1.0}]}


def pf(pred,gold,matched):
    p=matched/(pred+1e-8);r=matched/(gold+1e-8)
    return 2*p*r/(p+r+1e-8)


class PaperTests(unittest.TestCase):
    def test_device_weights_and_nonempty_coverage(self):
        g=control();g['states']=[];g['differential_equations']=[]
        result=scoring.score(g,g,'device_control')
        expected=.2+.2*4/6+.3*pf(3,3,3)+.3*pf(1,1,1)
        self.assertAlmostEqual(result['score'],expected)

    def test_lowercase_and_set_equations(self):
        g=control();p=copy.deepcopy(g)
        p['differential_equations']=['dx_dt = u']*2
        p['algebraic_equations']=['y = x']
        self.assertAlmostEqual(scoring.score(p,g,'device_control')['score'],scoring.score(g,g,'device_control')['score'])

    def test_empty_f1_uses_paper_formula(self):
        self.assertEqual(scoring.f1([],[]),0)

    def test_missing_field_keeps_other_components(self):
        g=control();p=copy.deepcopy(g);del p['notes']
        expected=scoring.score(g,g,'device_control')['score']-.2
        self.assertAlmostEqual(scoring.score(p,g,'device_control')['score'],expected)

    def test_branch_scales_and_weights(self):
        g=network();p=copy.deepcopy(g);p['Network'][0]['R (pu)']=0.11
        expected=.15+.25*pf(2,2,2)+.35*pf(1,1,1)+.15*(1-.05/(3+1e-8))+.10*2/(2+1e-8)
        self.assertAlmostEqual(scoring.score(p,g,'network_topology')['score'],expected)

    def test_type_accuracy_and_non_scored_bus_parameters(self):
        g=network();p=copy.deepcopy(g);p['Bus'][0]['PG']=999999
        self.assertEqual(scoring.score(p,g,'network_topology')['score'],scoring.score(g,g,'network_topology')['score'])
        p['Bus'][0]['Type']=2
        delta=scoring.score(g,g,'network_topology')['score']-scoring.score(p,g,'network_topology')['score']
        self.assertAlmostEqual(delta,.1/(2+1e-8))

    def test_undirected_parallel_matching(self):
        g=network();g['Network'].append({**g['Network'][0],'R (pu)':0.4})
        p=copy.deepcopy(g);p['Bus'].reverse();p['Network'].reverse()
        for row in p['Network']:row['FromBus'],row['ToBus']=row['ToBus'],row['FromBus']
        self.assertEqual(scoring.score(p,g,'network_topology')['score'],scoring.score(g,g,'network_topology')['score'])

    def test_explicit_bus_correspondence(self):
        g=network();p=copy.deepcopy(g)
        for b in p['Bus']:b['Bus']+=100
        for e in p['Network']:e['FromBus']+=100;e['ToBus']+=100
        try:result=scoring.score(p,g,'network_topology',bus_mapping={'101':1,'102':2})
        except TypeError as exc:self.fail(str(exc))
        self.assertEqual(result['score'],scoring.score(g,g,'network_topology')['score'])

    def test_no_matched_edges_param_score_is_one(self):
        g=network();p=copy.deepcopy(g);p['Network']=[]
        result=scoring.score(p,g,'network_topology')
        self.assertEqual(result.get('param_score'),1)

    def test_invalid_network_retains_literal_empty_match_term(self):
        result=scoring.score(None,network(),'network_topology')
        self.assertEqual(result['json_valid'],0)
        self.assertEqual(result['param_score'],1)
        self.assertAlmostEqual(result['score'],.15)

    def test_invalid_correspondence_is_rejected(self):
        for mapping in ({'1':1,'2':1},{'1':1},{'1':1,'2':99}, {'1':1,'01':2}):
            with self.assertRaises(ValueError):
                scoring.score(network(),network(),'network_topology',bus_mapping=mapping)

    def test_parallel_pairing_uses_parameter_error(self):
        g=network();g['Network'].append({**g['Network'][0],'R (pu)':.4})
        p=copy.deepcopy(g);p['Network'][0]['R (pu)']=.12;p['Network'].reverse()
        expected=1-(.02/.2)/(2*3+1e-8)
        self.assertAlmostEqual(scoring.score(p,g,'network_topology')['param_score'],expected)

    def test_incomplete_difficulties_do_not_fabricate_macro(self):
        rows=[{'model':'m','model_id':'id','task':'device_control','difficulty':'easy','mean_score':.6}]
        result=evaluate.task_summary(rows)
        self.assertFalse(result[0]['complete_difficulties'])
        self.assertIsNone(result[0]['macro_score'])

    def test_missing_latency_is_not_imputed_to_zero(self):
        rows=[{'model':'m','model_id':'id','task':'device_control','difficulty':'easy',
               'prediction':None,'metrics':{'score':0,'schema_valid':False}}]
        result=evaluate.summary(rows)[0]
        self.assertEqual(result['parse_rate'],0)
        self.assertEqual(result['latency_count'],0)
        self.assertIsNone(result['mean_latency_seconds'])

    def test_summary_macro_parse_and_latency(self):
        rows=[]
        for difficulty,count,value in [('easy',1,.9),('medium',4,.3),('hard',1,.6)]:
            rows.extend({'model':'m','model_id':'id','task':'device_control','difficulty':difficulty,
                         'prediction':{},'pure_json':True,'total_latency_ms':2000,
                         'metrics':{'score':value,'schema_valid':True}} for _ in range(count))
        s=evaluate.summary(rows)
        self.assertEqual(s[0].get('parse_rate'),1)
        self.assertEqual(s[0].get('mean_latency_seconds'),2)
        aggregate=getattr(evaluate,'task_summary',lambda x:[])(s)
        self.assertEqual(len(aggregate),1)
        self.assertAlmostEqual(aggregate[0]['macro_score'],.6)


if __name__=='__main__':unittest.main()
