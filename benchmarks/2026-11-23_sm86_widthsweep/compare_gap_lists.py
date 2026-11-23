import re, sys
theirs=[]
for line in open('/home/dejan/Downloads/scout_rtx5070_bitwidth_benchmark/scout_report_start_1000000000000000000000000.txt'):
    m=re.match(r'^(\d+)\s+([\d.]+)\s+(\d+)\s*$', line.strip())
    if m: theirs.append((int(m.group(1)), int(m.group(3)), float(m.group(2))))
# prvi redak je "Largest gap" pa ga preskacemo ako se ponavlja
seen=set(); th=[]
for g,lo,me in theirs:
    if (g,lo) in seen: continue
    seen.add((g,lo)); th.append((g,lo,me))
ours=[]
pat=re.compile(r'merit=([\d.]+) gap=(\d+) lower=(\d+) upper=(\d+)')
for line in open('/tmp/p0/our1e24.log'):
    m=pat.search(line)
    if m: ours.append((int(m.group(2)), int(m.group(3)), float(m.group(1))))
print(f'theirs (sm120 5070): {len(th)} gaps')
print(f'ours   (sm86  3070): {len(ours)} gaps')
tset={(g,lo) for g,lo,_ in th}; oset={(g,lo) for g,lo,_ in ours}
print(f'identical (gap, lower) pairs: {len(tset & oset)}')
print(f'missing from ours: {len(tset-oset)}   extra in ours: {len(oset-tset)}')
for x in sorted(tset-oset)[:5]: print('  MISSING', x)
for x in sorted(oset-tset)[:5]: print('  EXTRA  ', x)
# merit sukladnost
dm=[abs(a[2]-b[2]) for a,b in zip(sorted(th), sorted(ours))] if len(th)==len(ours) else []
if dm: print(f'max |merit difference| on sorted lists: {max(dm):.6f}')
