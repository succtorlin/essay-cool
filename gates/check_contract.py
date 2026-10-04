#!/usr/bin/env python3
"""
check_contract.py — enforce a declarative contract over generated artifacts.

Static structural checking: required sections in order, length caps on quoted
material, mandatory clauses that must survive into every artifact, banned
phrasings, and conditional requirements.

IMPORTANT — read this before trusting a green result:
this gate cannot tell you whether an artifact is *executable*. In the run that
produced these tools, all three static gates passed on a skill that demanded a
26-item audit and did not contain the 26 items. Static conformance and
executability are different properties. Pair this with an execution test that
gives the executor the artifact and nothing else (see docs/METHODOLOGY.md).

Contract file (JSON):
{
  "required_sections": ["## R", "## I", "## E", "## B"],
  "ordered": true,
  "max_quote_words": 100,
  "required_in_section": {"## B": ["does not promise", "survivorship"]},
  "banned": ["experts agree", "studies show"],
  "banned_unless_negated": {
      "pattern": "officers generally believe",
      "negators": ["never write", "do not write", "avoid"]
  },
  "require_if_present": {"2017 ->": ["knowledge cutoff"]},
  "max_numeric_ref": {"pattern": "#\\\\s?(\\\\d{1,2})", "max": 26}
}

Exit codes: 0 clean · 1 violations · 2 bad invocation.

Usage:
  check_contract.py --artifacts 'cards/*.md' --contract contract.json
"""
import argparse, glob, json, os, re, sys

def latin_words(s):
    return len(re.findall(r"[A-Za-z][A-Za-z'’-]*", s))

def check(path, c):
    t = open(path, encoding='utf-8', errors='replace').read()
    errs = []

    # 1. required sections, optionally in order
    pos = []
    for h in c.get('required_sections', []):
        i = t.find(h)
        if i < 0:
            errs.append('missing required section: %s' % h)
        else:
            pos.append((h, i))
    if c.get('ordered') and len(pos) == len(c.get('required_sections', [])):
        if [p[1] for p in pos] != sorted(p[1] for p in pos):
            errs.append('required sections present but out of order')

    # 2. quote length cap — quote INTERIORS only, so the artifact's own citation
    #    markup is not counted against the author's quota
    cap = c.get('max_quote_words')
    if cap:
        for m in re.finditer(r'"([^"\n]{40,2000})"', t):
            seg = m.group(1)
            if len(re.findall(r'[A-Za-z]', seg)) / max(len(seg), 1) < 0.6:
                continue
            w = latin_words(seg)
            if w > cap:
                errs.append('quote of %d words exceeds cap %d: %s...' % (w, cap, seg[:50]))

    # 3. clauses that must appear inside a given section
    for sec, needles in (c.get('required_in_section') or {}).items():
        i = t.find(sec)
        if i < 0:
            continue
        nxt = [j for j in (t.find('\n## ', i + 1),) if j > 0]
        body = t[i:nxt[0]] if nxt else t[i:]
        for n in needles:
            if n.lower() not in body.lower():
                errs.append('section %s missing required clause: %r' % (sec, n))

    # 4. flat bans
    for b in c.get('banned', []):
        if b.lower() in t.lower():
            errs.append('banned phrase present: %r' % b)

    # 5. bans that a nearby negation legitimises (an artifact may *prohibit* a
    #    phrasing; that is correct behaviour, not a violation)
    bu = c.get('banned_unless_negated')
    if bu:
        for m in re.finditer(re.escape(bu['pattern']), t, re.I):
            ctx = t[max(0, m.start() - 80):m.start()]
            if not any(n.lower() in ctx.lower() for n in bu.get('negators', [])):
                errs.append('banned phrase %r used without negation' % bu['pattern'])

    # 6. conditional requirements
    for trigger, needles in (c.get('require_if_present') or {}).items():
        if trigger in t:
            for n in needles:
                if n.lower() not in t.lower():
                    errs.append('%r present but required companion %r missing' % (trigger, n))

    # 7. numeric reference ceiling (catches references to item #43 of a 26-item list)
    mn = c.get('max_numeric_ref')
    if mn:
        over = sorted({int(m.group(1)) for m in re.finditer(mn['pattern'], t)
                       if int(m.group(1)) > mn['max']})
        if over:
            errs.append('references above declared max %d: %s' % (mn['max'], over))
    return errs

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--artifacts', required=True, nargs='+')
    p.add_argument('--contract', required=True)
    p.add_argument('--json')
    a = p.parse_args()
    try:
        c = json.load(open(a.contract))
    except Exception as e:
        print('error: cannot read --contract: %s' % e, file=sys.stderr); return 2
    files = sorted(f for g in a.artifacts for f in glob.glob(g))
    if not files:
        print('error: no artifact files matched', file=sys.stderr); return 2
    total, report = 0, {}
    for f in files:
        e = check(f, c)
        report[f] = e
        total += len(e)
        print('%-34s %s' % (os.path.basename(f), 'OK' if not e else 'FAIL(%d)' % len(e)))
        for x in e:
            print('    x %s' % x[:160])
    print('\n%d files, %d violations' % (len(files), total))
    if a.json:
        json.dump(report, open(a.json, 'w'), indent=1, ensure_ascii=False)
    return 1 if total else 0

if __name__ == '__main__':
    sys.exit(main())
