#!/usr/bin/env python3
"""
verify_attribution.py — check that each quotation is credited to the RIGHT speaker.

The trap this exists for: in interview and Q&A material, a speaker's biography
is often printed at the END of their section, not the start. Any intuition that
"the text near this bio belongs to this person" shifts every quotation by one
speaker. The error is invisible to a quote-provenance check, because the quote
really is in the source — just attributed to the wrong human being.

You declare the speaker sections once (by line range), and this gate reports any
quotation whose nearby credited name disagrees with the section it actually
falls in.

Section config is TOML-free JSON:

  [
    {"file": "corpus/qa.txt", "speaker": "Okonkwo", "start": 1,   "end": 19},
    {"file": "corpus/qa.txt", "speaker": "Raman",   "start": 20, "end": 120}
  ]

How to find the boundaries honestly: locate every biography line, then confirm
with an independent signal — e.g. first-person institutional references
(see docs/METHODOLOGY.md) must fall inside that person's
section. If the two signals disagree, do not guess; read the chapter.

Exit codes: 0 all correct · 1 misattribution found · 2 bad invocation.

Usage:
  verify_attribution.py --artifacts 'cards/*.md' --sections sections.json \\
      --names Okonkwo Raman
"""
import argparse, glob, json, os, re, sys

def norm(x):
    x = x.lower().replace('’', "'")
    x = x.replace('1', 'i').replace('0', 'o')      # OCR glyph confusion
    return re.sub(r'[^a-z]', '', x)

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--artifacts', required=True, nargs='+')
    p.add_argument('--sections', required=True, help='JSON list of {file,speaker,start,end}')
    p.add_argument('--names', required=True, nargs='+', help='speaker surnames as written in artifacts')
    p.add_argument('--window', type=int, default=300,
                   help='chars before a quote searched for a credited name (default 300)')
    p.add_argument('--min-words', type=int, default=8)
    p.add_argument('--probe-chars', type=int, default=45)
    p.add_argument('--json', help='write a machine-readable report here')
    a = p.parse_args()

    try:
        secs = json.load(open(a.sections))
    except Exception as e:
        print('error: cannot read --sections: %s' % e, file=sys.stderr); return 2

    blobs = []
    for s in secs:
        try:
            lines = open(s['file'], encoding='utf-8', errors='replace').read().split('\n')
        except FileNotFoundError:
            print('error: section file not found: %s' % s['file'], file=sys.stderr); return 2
        end = s.get('end') or len(lines)
        blobs.append((s['speaker'], norm('\n'.join(lines[s['start'] - 1:end]))))

    art = [f for g in a.artifacts for f in glob.glob(g)]
    if not art:
        print('error: no artifact files matched', file=sys.stderr); return 2

    checked, bad = 0, []
    for af in sorted(art):
        txt = open(af, encoding='utf-8', errors='replace').read()
        for m in re.finditer(r'"([^"\n]{40,500})"', txt):
            seg = m.group(1)
            if len(re.findall(r'[A-Za-z]', seg)) / max(len(seg), 1) < 0.6:
                continue
            ctx = txt[max(0, m.start() - a.window):m.start()]
            named = [n for n in a.names if n in ctx]
            if len(named) != 1:
                continue                     # unattributed or ambiguous: not this gate's job
            claim = named[-1]
            for frag in re.split(r'\.\.\.|…', seg):
                probe = norm(frag)[:a.probe_chars]
                if len(probe) < a.min_words * 4:
                    continue
                hits = [who for who, blob in blobs if probe in blob]
                if not hits:
                    continue                 # not from a declared section
                checked += 1
                if claim not in hits:
                    bad.append({'file': os.path.basename(af), 'claimed': claim,
                                'actual': '/'.join(sorted(set(hits))),
                                'fragment': frag.strip()[:90]})

    print('attributed quotes checked: %d | MISATTRIBUTED: %d' % (checked, len(bad)))
    for b in bad:
        print('  WRONG SPEAKER  %-24s claims %-12s actual=%-12s %s'
              % (b['file'], b['claimed'], b['actual'], b['fragment']))
    if checked == 0:
        print('  (no attributed quotes matched a declared section; nothing was verified)')
    if a.json:
        json.dump({'checked': checked, 'misattributed': bad}, open(a.json, 'w'), indent=1, ensure_ascii=False)
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())
