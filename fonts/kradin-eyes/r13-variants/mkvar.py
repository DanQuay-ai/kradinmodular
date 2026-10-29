"""variant A/B skeleton edits on top of the r12 skeleton (override12.json)"""
import json, copy, sys
O0 = json.load(open('/tmp/claude-0/override12.json'))
def mirror(st, c):
    s = copy.deepcopy(st); s['x'] = round(2 * c - st['x'], 2); s['h'] = (180 - st['h']) % 360
    for g in s['segs']:
        if g['t'] in ('A', 'C'): g['ang'] = -g['ang']
    return s
def var(v):
    O = copy.deepcopy(O0)
    # u: the two crossing strokes mirror each other (A: the tight curve, B: the round curve)
    u = O['u']; c = (u[0]['x'] + u[1]['x']) / 2
    O['u'] = [u[0], mirror(u[0], c)] if v == 'A' else [mirror(u[1], c), u[1]]
    # ku: rings and bar centred on the U
    ku = O['ku']; Ux = ku[0]['x']; Uc = Ux + ku[0]['segs'][1]['r'] + ku[0]['segs'][2]['len'] / 2
    for i in (1, 2): ku[i]['x'] = round(Uc + 75, 2)
    ku[3]['x'] = round(Uc - ku[3]['segs'][0]['len'] / 2, 2)
    # fɔ: the curl (A: shorter, B: tighter)
    f = O['fɔ'][1]['segs'][-1]
    if v == 'A': f['ang'] = -110
    else: f['r'] = 70
    # se, sɛ: hooks more vertical
    d = 16 if v == 'A' else 26
    for st in O['se']: st['h'] = (st['h'] + d) % 360
    for st in O['sɛ']: st['h'] = (st['h'] - d) % 360
    # sɔ: shorter arches
    cutw = 48 if v == 'A' else 78
    a, b = O['sɔ'][0], O['sɔ'][1]
    a['x'] += cutw; b['x'] -= cutw
    for st in (a, b): st['segs'][0]['len'] -= cutw; st['segs'][-1]['len'] -= cutw
    # ne, nɛ: the hook's top run on the top axis (651), like the bars
    for k in ('ne', 'nɛ'):
        st = O[k][0]; top = st['y'] + st['segs'][0]['len'] + st['segs'][1]['r']; dy = 651 - top
        st['y'] += dy; st['segs'][4]['len'] += dy
        if v == 'B': st['segs'][0]['len'] += 35; st['y'] -= 35       # longer tick
    # e (B only): mirrored copies of both strokes, drawn as strokes
    if v == 'B':
        def vflip(st):
            s = copy.deepcopy(st); s['y'] = 700 - st['y']; s['h'] = (-st['h']) % 360
            for g in s['segs']:
                if g['t'] in ('A', 'C'): g['ang'] = -g['ang']
            return s
        O['e'] = O['e'] + [vflip(s) for s in O['e']]
    json.dump(O, open(f'/tmp/claude-0/var/override{v}.json', 'w'), ensure_ascii=False)
for v in 'AB': var(v)
