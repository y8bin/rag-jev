import copy
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('human_review',Path('scripts/analyze_koblex_human_review.py'))
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)

def sheet():
    return [{'review_id':'R1','question':'Q','answer':'A','selected_provisions':['LAW'],
             'correctness_0_1_2':None,'selected_evidence_support_0_1_2':None,
             'unsupported_legal_claim':None,'notes':''}]

def test_rejects_missing_fabricated_type_or_edited_review_content():
    template=sheet()
    with pytest.raises(ValueError,match='Missing'):review.validate(sheet(),template)
    valid=copy.deepcopy(template)
    valid[0].update(correctness_0_1_2=2,selected_evidence_support_0_1_2=1,unsupported_legal_claim=False)
    assert review.validate(valid,template)['R1']['correctness_0_1_2']==2
    invalid=copy.deepcopy(valid);invalid[0]['correctness_0_1_2']=True
    with pytest.raises(ValueError,match='invalid'):review.validate(invalid,template)
    invalid=copy.deepcopy(valid);invalid[0]['answer']='EDITED'
    with pytest.raises(ValueError,match='edited'):review.validate(invalid,template)

def test_agreement_does_not_fabricate_kappa_when_undefined():
    perfect=review.agreement([0,1,2],[0,1,2],3)
    assert perfect['raw_agreement']==perfect['kappa']==1
    undefined=review.agreement([1,1],[1,1],3)
    assert undefined['raw_agreement']==1 and undefined['kappa'] is None
    opposite=review.agreement([0,1],[1,0],2)
    assert opposite['raw_agreement']==0 and opposite['kappa']==-1
