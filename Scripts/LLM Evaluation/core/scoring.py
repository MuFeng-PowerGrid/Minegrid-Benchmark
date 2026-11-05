import json
import math
import re
from collections import Counter, defaultdict

VERSION = 'minegrid-paper-v1'
EPSILON = 1e-8
EDIT_VERSION = 'minegrid-edit-minimal-v1'
CONTROL_LISTS = ('control_units', 'inputs', 'states', 'outputs',
                 'differential_equations', 'algebraic_equations')
BUS_FIELDS = ('Bus', 'Type', 'Base (kV)', 'B (pu)', 'G (pu)', 'V', 'Theta',
              'PG', 'QG', 'PL', 'QL', 'Qmin', 'Qmax', 'Pmin', 'Pmax',
              'Vmin', 'Vmax', 'Area No.', 'ACorDCorIC', 'Apparatus', 'Number')
EDGE_FIELDS = ('FromBus', 'ToBus', 'R (pu)', 'X (pu)', 'Turn')
INTEGER_FIELDS = {'Bus', 'Type', 'Area No.', 'Apparatus', 'Number', 'FromBus', 'ToBus'}


def parse_json(text):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError('Duplicate JSON key: ' + key)
            obj[key] = value
        return obj
    def constant(value):
        raise ValueError('Non-finite JSON number: ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def _edit_fields(obj):
    if not isinstance(obj, dict):
        raise ValueError('Edit model must be a JSON object')
    leaves, shape = {}, {}
    def visit(value, path):
        if isinstance(value, dict):
            if not all(isinstance(k, str) for k in value):
                raise ValueError('JSON keys must be strings')
            shape[path] = ('object', tuple(sorted(value)))
            for key, child in value.items():
                visit(child, path + '/' + key.replace('~', '~0').replace('/', '~1'))
        elif isinstance(value, list):
            shape[path] = ('array', len(value))
            for i, child in enumerate(value):
                visit(child, path + '/' + str(i))
        elif value is None or type(value) in (str, bool):
            shape[path] = type(value).__name__
        elif _finite(value):
            shape[path] = 'number'
        else:
            raise ValueError('Edit model contains a non-JSON or non-finite value')
        if not isinstance(value, (dict, list)) or not value:
            leaves[path] = value
    visit(obj, '')
    return leaves, shape


def _edit_equal(a, b):
    return (_finite(a) and _finite(b) or type(a) is type(b)) and a == b


def validate_edit_case(baseline, reference, target_paths):
    before, shape = _edit_fields(baseline)
    after, expected_shape = _edit_fields(reference)
    if shape != expected_shape:
        raise ValueError('Edit reference must preserve baseline structure and value types')
    if (not isinstance(target_paths, list) or not target_paths
            or not all(isinstance(p, str) for p in target_paths)
            or len(set(target_paths)) != len(target_paths)):
        raise ValueError('target_paths must be a nonempty list of unique JSON Pointer leaf paths')
    changed = {p for p in before if not _edit_equal(before[p], after[p])}
    if set(target_paths) != changed:
        raise ValueError('target_paths must exactly identify the changed reference leaves')
    return before, after, shape


def score_edit(prediction, baseline, reference, target_paths):
    before, after, expected_shape = validate_edit_case(baseline, reference, target_paths)
    error = None
    try:
        predicted, shape = _edit_fields(prediction)
        valid = shape == expected_shape
        if not valid:
            error = 'Prediction structure or value types differ from baseline'
    except ValueError as exc:
        predicted, valid, error = {}, False, str(exc)
    targets = set(target_paths)
    preserved = before.keys() - targets
    hit = lambda p, values: p in predicted and _edit_equal(predicted[p], values[p])
    accuracy = sum(hit(p, after) for p in targets) / (len(targets) + EPSILON)
    preservation = sum(hit(p, before) for p in preserved) / (len(preserved) + EPSILON)
    return {'metric_version': EDIT_VERSION, 'validity_scope': 'structure_only',
            'schema_valid': valid, 'validation_error': error, 'val_score': float(valid),
            'target_accuracy': accuracy, 'preserve_score': preservation,
            'score': .45 * accuracy + .35 * preservation + .20 * valid}


def validate(obj, task):
    if not isinstance(obj, dict):
        raise ValueError('Answer must be a JSON object')
    if task == 'device_control':
        if set(obj) != set(CONTROL_LISTS) | {'task', 'difficulty', 'notes'}:
            raise ValueError('Control answer fields differ')
        if obj['task'] != 'derive_control_dae' or obj['difficulty'] not in ('easy', 'medium', 'hard'):
            raise ValueError('Invalid control task/difficulty')
        if not isinstance(obj['notes'], str):
            raise ValueError('notes must be a string')
        for key in CONTROL_LISTS:
            if not isinstance(obj[key], list) or not all(isinstance(x, str) and x.strip() for x in obj[key]):
                raise ValueError(key + ' must be a list of nonempty strings (empty list allowed)')
        return
    if task != 'network_topology':
        raise ValueError('Unknown task: ' + str(task))
    if set(obj) != {'Bus', 'Network'} or not isinstance(obj['Bus'], list) or not obj['Bus'] or not isinstance(obj['Network'], list):
        raise ValueError('Expected nonempty Bus array and Network array')
    for key, fields in [('Bus', BUS_FIELDS), ('Network', EDGE_FIELDS)]:
        for row in obj[key]:
            if not isinstance(row, dict) or set(row) != set(fields):
                raise ValueError(key + ' row fields differ')
            for field, value in row.items():
                if field == 'ACorDCorIC':
                    if value not in ('AC', 'DC', 'IC'):
                        raise ValueError('Invalid ACorDCorIC')
                elif type(value) not in (int, float) or not math.isfinite(value):
                    raise ValueError('Invalid numeric field: ' + field)
                elif field in INTEGER_FIELDS and value != int(value):
                    raise ValueError('Non-integral identifier/category: ' + field)
    ids = [b['Bus'] for b in obj['Bus']]
    if len(set(ids)) != len(ids) or any(b['Type'] not in (1, 2, 3) for b in obj['Bus']):
        raise ValueError('Duplicate bus ID or invalid bus type')
    for edge in obj['Network']:
        if edge['FromBus'] not in ids or edge['ToBus'] not in ids or edge['FromBus'] == edge['ToBus']:
            raise ValueError('Invalid branch endpoints')


def f1(a, b):
    a, b = Counter(a), Counter(b)
    matched = sum((a & b).values())
    precision = matched / (sum(a.values()) + EPSILON)
    recall = matched / (sum(b.values()) + EPSILON)
    return 2 * precision * recall / (precision + recall + EPSILON)


def assignment_value(values):
    if not values or not values[0]:
        return 0.0
    n = max(len(values), len(values[0]))
    costs = [[1 - (values[i][j] if i < len(values) and j < len(values[0]) else 0)
              for j in range(n)] for i in range(n)]
    u, v, p, way = [0.] * (n+1), [0.] * (n+1), [0] * (n+1), [0] * (n+1)
    for i in range(1, n+1):
        p[0] = i
        j0, minimum, used = 0, [float('inf')] * (n+1), [False] * (n+1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], float('inf'), 0
            for j in range(1, n+1):
                if not used[j]:
                    cur = costs[i0-1][j-1] - u[i0] - v[j]
                    if cur < minimum[j]:
                        minimum[j], way[j] = cur, j0
                    if minimum[j] < delta:
                        delta, j1 = minimum[j], j
            for j in range(n+1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    return sum(1 - costs[p[j]-1][j-1] for j in range(1, n+1))


def _finite(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def _identifier(value):
    return int(value) if _finite(value) and value == int(value) else None


def _rows(obj, key):
    value = obj.get(key)
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _buses(obj):
    rows = _rows(obj, 'Bus')
    counts = Counter(_identifier(row.get('Bus')) for row in rows)
    return {int(row['Bus']): row for row in rows
            if _identifier(row.get('Bus')) is not None and counts[_identifier(row['Bus'])] == 1}


def _mapping(bus_mapping, predicted, reference):
    if bus_mapping is None:
        return {key: key for key in predicted}
    if not isinstance(bus_mapping, dict):
        raise ValueError('bus_mapping must map predicted bus IDs to reference bus IDs')
    result = {}
    for source, target in bus_mapping.items():
        if isinstance(source, str):
            if not re.fullmatch(r'-?\d+', source):
                raise ValueError('Invalid source bus ID in bus_mapping')
            source = int(source)
        source, target = _identifier(source), _identifier(target)
        if source is None or target is None or source in result:
            raise ValueError('Invalid or repeated bus_mapping ID')
        result[source] = target
    if set(result) != set(predicted) or len(set(result.values())) != len(result) or not set(result.values()) <= set(reference):
        raise ValueError('bus_mapping must be a complete one-to-one correspondence to reference buses')
    return result


def _branches(obj, buses, mapping):
    result = defaultdict(list)
    for row in _rows(obj, 'Network'):
        source, target = _identifier(row.get('FromBus')), _identifier(row.get('ToBus'))
        if source not in buses or target not in buses or source == target:
            continue
        result[tuple(sorted((mapping[source], mapping[target])))].append(row)
    return result


def _branch_similarity(predicted, reference):
    error = 0.0
    for key, scale in [('R (pu)', .2), ('X (pu)', 1.), ('Turn', .2)]:
        a, b = predicted.get(key), reference.get(key)
        error += min(abs(a - b) / scale, 1.) if _finite(a) and _finite(b) else 1.
    return 1 - error / 3


def score(prediction, gold, task, bus_mapping=None):
    validate(gold, task)
    result = {'metric_version': VERSION, 'schema_valid': False, 'score': 0.0}
    try:
        validate(prediction, task)
        if task == 'device_control' and prediction['difficulty'] != gold['difficulty']:
            raise ValueError('Control difficulty differs from reference')
        result['schema_valid'] = True
    except (ValueError, TypeError, OverflowError) as exc:
        result['validation_error'] = str(exc)
    result['json_valid'] = float(result['schema_valid'])
    pred = prediction if isinstance(prediction, dict) else {}
    if task == 'device_control':
        def items(obj, key):
            value = obj.get(key)
            return [x for x in value if isinstance(x, str)] if isinstance(value, list) else []
        def equations(obj):
            return {re.sub(r'\s+', '', x).lower() for key in CONTROL_LISTS[4:] for x in items(obj, key)}
        def symbols(obj):
            text = ' '.join(x for key in CONTROL_LISTS[1:] for x in items(obj, key))
            return {x.lower() for x in re.findall(r'[A-Za-z_][A-Za-z0-9_]*', text)}
        coverage = sum(isinstance(pred.get(k), list) and bool(pred[k]) for k in CONTROL_LISTS) / len(CONTROL_LISTS)
        result.update(field_coverage=coverage, symbol_f1=f1(symbols(pred), symbols(gold)),
                      equation_match=f1(equations(pred), equations(gold)))
        result['score'] = .2 * result['json_valid'] + .2 * coverage + .3 * result['symbol_f1'] + .3 * result['equation_match']
    else:
        pb, gb = _buses(pred), _buses(gold)
        mapping = _mapping(bus_mapping, pb, gb)
        mapped = {mapping[key]: row for key, row in pb.items()}
        common = mapped.keys() & gb.keys()
        type_hits = sum(_identifier(mapped[key].get('Type')) == _identifier(gb[key].get('Type')) for key in common)
        pe, ge = _branches(pred, pb, mapping), _branches(gold, gb, {key:key for key in gb})
        matched, error = 0, 0.0
        for key in pe.keys() & ge.keys():
            count = min(len(pe[key]), len(ge[key]))
            similarities = [[_branch_similarity(a, b) for b in ge[key]] for a in pe[key]]
            error += 3 * max(0.0, count - assignment_value(similarities))
            matched += count
        edges = lambda groups: [key for key, rows in groups.items() for _ in rows]
        result.update(bus_f1=f1(mapped.keys(), gb.keys()), edge_f1=f1(edges(pe), edges(ge)),
                      param_score=1 - error / (3 * matched + EPSILON),
                      type_accuracy=type_hits / (len(common) + EPSILON), matched_branches=matched)
        result['score'] = (.15 * result['json_valid'] + .25 * result['bus_f1'] + .35 * result['edge_f1']
                           + .15 * result['param_score'] + .10 * result['type_accuracy'])
    result['score'] = min(1.0, max(0.0, result['score']))
    return result


