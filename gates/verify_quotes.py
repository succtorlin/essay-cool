#!/usr/bin/env python3
"""
verify_quotes.py — trace every quotation in a generated artifact back to its source.

Catches the failure mode where an LLM writing a skill, card, summary or report
produces a quotation that *looks* sourced but is paraphrased, merged from two
places, or invented outright.

The hard part is not string matching — it is that real sources are OCR'd scans.
This gate normalises away the five corruptions that defeat naive `grep`:

  1. intra-word spaces .......... "ar e writing"  -> arewriting
  2. glyph confusion ............ scans render I as 1, O as 0
  3. punctuation / smart quotes . don't / don’t / "..." / “...”
  4. page furniture mid-sentence  "of this 139 <<<PAGE 154>>> Book Title essay is"
  5. author-side elisions ....... "A ... B" is split and each fragment traced

Exit codes: 0 all traced · 1 untraceable quotes found · 2 bad invocation.

Usage:
  verify_quotes.py --artifacts 'cards/*.md' --sources 'corpus/*.txt'
  verify_quotes.py --artifacts out.md --sources src.txt --min-words 6 --json report.json
"""
import argparse, glob, json, os, re, sys

PAGE_MARKER = re.compile(r'<<<\s*PAGE\s*\d+\s*>>>', re.I)

def build_normalizer(glyph_fix=True):
    def norm(x):
        x = x.lower().replace('’', "'").replace('‘', "'")
        x = x.replace('“', '"').replace('”', '"')
        if glyph_fix:
            # OCR of scanned print: capital I -> 1, capital O -> 0
            x = x.replace('1', 'i').replace('0', 'o')
        return re.sub(r'[^a-z]', '', x)
    return norm

def clean_source(raw, header_patterns):
    raw = PAGE_MARKER.sub('', raw)
    for pat in header_patterns:
        # strip a running header together with any page number hugging it;
        # ORDER MATTERS: the header text is the anchor for finding that number,
        # so they must be removed in one pass. Removing the header first leaves
        # an orphan digit that severs the sentence it landed in.
        raw = re.sub(r'[&\s]*\d{0,4}\s*' + pat + r'\s*\d{0,4}', '', raw, flags=re.I)
    raw = re.sub(r'\n\s*\d{1,4}\s*\n', '\n', raw)   # page numbers alone on a line
    return raw

def extract_quotes(text, min_chars, max_chars, latin_ratio):
    """Pull quoted spans that are genuinely Latin-script prose.

    Only the *interior* of a quotation is returned. This matters: artifacts
    routinely prefix a quote with their own citation markup ("**#14** — ...",
    "H:17 (post-hoc) — ..."). Those digits are artifact-side bookkeeping, and
    feeding them through the OCR glyph fix (1->i, 0->o) corrupts the probe and
    produces false "untraceable" reports. So: take what is between the quote
    marks, never the whole line.
    """
    out = []
    seen = set()

    def push(seg):
        seg = seg.strip()
        if not seg or len(seg) < min_chars:
            return
        latin = len(re.findall(r'[A-Za-z]', seg))
        if latin / max(len(seg), 1) < latin_ratio:
            return            # CJK-dominant span: not an English quotation
        key = seg[:80]
        if key not in seen:
            seen.add(key)
            out.append(seg)

    # straight-quoted spans anywhere in the file
    for m in re.finditer(r'"([^"\n]{%d,%d})"' % (min_chars, max_chars), text):
        push(m.group(1))
    # blockquote lines: if the line carries a quoted span, that span was already
    # captured above; otherwise treat the line itself as the quotation.
    for m in re.finditer(r'^>\s?(.+)$', text, re.M):
        line = m.group(1).strip()
        if '"' in line or '\u201c' in line:
            continue
        push(line)
    return out

def trace(fragment, src_norm, norm, probe_chars, min_probe):
    probe = norm(fragment)[:probe_chars]
    if len(probe) < min_probe:
        return None                      # too short to be evidence either way
    if probe in src_norm:
        return True
    # Fallback: page furniture can land anywhere. Accept when both halves of the
    # fragment appear, which tolerates exactly one interruption.
    full = norm(fragment)
    a, b = full[:len(full) // 2], full[len(full) // 2:]
    if len(a) >= 20 and len(b) >= 20 and a in src_norm and b in src_norm:
        return True
    return False

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--artifacts', required=True, nargs='+', help='glob(s) of generated files to check')
    p.add_argument('--sources', required=True, nargs='+', help='glob(s) of source text files')
    p.add_argument('--header', action='append', default=[],
                   help='regex for a running header to strip (repeatable)')
    p.add_argument('--no-glyph-fix', action='store_true', help='disable the I->1 / O->0 OCR normalisation')
    p.add_argument('--min-words', type=int, default=8, help='ignore quotes shorter than this (default 8)')
    p.add_argument('--probe-chars', type=int, default=45, help='normalised chars compared (default 45)')
    p.add_argument('--json', help='write a machine-readable report here')
    p.add_argument('-q', '--quiet', action='store_true')
    a = p.parse_args()

    src_files = [f for g in a.sources for f in glob.glob(g)]
    art_files = [f for g in a.artifacts for f in glob.glob(g)]
    if not src_files:
        print('error: no source files matched', file=sys.stderr); return 2
    if not art_files:
        print('error: no artifact files matched', file=sys.stderr); return 2

    norm = build_normalizer(glyph_fix=not a.no_glyph_fix)
    raw = ''.join(open(f, encoding='utf-8', errors='replace').read() for f in src_files)
    src_norm = norm(clean_source(raw, a.header))

    checked = 0
    misses = []
    for af in sorted(art_files):
        text = open(af, encoding='utf-8', errors='replace').read()
        for quote in extract_quotes(text, a.min_words * 4, 600, 0.6):
            for frag in re.split(r'\.\.\.|…|\[\.\.\.\]', quote):
                if len(re.findall(r"[A-Za-z][A-Za-z']*", frag)) < a.min_words:
                    continue
                verdict = trace(frag, src_norm, norm, a.probe_chars, a.min_words * 4)
                if verdict is None:
                    continue
                checked += 1
                if not verdict:
                    misses.append({'file': os.path.basename(af), 'fragment': frag.strip()[:120]})

    if not a.quiet:
        print('quote fragments checked: %d | untraceable: %d' % (checked, len(misses)))
        for m in misses:
            print('  UNTRACEABLE  %-28s %s' % (m['file'], m['fragment']))
        if checked == 0:
            print('  (no quotations met the --min-words threshold; nothing was verified)')
    if a.json:
        json.dump({'checked': checked, 'untraceable': misses}, open(a.json, 'w'), indent=1, ensure_ascii=False)
    return 1 if misses else 0

if __name__ == '__main__':
    sys.exit(main())
