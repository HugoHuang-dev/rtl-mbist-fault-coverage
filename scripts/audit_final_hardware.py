# -----------------------------------------------------------------------------
# Hugo's MBIST Project
# Author  : sunmingyin.huang@haw-hamburg.de
# Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
# File    : audit_final_hardware.py
# Module  : audit_final_hardware
# -----------------------------------------------------------------------------
"""Check native board captures against the frozen external transaction sequence."""
import csv
import copy
import hashlib
import io
import json
import xml.etree.ElementTree as ET
import zipfile
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / 'results/step08/hardware_final'
BUILD = ROOT / 'results/reruns/20260926_review_final/step08'
RELEASE = ROOT / 'releases/20260926_review'
SPEC = ROOT / 'specs/march_c_minus_64x8.csv'
CASES = [('08_normal_ila_round1.ila', False, False),
         ('10_normal_ila_round2.ila', False, True),
         ('11_normal_ila_after_reset.ila', False, False),
         ('15_fault_ila_round1.ila', True, False),
         ('16_fault_ila_round2.ila', True, True)]

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def num(row, key):
    return int(row[key], 16 if key in ('req_wdata[7:0]', 'rd_data[7:0]',
               'first_fail_expected[7:0]', 'first_fail_actual[7:0]') else 10)

def probe_check(raw, release):
    cores = json.loads(release.read_text())['ltx_root']['ltx_data'][0]['debug_cores']
    core = next(c for c in cores if c['name'] == 'u_ila')
    pins = {p['portIndex']: p for p in core['pins']}
    probes = ET.fromstring(raw).findall('.//probe')
    ports = []
    for probe in probes:
        options = {o.attrib['Id']: o.attrib['value'] for o in probe.findall('.//Option')}
        port = int(options['PROBE_PORT']); ports.append(port)
        require(options['CORE_UUID'] == core['uuid'], 'ILA core UUID differs from release')
        pin = pins[port]
        names = [n.attrib['name'] for n in probe.findall('./nets/net')]
        expected = [s['name'] for n in pin['nets'] for s in n.get('subnets', [n])]
        require(names == expected, f'Probe {port} mapping differs')
        require(int(options['PROBE_PORT_BIT_COUNT']) == len(names), 'Probe width differs')
        require(int(options['PROBE_PORT_BITS']) == 0, 'Probe offset differs')
    require(sorted(ports) == sorted(pins), 'Probe ports incomplete or duplicated')
    return core['uuid']

def audit_samples(rows, reference, fault, restart):
    require(len(rows) == 1024 and len(reference) == 640, 'Capture/reference length differs')
    require(num(rows[0], 'TRIGGER') == num(rows[0], 'start_pulse') == 1, 'Missing start trigger')
    require(num(rows[0], 'busy') == 0 and num(rows[0], 'req_valid') == 0, 'Start not idle')
    for field, value in [('done', int(restart)), ('pass', int(restart and not fault)),
                         ('fail', int(restart and fault)), ('error_count[8:0]', int(restart and fault)),
                         ('accepted_count[9:0]', 640 if restart else 0)]:
        require(num(rows[0], field) == value, f'Previous result differs: {field}')
    requests = [(i, r) for i, r in enumerate(rows) if num(r, 'req_valid')]
    require(len(requests) == 640, 'Request count differs')
    mismatches = []
    reads = writes = 0
    phases = {}
    for sequence, ((index, row), expected) in enumerate(zip(requests, reference)):
        phase = num(row, 'u_mbist/phase[2:0]')
        address = num(row, 'req_addr[5:0]')
        write = num(row, 'req_write')
        require(int(expected['seq']) == sequence, 'Reference order differs')
        require(f'M{phase}' == expected['phase'] and address == int(expected['address']),
                f'Address/phase differs at request {sequence}')
        require(('write' if write else 'read') == expected['operation'], 'Read/write order differs')
        phases[f'M{phase}'] = phases.get(f'M{phase}', 0) + 1
        if write:
            writes += 1
            require(num(row, 'req_wdata[7:0]') == int(expected['write_data'], 16), 'Write data differs')
        else:
            response = rows[index + 1]
            require(num(response, 'rd_valid') == 1, 'Missing one-cycle response')
            want = int(expected['expected_read'], 16)
            actual = num(response, 'rd_data[7:0]')
            injected = fault and reads == 71
            require(actual == (want ^ 1 if injected else want), f'Read data differs at read {reads}')
            if actual != want:
                mismatches.append(dict(response_sample=index+1, phase=phase, address=address,
                                       expected=want, actual=actual, read_ordinal=reads))
            reads += 1
    require(reads == writes == 320, 'Read/write totals differ')
    require(len(mismatches) == int(fault), 'Unexpected mismatch total')
    if fault:
        require(mismatches[0]['phase'] == 2 and mismatches[0]['address'] == 7, 'Fault location differs')
    last_response = requests[-1][0] + 1
    done_sample = last_response + 1
    for i, row in enumerate(rows):
        require(num(row, 'Sample in Buffer') == i, 'Noncontiguous buffer')
        if not i:
            continue
        prior = rows[i-1]
        require(num(row, 'start_pulse') == 0, 'Additional start inside capture')
        count = 0 if i == 1 else num(prior, 'accepted_count[9:0]') + num(prior, 'req_valid')
        require(num(row, 'accepted_count[9:0]') == count, f'Counter mismatch at sample {i}')
        require(num(row, 'rd_valid') == int(num(prior, 'req_valid') and not num(prior, 'req_write')),
                f'Read latency differs at sample {i}')
        seen = [m for m in mismatches if m['response_sample'] < i]
        require(num(row, 'error_count[8:0]') == len(seen), f'Error count differs at sample {i}')
        require(num(row, 'fail') == int(bool(seen)), f'FAIL timing differs at sample {i}')
        require(num(row, 'done') == int(i >= done_sample), f'DONE timing differs at sample {i}')
        require(num(row, 'pass') == int(i >= done_sample and not fault), f'PASS differs at sample {i}')
        require(num(row, 'busy') == int(i < done_sample), f'BUSY differs at sample {i}')
        for field, key in [('first_fail_phase[2:0]', 'phase'), ('first_fail_addr[5:0]', 'address'),
                           ('first_fail_expected[7:0]', 'expected'), ('first_fail_actual[7:0]', 'actual')]:
            require(num(row, field) == (seen[0][key] if seen else 0), f'Diagnostic differs: {field}, sample {i}')
    require(num(rows[-1], 'accepted_count[9:0]') == 640 and done_sample == 961, 'Completion differs')
    return dict(status='pass', mode='fault' if fault else 'normal', restart_from_done=restart,
                samples=len(rows), requests=len(requests), reads=reads, writes=writes,
                requests_by_phase=phases, last_request_sample=requests[-1][0],
                last_response_sample=last_response, done_sample=done_sample,
                final_pass=num(rows[-1], 'pass'), final_fail=num(rows[-1], 'fail'),
                final_error_count=num(rows[-1], 'error_count[8:0]'), mismatches=mismatches)

