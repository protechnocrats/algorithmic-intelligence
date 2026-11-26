#!/usr/bin/env python3
"""MCP server for the algorithmic-intelligence skill: exact helpers for the steps agents get wrong by hand.

It never runs project code. The agent runs builds, tests, and benchmarks in its own shell, where the
host's sandbox, permissions, and guard hooks apply; this server only computes and checks:

  benchmark_compare    medians, spread, a bootstrap interval for the speedup, and the A/A noise floor
  doubling_fit         growth exponents from a doubling experiment, labeled, with a prediction
  plant_difference     put a known difference into one source file (to show a test can catch it)
  restore_difference   put the file back byte for byte, and record whether the tests caught it
  planted_status       list differences still planted, so none is left behind
  declare_no_differential_test   record why an edit to existing code needs no differential test
  check_summary        the final-summary lines the skill requires

Transport: MCP over stdio (newline-delimited JSON-RPC 2.0). Standard library only; Python 3.9+.
Project root: the directory the host starts the server in, or $ALGORITHMIC_INTELLIGENCE_ROOT.
Usage: python3 server.py   (hosts start it; see the README section "Optional: MCP tools")
"""
import hashlib
import json
import math
import os
import random
import re
import statistics
import sys
import tempfile
import time

SERVER_NAME = 'algorithmic-intelligence'
SERVER_VERSION = '0.1.1'
# Newest first. A client asking for one of these gets it back; otherwise the newest is offered.
PROTOCOL_VERSIONS = ['2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05']
MAX_FILE_BYTES = 5_000_000
BOOTSTRAP_ROUNDS = 4000

INSTRUCTIONS = (
    'Helpers for the algorithmic-intelligence skill. This server never runs project code: run builds, tests, '
    'and benchmarks in your own shell, then pass the results here. Use benchmark_compare before claiming a '
    'speedup, doubling_fit for growth rates, plant_difference/restore_difference to show a test can fail, '
    'planted_status before finishing, and check_summary on the final summary.')


# ---------------------------------------------------------------------------------------------- statistics
def _median(xs):
    return statistics.median(xs)


def _iqr(xs):
    if len(xs) < 2:
        return 0.0
    q = statistics.quantiles(xs, n=4, method='inclusive')
    return q[2] - q[0]


def _ratio_interval(base, cand, rounds=BOOTSTRAP_ROUNDS, seed=20261113):
    """95% percentile bootstrap interval for median(cand) / median(base), resampling each group's runs."""
    rng = random.Random(seed)
    ratios = []
    for _ in range(rounds):
        b = _median([rng.choice(base) for _ in base])
        c = _median([rng.choice(cand) for _ in cand])
        if b > 0:
            ratios.append(c / b)
    ratios.sort()
    lo = ratios[int(0.025 * (len(ratios) - 1))]
    hi = ratios[int(0.975 * (len(ratios) - 1))]
    return lo, hi


def _times(name, value):
    if not isinstance(value, list) or not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value):
        raise ToolError(f'{name} must be a list of numbers (one time per run)')
    if len(value) < 2:
        raise ToolError(f'{name} needs at least 2 runs; 10 or more give a usable interval')
    if any(v <= 0 or math.isnan(v) or math.isinf(v) for v in value):
        raise ToolError(f'{name} must contain only positive, finite times')
    return [float(v) for v in value]


