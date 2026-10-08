"""analysis/exploratory_family.family_p: the BH sign rule (PREREG change log, 8 Oct)."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'analysis'))
import pytest
from exploratory_family import family_p

def test_directional_specs_use_the_one_sided_p():
    res = {'p_one_sided': 0.01, 'p_two_sided': 0.02}
    assert family_p(res, '+') == (0.01, 'one-sided (+)') and family_p(res, '-') == (0.01, 'one-sided (-)')

def test_specs_without_a_sign_use_the_two_sided_p():
    assert family_p({'p_one_sided': 0.01, 'p_two_sided': 0.02}, 'none') == (0.02, 'two-sided')
    with pytest.raises(KeyError): family_p({'p_one_sided': 0.01}, 'none')