def audit(write=True):
    files = json.loads((HARDWARE / 'file_manifest.json').read_text(encoding='utf-8'))
    require(len(files) == 17 and len({f['file'] for f in files}) == 17, 'Evidence inventory differs')
    for f in files:
        require(sha(HARDWARE / f['file']) == f['sha256'], f"Evidence hash differs: {f['file']}")
    release_hashes = {}
    for mode, variant in [('normal_led', 'base'), ('normal_ila', 'ila'),
                          ('fault_led', 'base_fault'), ('fault_ila', 'ila_fault')]:
        debug = mode.endswith('ila')
        for suffix in (['bit', 'ltx'] if debug else ['bit']):
            name = f'{mode}.{suffix}'
            original = BUILD / variant / f"{'board_with_ila' if debug else 'board_top'}.{suffix}"
            require(sha(RELEASE / name) == sha(original), f'Release differs from implemented build: {name}')
            release_hashes[name] = sha(original)
    for line in (RELEASE / 'SHA256.txt').read_text().splitlines():
        digest, name = line.split(None, 1)
        require(release_hashes.get(name.strip()) == digest.lower(), 'Release manifest differs')
    reference = list(csv.DictReader(io.StringIO(SPEC.read_text(encoding='utf-8'))))
    results = []
    for filename, fault, restart in CASES:
        path = HARDWARE / 'captures' / filename
        with zipfile.ZipFile(path) as archive:
            require(archive.testzip() is None, 'Corrupt ILA archive')
            raw = archive.read('waveform.csv')
            uuid = probe_check(archive.read('probes.ltx'), RELEASE / ('fault_ila.ltx' if fault else 'normal_ila.ltx'))
            rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
            result = audit_samples(rows, reference, fault, restart)
            result.update(capture=filename, sha256=sha(path), core_uuid=uuid)
            results.append(result)
            if write:
                exports = HARDWARE / 'exports' / path.stem
                exports.mkdir(parents=True, exist_ok=True)
                for member in ('waveform.csv', 'waveform.vcd'):
                    (exports / member).write_bytes(archive.read(member))
    report = dict(status='pass', capture_count=5, normal_pass_runs=3, controlled_fail_runs=2,
                  request_count_per_run=640, reference_sha256=sha(SPEC),
                  release_sha256=release_hashes, captures=results)
    if write:
        (HARDWARE / 'audit.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        fields = ['capture','mode','restart_from_done','requests','reads','writes','done_sample',
                  'final_pass','final_fail','final_error_count','status']
        with (HARDWARE / 'capture_summary.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fields, extrasaction='ignore')
            writer.writeheader(); writer.writerows(results)
    return report

def self_check():
    reference = list(csv.DictReader(io.StringIO(SPEC.read_text(encoding='utf-8'))))
    with zipfile.ZipFile(HARDWARE / 'captures/16_fault_ila_round2.ila') as archive:
        rows = list(csv.DictReader(io.StringIO(archive.read('waveform.csv').decode('utf-8-sig'))))
    changes = [('counter', 1023, 'accepted_count[9:0]', '639'),
               ('diagnostic', 280, 'first_fail_addr[5:0]', '8'),
               ('read_latency', 279, 'rd_valid', '0'),
               ('early_done', 950, 'done', '1'),
               ('restart_clear', 1, 'fail', '1'),
               ('request_order', 1, 'req_addr[5:0]', '1')]
    results = []
    for name, index, field, value in changes:
        altered = copy.deepcopy(rows)
        altered[index][field] = value
        try:
            audit_samples(altered, reference, True, True)
        except ValueError as error:
            results.append(dict(case=name, result='rejected', reason=str(error)))
        else:
            raise ValueError(f'Invalid data accepted: {name}')
    (HARDWARE / 'audit_self_check.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true', help='Check six invalid in-memory copies')
    args = parser.parse_args()
    result = audit()
    if args.self_test:
        self_check()
    print('FINAL_HARDWARE_AUDIT_PASS captures=5 normal=3 controlled_fail=2 requests_per_run=640')