def benchmark_compare(args):
    base = _times('baseline_times', args.get('baseline_times'))
    cand = _times('candidate_times', args.get('candidate_times'))
    aa = args.get('aa_times')
    aa = _times('aa_times', aa) if aa is not None else None
    unit = str(args.get('unit') or 's')

    mb, mc = _median(base), _median(cand)
    ratio = mc / mb
    lo, hi = _ratio_interval(base, cand)
    out = {
        'unit': unit,
        'baseline': {'runs': len(base), 'median': mb, 'iqr': _iqr(base)},
        'candidate': {'runs': len(cand), 'median': mc, 'iqr': _iqr(cand)},
        'time_ratio': ratio,
        'time_ratio_95ci': [lo, hi],
        'speedup': mb / mc,
        'change_percent': (ratio - 1) * 100,
        'warnings': [],
    }
    noise = None
    if aa is not None:
        alo, ahi = _ratio_interval(base, aa, seed=20261114)
        noise = max(abs(1 - alo), abs(ahi - 1))
        out['aa'] = {'runs': len(aa), 'median': _median(aa), 'time_ratio': _median(aa) / mb,
                     'time_ratio_95ci': [alo, ahi], 'noise_floor_percent': noise * 100}
        if alo > 1 or ahi < 1:
            out['warnings'].append('The A/A run (identical code) differs from the baseline beyond chance: the setup is '
                                   'biased (order, warm-up, environment). Fix the harness before trusting any comparison.')
    else:
        out['warnings'].append('No A/A run given: the noise floor is unknown. Benchmark the baseline against an identical '
                               'copy in the same harness and pass those times as aa_times.')
    if min(len(base), len(cand)) < 10:
        out['warnings'].append('Fewer than 10 runs per version: the interval is wide and can be unreliable.')

    if hi < 1:
        verdict = 'faster'
    elif lo > 1:
        verdict = 'slower'
    else:
        verdict = 'no measurable difference'
    if verdict != 'no measurable difference' and noise is not None and abs(1 - ratio) <= noise:
        verdict = 'no measurable difference'
        out['warnings'].append('The change is no larger than the A/A noise floor.')
    out['verdict'] = verdict
    out['summary'] = (f'{verdict}: candidate median {mc:.4g} {unit} vs baseline {mb:.4g} {unit} '
                      f'(time ratio {ratio:.3f}, 95% interval {lo:.3f} to {hi:.3f}'
                      + (f'; A/A noise floor {noise * 100:.1f}%' if noise is not None else '') + '). '
                      'Label it measured only if these runs came from this session.')
    return out


# ---------------------------------------------------------------------------------------------- doubling
def _doubling_label(b):
    if b < 0.5:
        return 'below linear: fixed overhead dominates at this size, or the work is sublinear'
    if b < 0.85:
        return 'between constant and linear: overhead still dominates, or sublinear'
    if b < 1.15:
        return 'near 1: linear'
    if b < 1.4:
        return 'slightly above 1: fits n log n (or linear with a cache or memory boundary crossed)'
    if b < 1.75:
        return 'between n log n and quadratic: mixed costs, or a boundary crossed; measure more sizes'
    if b < 2.3:
        return 'near 2: quadratic'
    if b < 2.75:
        return 'between quadratic and cubic'
    if b < 3.3:
        return 'near 3: cubic'
    return 'above cubic: exponential growth or a resource exhausted'


def doubling_fit(args):
    pts = args.get('points')
    if not isinstance(pts, list) or len(pts) < 2:
        raise ToolError('points must be a list of at least 2 {"n": size, "time": seconds} objects')
    try:
        points = sorted((float(p['n']), float(p['time'])) for p in pts)
    except (TypeError, KeyError, ValueError):
        raise ToolError('each point needs a numeric "n" (input size) and "time" (measured time)')
    rows = []
    for (n1, t1), (n2, t2) in zip(points, points[1:]):
        if n1 <= 0 or n2 <= n1 or t1 <= 0 or t2 <= 0:
            raise ToolError(f'sizes must be positive and increasing and times positive: ({n1:g}, {t1:g}) -> ({n2:g}, {t2:g})')
        b = math.log(t2 / t1) / math.log(n2 / n1)
        rows.append({'from_n': n1, 'to_n': n2, 'exponent': b, 'label': _doubling_label(b)})
    n_last, t_last = points[-1]
    last_b = rows[-1]['exponent']
    out = {'pairs': rows, 'prediction': {'n': 2 * n_last, 'time': t_last * 2 ** last_b,
                                         'note': 'write this down before measuring the next size'},
           'warnings': []}
    if len(rows) >= 2 and abs(rows[-1]['exponent'] - rows[0]['exponent']) > 0.3:
        out['warnings'].append('The exponent changes across sizes: small sizes may include fixed overhead, or the working '
                               'set crossed a cache or memory boundary. Base the claim on the largest sizes.')
    return out


# ---------------------------------------------------------------------------------------------- summary
REQUIRED_SUMMARY = ['Complexity', 'Data structures', 'Contract changes', 'Bugs noticed', 'Hazards noticed', 'Commands not run']


def _label_pattern(label):
    words = r'\s+'.join(re.escape(w) for w in label.split())
    return re.compile(r'^\s*(?:(?:[-*+>]|\d+[.)])\s+)?(?:#{1,6}\s+)?(?:\*\*|__|`)?' + words +
                      r'(?:\*\*|__|`)?\s*(?::|$)', re.I | re.M)


