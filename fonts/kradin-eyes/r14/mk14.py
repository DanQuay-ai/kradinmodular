import json, copy
O = json.load(open('/tmp/claude-0/override12.json'))
A = json.load(open('/tmp/claude-0/var/overrideA.json')); B = json.load(open('/tmp/claude-0/var/overrideB.json'))
for k in ('u', 'se', 'sɛ', 'sɔ', 'ne', 'nɛ'): O[k] = copy.deepcopy(B[k])
O['ku'] = copy.deepcopy(A['ku'])
O['nɛ'][1]['y'] = O['nɛ'][2]['y']                       # the bowl's bottom run on the bar's line (one horizontal)
for v in 'AB':
    Ov = copy.deepcopy(O); f = Ov['fɔ'][1]['segs']        # L300, A160 -180, A91 -180
    if v == 'A': f[1]['r'] = 145; f[2]['r'] = 80
    else: f[1]['r'] = 150; Ov['fɔ'][1]['y'] += 20; f[2]['ang'] = -140
    json.dump(Ov, open(f'/tmp/claude-0/r14/override{v}.json', 'w'), ensure_ascii=False)
json.dump({'pa': [{'op': 'cut', 'x': 430, 'y': 886}], 'si': [{'op': 'foot', 'stroke': 1, 'end': -1, 'f': 1.0}],
           're': [{'op': 'pull', 'stroke': 0, 'end': 0, 'd': 45, 'w': '140'}, {'op': 'pull', 'stroke': 3, 'end': -1, 'd': 45, 'w': '140'}]},
          open('/tmp/claude-0/r14/force.json', 'w'), ensure_ascii=False)
OA = json.load(open('/tmp/claude-0/var/ownerA.json'))
json.dump({k: OA[k] for k in ('tɔ', 'nɔ', 'no')}, open('/tmp/claude-0/r14/owner.json', 'w'), ensure_ascii=False)
print(O['nɛ'][1]['y'], O['nɛ'][2]['y'])
