#!/usr/bin/env python3
"""Evaluate manually recorded answers across same benchmark questions.

Input JSON: [{id, baseline: {score:0..2, evidence:[...]},
               semantic: {score:0..2, evidence:[...]}}].
No claims about live Copilot or fabricated scoring.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


def compare(records):
    if len(records) != 10 or len({r['id'] for r in records}) != 10:
        raise ValueError('Expected 10 unique questions')
    scores = {}
    for mode in ('baseline','semantic'):
        values=[]
        for r in records:
            raw = r[mode]['score']
            if type(raw) is not int or raw not in (0,1,2):
                raise ValueError('Scores must be 0, 1 or 2')
            if not isinstance(r[mode]['evidence'], list):
                raise ValueError('Evidence must be a list')
            values.append(raw)
        scores[mode]=values
    return {'baseline_total':sum(scores['baseline']), 'semantic_total':sum(scores['semantic']),
            'baseline_mean':sum(scores['baseline'])/10,
            'semantic_mean':sum(scores['semantic'])/10,
            'delta':sum(scores['semantic'])-sum(scores['baseline'])}


def main():
    if len(sys.argv)!=2:
        raise SystemExit('Usage: python scripts/pr7_compare.py docs/pr7/results_actual.json')
    records=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    result=compare(records)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print('Scores require real user-verified Copilot responses; scripts do not generate scores.')

if __name__=='__main__': main()