def check_summary(args):
    text = args.get('text')
    if not isinstance(text, str):
        raise ToolError('text must be the final summary as a string')
    missing = [label for label in REQUIRED_SUMMARY if not _label_pattern(label).search(text)]
    return {'complete': not missing, 'missing': missing,
            'note': ('All required lines are present.' if not missing else
                     'Add each missing label as its own line ("Label: ..."), writing "none" when empty.')}


# ---------------------------------------------------------------------------------------------- planting
def project_root():
    return os.path.realpath(os.environ.get('ALGORITHMIC_INTELLIGENCE_ROOT') or os.getcwd())


def git_dir(root):
    """The repository's .git directory, found from the root or any directory above it, or None."""
    d = root
    while True:
        if os.path.isdir(os.path.join(d, '.git')):
            return os.path.join(d, '.git')
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def _state_dir(root, kind='plants'):
    git = git_dir(root)
    if git:  # inside .git: never shows up as a change, survives a server restart; the edit gate reads it here
        d = os.path.join(git, 'algorithmic-intelligence', kind)
    else:
        d = os.path.join(tempfile.gettempdir(), 'algorithmic-intelligence-' + kind,
                         hashlib.sha256(root.encode()).hexdigest()[:16])
    os.makedirs(d, exist_ok=True)
    return d


def _inside(root, path):
    """The real path of a project file, refusing anything outside the root, under .git, or a symlink leaving it."""
    if not isinstance(path, str) or not path:
        raise ToolError('file must be a path inside the project')
    full = os.path.realpath(os.path.join(root, path))
    if os.path.commonpath([root, full]) != root or full == root:
        raise ToolError(f'{path} is outside the project root {root}')
    rel = os.path.relpath(full, root)
    if rel.split(os.sep)[0] == '.git':
        raise ToolError('files under .git cannot be changed')
    if not os.path.isfile(full):
        raise ToolError(f'{path} is not a file in the project')
    if os.path.getsize(full) > MAX_FILE_BYTES:
        raise ToolError(f'{path} is larger than {MAX_FILE_BYTES} bytes')
    return full, rel


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _records(root, kind='plants'):
    d = _state_dir(root, kind)
    out = []
    for name in sorted(os.listdir(d)):
        if name.endswith('.json'):
            try:
                with open(os.path.join(d, name), encoding='utf-8') as f:
                    out.append(json.load(f))
            except (OSError, ValueError):
                continue
    return out


def _write_atomic(path, data):
    tmp = path + '.ai-tmp'
    mode = os.stat(path).st_mode
    with open(tmp, 'wb') as f:
        f.write(data)
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def plant_difference(args):
    root = project_root()
    full, rel = _inside(root, args.get('file'))
    find, replace = args.get('find'), args.get('replace')
    if not isinstance(find, str) or not find or not isinstance(replace, str) or find == replace:
        raise ToolError('find must be non-empty text and replace must differ from it')
    for r in _records(root):
        if r['status'] == 'planted' and r['file'] == rel:
            raise ToolError(f'{rel} already has a planted difference ({r["id"]}); restore it first')
    with open(full, 'rb') as f:
        original = f.read()
    fb = find.encode('utf-8')
    count = original.count(fb)
    if count != 1:
        raise ToolError(f'find must occur exactly once in {rel}; it occurs {count} times. Include more surrounding text.')
    planted = original.replace(fb, replace.encode('utf-8'), 1)
    covers = args.get('covers') or []
    if not isinstance(covers, list) or not all(isinstance(c, str) for c in covers):
        raise ToolError('covers must be a list of file paths')
    covered = [_inside(root, c) for c in covers]
    covers_sha = []
    for f, _ in covered:  # lets a later session's edit gate tell whether these files are still the version tested
        with open(f, 'rb') as fh:
            covers_sha.append(_sha(fh.read()))
    pid ='plant-' + time.strftime('%Y%m%d-%H%M%S') + '-' + _sha(original + planted)[:8]
    d = _state_dir(root)
    with open(os.path.join(d, pid + '.orig'), 'wb') as f:
        f.write(original)
    record = {'id': pid, 'file': rel, 'file_abs': full, 'status': 'planted', 'planted_at': time.time(),
              'covers': [r for _, r in covered], 'covers_abs': [f for f, _ in covered], 'covers_sha256': covers_sha,
              'original_sha256': _sha(original), 'planted_sha256': _sha(planted),
              'purpose': str(args.get('purpose') or '')[:500], 'tests_failed': None, 'evidence': None}
    with open(os.path.join(d, pid + '.json'), 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=1)
    _write_atomic(full, planted)
    return {'id': pid, 'file': rel, 'covers': record['covers'], 'status': 'planted',
            'next': 'Run the tests that should catch this difference now, in your own shell. Then call '
                    'restore_difference with this id and whether they failed. Do not edit this file meanwhile.'}


