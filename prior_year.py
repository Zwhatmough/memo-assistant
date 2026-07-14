"""Deterministic prior-year value extractor.

Scans verified fact excerpts for the "(YYYY: £Xm)" pattern that annual
reports use to show comparatives, and creates synthetic prior-year facts
from the matches. No API calls — pure regex over already-validated text.

Every prior-year fact inherits the citation from its parent (the excerpt
is already verified). The value is the raw number from the pattern; the
unit is inherited from the parent fact so no conversion is needed.

Usage:
    python prior_year.py                                  # uses default paths
    python prior_year.py --facts output/validated_facts.json
"""

import argparse
import json
import os
import re
from typing import Optional


# Matches patterns like:  (2025: £601.1m)  (2025: 70%)  (2025: 14,013)  (2025: £2,854)
PRIOR_YEAR_RE = re.compile(
    r'\((\d{4})[;:]\s*'        # group 1: year
    r'([£$]?)'                  # group 2: optional currency prefix
    r'([\d,]+(?:\.\d+)?)'       # group 3: numeric value (commas allowed, optional decimal)
    r'([m%p]?)'                 # group 4: optional suffix — m=millions, %=percent, p=pence
    r'\)',
    re.I,
)


def _parse_value(digits_str: str) -> float:
    """Parse a numeric string (stripping commas) to float."""
    return float(digits_str.replace(',', ''))


def _select_match(
    matches: list[tuple],
    parent_unit: str,
) -> Optional[tuple]:
    """Pick the best match from a list of (year, prefix, digits, suffix) tuples.

    When an excerpt contains multiple prior-year values (e.g. tax charge and
    effective tax rate in the same sentence), we select the one whose format
    aligns with the parent fact's unit.
    """
    unit = (parent_unit or '').lower()
    is_pct = '%' in unit or 'percent' in unit
    is_pence = 'pence' in unit or (unit == 'p')
    # Everything else is treated as monetary or count (selects first non-pct match)

    for year, prefix, digits, suffix in matches:
        has_currency = bool(prefix)         # £ or $
        has_pct = suffix == '%'
        has_pence = suffix.lower() == 'p'

        if is_pct and has_pct:
            return year, prefix, digits, suffix
        if is_pence and has_pence:
            return year, prefix, digits, suffix
        if not is_pct and not is_pence and not has_pct and not has_pence:
            return year, prefix, digits, suffix

    # Fallback: return first match
    return matches[0]


def _apply_sign(value: float, parent_value: float) -> float:
    """If the parent fact is negative, negate the extracted value.

    Annual reports always write losses as positive numbers with the word
    'loss' nearby. E.g. "operating losses of £2.0m (2025: £4.3m)" — the
    2025 value is also a loss (−4.3) even though the pattern gives +4.3.
    Inheriting the parent's sign handles this correctly.
    """
    if parent_value < 0 and value > 0:
        return -value
    return value


def extract_prior_year_facts(validated_facts: list[dict]) -> list[dict]:
    """Return synthetic prior-year facts parsed from verified excerpts.

    Only processes financial_figures (which have explicit value/unit).
    Non-financial categories (business_facts, etc.) are skipped — their
    values are qualitative and not needed for growth-rate calculations.

    Args:
        validated_facts: list of chunks from validated_facts.json

    Returns:
        List of synthetic fact dicts, one per successfully parsed prior-year
        value. Each fact has the same shape as a financial_figure fact, plus
        a 'derived_from' field documenting the parent and the matched text.
    """
    prior_facts = []
    seen: set[tuple] = set()  # (label_lower, period) to deduplicate across chunks

    for chunk in validated_facts:
        chunk_id = chunk.get('chunk_id', '')

        for fig in chunk.get('financial_figures', []):
            if fig.get('citation_status') not in ('verified', 'corrected'):
                continue

            excerpt = fig.get('source', {}).get('excerpt', '')
            if not excerpt:
                continue

            matches = PRIOR_YEAR_RE.findall(excerpt)
            if not matches:
                continue

            best = _select_match(matches, fig.get('unit', ''))
            if best is None:
                continue

            year, prefix, digits, suffix = best
            raw_value = _parse_value(digits)
            value = _apply_sign(raw_value, fig['value'])

            period = f'FY{year}'
            key = (fig['label'].lower(), period)
            if key in seen:
                continue
            seen.add(key)

            # Reconstruct the matched text for the audit trail
            matched_text = f'({year}: {prefix}{digits}{suffix})'

            prior_facts.append({
                'label': fig['label'],
                'value': value,
                'unit': fig.get('unit', ''),
                'period': period,
                'citation_status': 'derived_from_excerpt',
                'derived_from': {
                    'chunk_id': chunk_id,
                    'parent_label': fig['label'],
                    'parent_value': fig['value'],
                    'parent_period': fig.get('period', ''),
                    'excerpt': excerpt,
                    'matched_text': matched_text,
                },
            })

    return prior_facts


def main():
    parser = argparse.ArgumentParser(description='Extract prior-year values from excerpts')
    parser.add_argument('--facts', default='output/validated_facts.json')
    parser.add_argument('--out', default='output/prior_year_facts.json')
    args = parser.parse_args()

    with open(args.facts) as f:
        chunks = json.load(f)

    prior = extract_prior_year_facts(chunks)

    os.makedirs('output', exist_ok=True)
    with open(args.out, 'w') as f:
        json.dump(prior, f, indent=2)

    print(f'Extracted {len(prior)} prior-year facts')
    for p in prior:
        src = p['derived_from']
        print(f'  {p["label"]} | {p["value"]} {p["unit"]} | {p["period"]}')
        print(f'    From: {src["matched_text"]} in excerpt: "{src["excerpt"][:80]}"')


if __name__ == '__main__':
    main()
