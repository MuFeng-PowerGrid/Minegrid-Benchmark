import argparse
import copy
from collections import Counter
import io
import itertools
import json
import os
from pathlib import Path
import random
import re
import math
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
import evaluate
from core import client, config, data, scoring


def expected_identity(sample):
    g = sample['label']
    eps = 1e-8
    def match(n):
        p = n / (n + eps)
        return 2 * p * p / (2 * p + eps)
    if sample['task'] == 'device_control':
        keys = ['control_units', 'inputs', 'states', 'outputs', 'differential_equations', 'algebraic_equations']
        coverage = sum(bool(g[k]) for k in keys) / 6
        text = ' '.join(x for k in keys[1:] for x in g[k])
        symbols = set(x.lower() for x in re.findall(r'[A-Za-z_][A-Za-z0-9_]*', text))
        eq = set(re.sub(r'\s+', '', x).lower() for k in keys[4:] for x in g[k])
        return .2 + .2 * coverage + .3 * match(len(symbols)) + .3 * match(len(eq))
    nodes, edges = len(g['Bus']), len(g['Network'])
    return .15 + .25 * match(nodes) + .35 * match(edges) + .15 + .1 * nodes / (nodes + eps)


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(os.environ.get('MINEGRID_DATASET_ROOT', PACKAGE.parents[1]))
        cls.samples, cls.hashes = data.load(cls.root)
        cls.gold = {s['id']: s for s in cls.samples}
        cls.device = next(s['label'] for s in cls.samples if s['task'] == 'device_control' and not s['label']['states'])
        cls.network = cls.gold['net_medium_0213']['label']

    def test_all_reference_answers_follow_paper_formula(self):
        self.assertEqual(len(self.samples), 1429)
        for s in self.samples:
            with self.subTest(id=s['id']):
                result = scoring.score(s['label'], s['label'], s['task'])
                self.assertTrue(result['schema_valid'])
                self.assertAlmostEqual(result['score'], expected_identity(s), places=12)

    def test_dataset_counts_and_confirmed_parallel_branches(self):
        counts=Counter((s['task'],s['difficulty']) for s in self.samples)
        self.assertEqual(counts,{('device_control','easy'):76,('device_control','medium'):593,('device_control','hard'):366,
                                 ('network_topology','easy'):38,('network_topology','medium'):222,('network_topology','hard'):134})
        for sid,pair,count,total in [('net_medium_0013',(2,3),1,19),('net_medium_0213',(1,2),2,21),('net_hard_0005',(102,217),4,120)]:
            edges=self.gold[sid]['label']['Network']
            self.assertEqual(len(edges),total)
            self.assertEqual(Counter(tuple(sorted((e['FromBus'],e['ToBus']))) for e in edges)[pair],count)

    def test_empty_arrays_and_lowercase_equations(self):
        self.assertAlmostEqual(scoring.score(self.device, self.device, 'device_control')['score'], expected_identity({'task':'device_control','label':self.device}))
        g = copy.deepcopy(self.device);g['algebraic_equations'] = ['Y=K*x']
        p = copy.deepcopy(g);p['algebraic_equations'] = ['y=k*x']
        self.assertEqual(scoring.score(p, g, 'device_control')['score'], scoring.score(g, g, 'device_control')['score'])

    def test_parallel_multiplicity(self):
        p = copy.deepcopy(self.network)
        p['Network'] = list({(e['FromBus'], e['ToBus']): e for e in p['Network']}.values())
        self.assertLess(len(p['Network']), len(self.network['Network']))
        self.assertLess(scoring.score(p, self.network, 'network_topology')['score'], 1)

    def test_reordered_rows_match(self):
        p = copy.deepcopy(self.network);p['Network'].reverse();p['Bus'].reverse()
        self.assertAlmostEqual(scoring.score(p, self.network, 'network_topology')['score'], 1)

    def test_non_paper_bus_parameters_do_not_change_score(self):
        for field in ('PG', 'PL', 'V', 'Base (kV)', 'Qmin', 'Pmax'):
            p = copy.deepcopy(self.network);p['Bus'][0][field] += 10
            self.assertEqual(scoring.score(p, self.network, 'network_topology')['score'], scoring.score(self.network, self.network, 'network_topology')['score'])

    def test_bad_predictions_do_not_raise(self):
        for p in (None, [], {}, {'Bus':['bad'], 'Network':[]}, {'Bus':[None]}, True):
            for task, gold in [('device_control', self.device), ('network_topology', self.network)]:
                result = scoring.score(p, gold, task)
                self.assertTrue(math.isfinite(result['score']))
                self.assertTrue(0 <= result['score'] <= 1)
                self.assertFalse(result['schema_valid'])
                self.assertIn('validation_error', result)

    def test_nonfinite_and_nonintegral_values(self):
        for field, value in [('Bus', 1.1), ('PG', float('nan')), ('Type', 99), ('V', True)]:
            p = copy.deepcopy(self.network);p['Bus'][0][field] = value
            self.assertFalse(scoring.score(p, self.network, 'network_topology')['schema_valid'])

    def test_duplicate_bus_and_bad_endpoint(self):
        p=copy.deepcopy(self.network);p['Bus'].append(p['Bus'][0])
        self.assertFalse(scoring.score(p,self.network,'network_topology')['schema_valid'])
        p=copy.deepcopy(self.network);p['Network'][0]['FromBus']=-123
        self.assertFalse(scoring.score(p,self.network,'network_topology')['schema_valid'])

    def test_parallel_assignment_matches_brute_force(self):
        rng=random.Random(7)
        for height,width in [(1,3),(3,1),(3,3),(2,4)]:
            values=[[rng.random() for _ in range(width)] for _ in range(height)]
            n=max(height,width)
            pad=[[values[i][j] if i<height and j<width else 0 for j in range(n)] for i in range(n)]
            expected=max(sum(pad[i][order[i]] for i in range(n)) for order in itertools.permutations(range(n)))
            self.assertAlmostEqual(scoring.assignment_value(values),expected)

    def test_json_contract(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '```json\n{}\n```', 'Explanation: {}'):
            with self.assertRaises(ValueError):scoring.parse_json(text)

    def test_missing_or_escaped_files_rejected(self):
        for name in ('../missing', 'Multimodal/missing.png', 'C:/x', '/x', 'Multimodal\\x'):
            with self.assertRaises(ValueError):data.local_file(self.root.resolve(),name)

    def test_missing_image_is_not_silently_skipped(self):
        original=data.local_file
        def missing(root,name):
            if name.startswith('Multimodal/'):raise ValueError('Missing test image')
            return original(root,name)
        with patch.object(data,'local_file',side_effect=missing):
            with self.assertRaisesRegex(ValueError,'Missing test image'):data.load(self.root)

    def test_language_selection(self):
        samples,_=data.load(self.root,'en')
        self.assertEqual([x['id'] for x in samples],[x['id'] for x in self.samples])
        self.assertNotEqual(samples[0]['prompt'],self.samples[0]['prompt'])

    def test_configuration_and_selection(self):
        cfg=config.runtime(PACKAGE/'configs/default.yaml',self.root)
        cfg.update(tasks=['device_control'],difficulties=['hard'],max_samples_per_group=2)
        selected=evaluate.select(self.samples,cfg)
        self.assertEqual(len(selected),2)
        self.assertTrue(all(x['difficulty']=='hard' and x['task']=='device_control' for x in selected))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'bad.yaml';p.write_text('a: 1\na: 2\n')
            with self.assertRaises(ValueError):config.read_yaml(p)
            p.write_text('save_raw_only: true\n')
            with self.assertRaises(ValueError):config.runtime(p)

    def test_model_environment_and_identity(self):
        with patch.dict(os.environ, {'MINEGRID_BASE_URL':'https://example.invalid/v1','MINEGRID_MODEL':'actual-id'}):
            models=config.models(PACKAGE/'configs/models.yaml')
        self.assertEqual(models[0]['model'],'actual-id')
        self.assertNotIn('api_key',models[0])
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ValueError):config.models(PACKAGE/'configs/models.yaml')

    def test_client_explicit_request_and_retry(self):
        model={'name':'Qwen','model':'actual-id','base_url':'https://example.invalid/v1','api_key_env':'TEST_KEY','request_options':{'temperature':0.3}}
        cfg={'retries':1,'retry_wait_seconds':0,'timeout_seconds':2}
        response={'model':'served-id','choices':[{'message':{'content':'{}'},'finish_reason':'stop'}]}
        requests=[]
        def fake(request,timeout):
            requests.append(json.loads(request.data))
            if len(requests)==1:raise HTTPError(request.full_url,429,'rate limit',{},None)
            return io.BytesIO(json.dumps(response).encode())
        with patch.dict(os.environ,{'TEST_KEY':'secret'}),patch.object(client,'urlopen',side_effect=fake):
            result=client.call(model,self.samples[0],self.root,cfg)
        self.assertEqual(result['attempts'],2);self.assertIsNone(result['error'])
        self.assertEqual(result['model_id'],'actual-id');self.assertEqual(result['response_model_id'],'served-id')
        self.assertNotIn('reasoning_effort',requests[0]);self.assertEqual(requests[0]['temperature'],0.3)
        self.assertNotIn('secret',json.dumps(result))
        self.assertGreaterEqual(result['total_latency_ms'],0)

    def test_client_strict_json_no_format_retries(self):
        model={'model':'id','base_url':'https://example.invalid/v1','api_key_env':'TEST_KEY','request_options':{}}
        response={'choices':[{'message':{'content':'```json\n{}\n```'},'finish_reason':'stop'}]}
        with patch.dict(os.environ,{'TEST_KEY':'secret'}),patch.object(client,'urlopen',return_value=io.BytesIO(json.dumps(response).encode())) as mock:
            result=client.call(model,self.samples[0],self.root,{'retries':2,'retry_wait_seconds':0,'timeout_seconds':2})
        self.assertFalse(result['pure_json']);self.assertIsNone(result['prediction']);self.assertEqual(mock.call_count,1)

    def test_client_nonretryable_and_exhausted_errors(self):
        model={'model':'id','base_url':'https://example.invalid/v1','api_key_env':'TEST_KEY','request_options':{}}
        for status,expected_attempts in [(400,1),(503,3)]:
            def fail(request,timeout):raise HTTPError(request.full_url,status,'private detail',{},None)
            with patch.dict(os.environ,{'TEST_KEY':'secret'}),patch.object(client,'urlopen',side_effect=fail):
                result=client.call(model,self.samples[0],self.root,{'retries':2,'retry_wait_seconds':0,'timeout_seconds':2})
            self.assertEqual(result['attempts'],expected_attempts)
            self.assertEqual(result['error'],'HTTP '+str(status))
            self.assertNotIn('private detail',json.dumps(result))

    def test_parseable_json_is_distinct_from_answer_schema(self):
        model={'model':'id','base_url':'https://example.invalid/v1','api_key_env':'TEST_KEY','request_options':{}}
        response={'choices':[{'message':{'content':'[]'},'finish_reason':'stop'}]}
        with patch.dict(os.environ,{'TEST_KEY':'secret'}),patch.object(client,'urlopen',return_value=io.BytesIO(json.dumps(response).encode())):
            result=client.call(model,self.samples[0],self.root,{'retries':0,'retry_wait_seconds':0,'timeout_seconds':2})
        self.assertTrue(result['parseable'])
        self.assertFalse(result['pure_json'])
        self.assertIsNone(result['prediction'])

    def test_offline_missing_duplicate_and_unknown_ids(self):
        sample=self.samples[0]
        row={'model':'x','model_id':'id','sample_id':sample['id'],'prediction':sample['label']}
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'predictions.jsonl'
            for rows in ([],[row,row],[{**row,'sample_id':'unknown'}]):
                p.write_text('\n'.join(json.dumps(x) for x in rows),'utf-8')
                with self.assertRaises(ValueError):evaluate.offline_records(p,[sample])

    def test_end_to_end_offline_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);p=folder/'predictions.jsonl'
            p.write_text('\n'.join(json.dumps({'model':'reference','model_id':'reference','sample_id':s['id'],'prediction':s['label']}) for s in self.samples),'utf-8')
            args=argparse.Namespace(command='score',config=PACKAGE/'configs/default.yaml',root=self.root,predictions=p,output=folder/'result')
            result=evaluate.execute(args)
            self.assertEqual(result['records'],1429)
            summaries=json.loads((folder/'result/summary.json').read_text('utf-8'))
            self.assertEqual(len(summaries),6)
            for row in summaries:
                expected = [expected_identity(s) for s in self.samples if (s['task'],s['difficulty']) == (row['task'],row['difficulty'])]
                self.assertAlmostEqual(row['mean_score'],sum(expected)/len(expected),places=12)
            tasks=json.loads((folder/'result/task_summary.json').read_text('utf-8'))
            self.assertEqual(len(tasks),2)
            self.assertTrue(all(x['complete_difficulties'] for x in tasks))
            meta=json.loads((folder/'result/meta.json').read_text('utf-8'))
            self.assertEqual(meta['status'],'complete');self.assertTrue(meta['dataset_sha256'])
            with self.assertRaises(ValueError):evaluate.execute(args)


if __name__=='__main__':
    unittest.main()