def restore_difference(args):
    root = project_root()
    pid = args.get('id')
    if not isinstance(pid, str) or not re.fullmatch(r'plant-[0-9-]+-[0-9a-f]{8}', pid):
        raise ToolError('id must be the id plant_difference returned')
    tests_failed = args.get('tests_failed')
    if not isinstance(tests_failed, bool):
        raise ToolError('tests_failed must be true or false: did the tests fail while the difference was planted?')
    d = _state_dir(root)
    rec_path = os.path.join(d, pid + '.json')
    try:
        with open(rec_path, encoding='utf-8') as f:
            record = json.load(f)
        with open(os.path.join(d, pid + '.orig'), 'rb') as f:
            original = f.read()
    except OSError:
        raise ToolError(f'no planted difference {pid} in this project')
    if record['status'] != 'planted':
        raise ToolError(f'{pid} was already restored')
    full, rel = _inside(root, record['file'])
    with open(full, 'rb') as f:
        current = f.read()
    if _sha(current) != record['planted_sha256'] and not args.get('force'):
        raise ToolError(f'{rel} changed since the difference was planted, so restoring would discard those edits. '
                        'Undo them, or pass force: true to restore the original bytes anyway.')
    _write_atomic(full, original)
    with open(full, 'rb') as f:
        if _sha(f.read()) != record['original_sha256']:
            raise ToolError(f'{rel} could not be restored exactly; restore it from version control')
    record.update({'status': 'restored', 'restored_at': time.time(), 'tests_failed': tests_failed,
                   'evidence': str(args.get('evidence') or '')[:2000]})
    with open(rec_path, 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=1)
    caught = ('The tests caught the planted difference, so they can fail on this kind of change.' if tests_failed else
              'The tests did NOT catch the planted difference: they cannot show this kind of change is safe. '
              'Strengthen them before relying on them.')
    return {'id': pid, 'file': rel, 'status': 'restored', 'restored_exactly': True, 'tests_failed': tests_failed,
            'conclusion': caught}


NO_TEST_REASONS = {
    'new-code': 'new code with no earlier behavior to preserve (write mode: a declared stub, wiring, a new function)',
    'approved-behavior-change': 'a behavior change the developer approved by name in this conversation',
    'no-runtime-effect': 'no effect when the code runs (comments, formatting, renaming a private local)',
    'developer-waived': 'the developer, in this conversation, told you to make this edit without a differential test',
}


def declare_no_differential_test(args):
    root = project_root()
    files = args.get('files')
    if not isinstance(files, list) or not files or not all(isinstance(f, str) for f in files):
        raise ToolError('files must be a non-empty list of paths inside the project')
    kind = args.get('kind')
    if kind not in NO_TEST_REASONS:
        raise ToolError('kind must be one of: ' + ', '.join(f'{k} ({v})' for k, v in NO_TEST_REASONS.items()))
    reason = args.get('reason')
    if not isinstance(reason, str) or len(reason.strip()) < 15:
        raise ToolError('reason must say in a sentence why this edit needs no differential test')
    resolved = [_inside(root, f) for f in files]
    did = 'decl-' + time.strftime('%Y%m%d-%H%M%S') + '-' + _sha('|'.join(f for f, _ in resolved).encode() + reason.encode())[:8]
    record = {'id': did, 'files': [r for _, r in resolved], 'files_abs': [f for f, _ in resolved], 'kind': kind,
              'reason': reason.strip()[:1000], 'declared_at': time.time()}
    with open(os.path.join(_state_dir(root, 'declarations'), did + '.json'), 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=1)
    return {'id': did, 'files': record['files'], 'kind': kind,
            'note': 'Recorded. List these files and the reason in the final summary so the developer can check them; '
                    'an edit that changes behavior still needs the developer\'s approval (rule 5).'}


