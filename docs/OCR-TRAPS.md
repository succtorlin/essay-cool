# OCR traps in scanned sources

Every corruption here was observed in production text — 869 pages of scanned books. Examples are re-expressed against this repo's synthetic demo source so no third-party content is reproduced. If you verify quotations against OCR'd sources, you will meet all of them.

## 1. Intra-word spaces

```
source:  "As you ar e writing your essay , place your thumb over your name"
grep "are writing"  ->  0 hits
```

The OCR splits words at arbitrary points. **Fix:** strip all non-letters from both sides before comparing. Do not try to repair the words.

## 2. Glyph confusion — the one that will surprise you

Scanned print renders **capital I as `1`** and **O as `0`**:

```
source:  "1 used to give a talk on writing essays."
actual:  "I used to give a talk on writing essays."
```

An artifact that correctly transcribes this as "I" will *fail* a naive provenance check. **Fix:** map `1→i` and `0→o` on both sides.

**But:** this mangles legitimate digits. `#14` becomes `io`. Apply it only to the quoted text being compared, never to the artifact's own citation markup. This single mistake produced 121 false positives in my first run.

## 3. Page furniture landing mid-sentence

```
"The only shortcoming of this 139 <<<PAGE 154>>> BRIDGE INSPECTION HANDBOOK essay is that..."
```

A page number, a page marker, and a running header, inside one sentence, between "this" and "essay".

**Fix, and the order is the whole trick:** the running header is the *anchor* for locating the page number printed beside it. Remove them **in one pass**:

```python
re.sub(r'[&\s]*\d{0,4}\s*' + header_pattern + r'\s*\d{0,4}', '', raw)
```

Strip the header first and you orphan a digit in mid-sentence, severing exactly the quotes that span a page break.

**Backstop:** when a probe still fails, accept it if both halves of the fragment appear in the source. That tolerates one interruption anywhere, including shapes you did not anticipate.

## 4. Smart quotes and apostrophes

`don't` / `don’t` / `"x"` / `“x”`. Normalize all variants. Free to fix, silent if you don't.

## 5. Author-side elision

A faithful artifact writes `"A … B"`, eliding the middle. Neither half matches the whole probe.

**Fix:** split on `...`, `…`, `[...]` and trace each fragment independently.

This also produces a *good* signal: one card elided a phrase precisely because it contained source-copyrighted content. Splitting on the ellipsis showed both remaining halves traced cleanly — the elision was principled, not evasive.

## 6. Headers that vary

`BRIDGE INSPECTION HANDBOOK` / `BRIDGE MAINTENANCE HANDBOOK`. Use a pattern, not a literal: `--header 'BRIDGE [A-Z]+ HANDBOOK'`.

## Measure your corruption before trusting any count

```python
raw  = len(re.findall(r'admissions officer', text, re.I))          # 23
norm = len(re.findall(r'admissions\s*of\s*ficer', squeeze(text)))  # 100
```

**4.3×.** Any frequency claim built on the raw number is wrong. Run this check on your own corpus before you quantify anything in it.

## Detecting marker variants

Section markers get corrupted too. `ANALYSIS` appeared as `_ ANALYSIS.`, `ANALYSIS”.`, and `ANALYSIS ee eC eee ee aed`. An exact match found 30 of 44.

**Fix:** match on letters-only content of short lines:

```python
def is_marker(line, key):
    s = line.strip()
    if len(s) > 40: return False
    letters = re.sub(r'[^A-Za-z]', '', s).upper()
    return letters.startswith(key) and len(letters) <= len(key) + 12
```

Recovered 43 of 44; the 2 remaining were genuinely empty OCR artifacts, confirmed by an independent reader.
