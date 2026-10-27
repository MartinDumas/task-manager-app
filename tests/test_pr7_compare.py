from scripts.pr7_compare import compare
import pytest


def test_aggregate_and_delta():
    rows=[{'id':f'q{i}', 'baseline':{'score':0,'evidence':[]},
           'semantic':{'score':2,'evidence':['simulated']}} for i in range(10)]
    assert compare(rows)['delta'] == 20


def test_rejects_score_bool():
    rows=[{'id':f'q{i}', 'baseline':{'score':0,'evidence':[]},
           'semantic':{'score':2,'evidence':[]}} for i in range(10)]
    rows[0]['baseline']['score']=True
    with pytest.raises(ValueError):compare(rows)