def planted_status(args):
    root = project_root()
    records = _records(root)
    active = [{'id': r['id'], 'file': r['file'], 'purpose': r['purpose']} for r in records if r['status'] == 'planted']
    done = [{'id': r['id'], 'file': r['file'], 'covers': r.get('covers', []), 'tests_failed': r['tests_failed']}
            for r in records if r['status'] == 'restored']
    decls = [{'id': d['id'], 'files': d['files'], 'kind': d['kind'], 'reason': d['reason']} for d in _records(root, 'declarations')]
    return {'still_planted': active, 'restored': done, 'declared_no_differential_test': decls,
            'note': ('Nothing is left planted.' if not active else
                     'Differences are still planted: restore each with restore_difference before finishing.')}


# ---------------------------------------------------------------------------------------------- tool table
class ToolError(Exception):
    """A problem with the tool's arguments or the project state, reported to the agent as a tool error."""


def _obj(props, required=()):
    return {'type': 'object', 'properties': props, 'required': list(required), 'additionalProperties': False}


_NUMS = {'type': 'array', 'items': {'type': 'number'}}

TOOLS = {
    'benchmark_compare': {
        'fn': benchmark_compare,
        'description': ('Decide whether a measured speedup is real. Pass per-run times for the original (baseline) and '
                        'the changed code (candidate), measured alternately in the same harness, and ideally an A/A run '
                        '(the original against an identical copy). Returns medians, spread, a 95% bootstrap interval for '
                        'the time ratio, the noise floor, and a verdict: faster, slower, or no measurable difference. '
                        'Run the benchmarks yourself first; this tool runs nothing.'),
        'inputSchema': _obj({'baseline_times': _NUMS, 'candidate_times': _NUMS, 'aa_times': _NUMS,
                             'unit': {'type': 'string', 'description': 'unit of the times, e.g. "ms"'}},
                            ['baseline_times', 'candidate_times']),
        'annotations': {'readOnlyHint': True, 'openWorldHint': False},
    },
    'doubling_fit': {
        'fn': doubling_fit,
        'description': ('Growth rate from a doubling experiment: pass measured times at increasing input sizes. Returns '
                        'the exponent b = log(T2/T1)/log(N2/N1) for each pair, labeled (near 1 linear, about 1.1-1.3 '
                        'n log n, near 2 quadratic), and predicts the time at the next doubling so you can check it.'),
        'inputSchema': _obj({'points': {'type': 'array', 'items': _obj({'n': {'type': 'number'}, 'time': {'type': 'number'}},
                                                                       ['n', 'time'])}}, ['points']),
        'annotations': {'readOnlyHint': True, 'openWorldHint': False},
    },
    'plant_difference': {
        'fn': plant_difference,
        'description': ('Show that a test can fail: replace one exact snippet in one project source file with a '
                        'deliberately wrong version, recording the original bytes. Run the tests yourself, then call '
                        'restore_difference. Paths must be inside the project; one planted difference per file.'),
        'inputSchema': _obj({'file': {'type': 'string', 'description': 'path relative to the project root'},
                             'find': {'type': 'string', 'description': 'exact text that occurs once in the file'},
                             'replace': {'type': 'string', 'description': 'the wrong version to plant'},
                             'purpose': {'type': 'string', 'description': 'what the tests should notice'},
                             'covers': {'type': 'array', 'items': {'type': 'string'},
                                        'description': 'other files the same change touches (callers updated with it), '
                                                       'which the same tests cover'}},
                            ['file', 'find', 'replace']),
        'annotations': {'readOnlyHint': False, 'destructiveHint': False, 'idempotentHint': False, 'openWorldHint': False},
    },
    'restore_difference': {
        'fn': restore_difference,
        'description': ('Put back a file changed by plant_difference, byte for byte, and record whether the tests failed '
                        'while the difference was planted. Refuses if the file was edited since (pass force to override).'),
        'inputSchema': _obj({'id': {'type': 'string'}, 'tests_failed': {'type': 'boolean'},
                             'evidence': {'type': 'string', 'description': 'the failing test names or output line'},
                             'force': {'type': 'boolean'}}, ['id', 'tests_failed']),
        'annotations': {'readOnlyHint': False, 'destructiveHint': False, 'idempotentHint': False, 'openWorldHint': False},
    },
    'planted_status': {
        'fn': planted_status,
        'description': ('List differences still planted, those restored (and whether the tests caught them), and files '
                        'declared to need no differential test. Call before finishing.'),
        'inputSchema': _obj({}),
        'annotations': {'readOnlyHint': True, 'openWorldHint': False},
    },
    'declare_no_differential_test': {
        'fn': declare_no_differential_test,
        'description': ('Record why an edit to existing code needs no differential test: new-code (a declared stub or '
                        'wiring with no earlier behavior), approved-behavior-change (approved by name), or '
                        'no-runtime-effect, or developer-waived (the developer told you to proceed without one). The edit gate, when '
                        'installed, then lets edits to these files through. '
                        'List the declaration in the final summary. Do not use it to skip tests for an optimization.'),
        'inputSchema': _obj({'files': {'type': 'array', 'items': {'type': 'string'}},
                             'kind': {'type': 'string', 'enum': list(NO_TEST_REASONS)},
                             'reason': {'type': 'string'}}, ['files', 'kind', 'reason']),
        'annotations': {'readOnlyHint': False, 'destructiveHint': False, 'idempotentHint': False, 'openWorldHint': False},
    },
    'check_summary': {
        'fn': check_summary,
        'description': ('Check a final summary for the lines the algorithmic-intelligence skill requires: Complexity, '
                        'Data structures, Contract changes, Bugs noticed, Hazards noticed, Commands not run.'),
        'inputSchema': _obj({'text': {'type': 'string'}}, ['text']),
        'annotations': {'readOnlyHint': True, 'openWorldHint': False},
    },
}


# ---------------------------------------------------------------------------------------------- protocol
def _result(rid, result):
    return {'jsonrpc': '2.0', 'id': rid, 'result': result}


def _error(rid, code, message):
    return {'jsonrpc': '2.0', 'id': rid, 'error': {'code': code, 'message': message}}


def handle(msg):
    """One JSON-RPC message in, one response (or None for a notification) out."""
    if not isinstance(msg, dict) or msg.get('jsonrpc') != '2.0' or not isinstance(msg.get('method'), str):
        return _error(msg.get('id') if isinstance(msg, dict) else None, -32600, 'invalid request')
    rid, method, params = msg.get('id'), msg['method'], msg.get('params') or {}
    if 'id' not in msg:  # notification (notifications/initialized, cancelled, ...): no response
        return None
    if method == 'initialize':
        asked = params.get('protocolVersion') if isinstance(params, dict) else None
        version = asked if asked in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0]
        return _result(rid, {'protocolVersion': version, 'capabilities': {'tools': {'listChanged': False}},
                             'serverInfo': {'name': SERVER_NAME, 'version': SERVER_VERSION},
                             'instructions': INSTRUCTIONS})
    if method == 'ping':
        return _result(rid, {})
    if method == 'tools/list':
        return _result(rid, {'tools': [{'name': n, 'description': t['description'], 'inputSchema': t['inputSchema'],
                                        'annotations': t['annotations']} for n, t in TOOLS.items()]})
    if method == 'tools/call':
        name = params.get('name') if isinstance(params, dict) else None
        if name not in TOOLS:
            return _error(rid, -32602, f'unknown tool: {name}')
        args = params.get('arguments') or {}
        if not isinstance(args, dict):
            return _error(rid, -32602, 'arguments must be an object')
        try:
            out = TOOLS[name]['fn'](args)
        except ToolError as e:
            return _result(rid, {'content': [{'type': 'text', 'text': str(e)}], 'isError': True})
        except Exception as e:  # a bug here must not take the session down
            return _result(rid, {'content': [{'type': 'text', 'text': f'internal error in {name}: {e!r}'}], 'isError': True})
        return _result(rid, {'content': [{'type': 'text', 'text': json.dumps(out, indent=1)}],
                             'structuredContent': out, 'isError': False})
    return _error(rid, -32601, f'method not found: {method}')


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            reply = _error(None, -32700, 'parse error')
        else:
            reply = [r for r in map(handle, msg) if r] if isinstance(msg, list) else handle(msg)
        if reply:
            sys.stdout.write(json.dumps(reply) + '\n')
            sys.stdout.flush()


if __name__ == '__main__':
    main()
