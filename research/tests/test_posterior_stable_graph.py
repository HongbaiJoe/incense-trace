import numpy as np
import pytest
from scipy.stats import beta
from scipy.integrate import quad
from scipy.special import logit
from xiangji.models.posterior_stable_graph import beta_logit_moments, decompose_variation, project_composition, PosteriorStableGraphCompletion
from xiangji.models.data import FormulaRecord

def test_exact_moments_against_quadrature():
    a, b = 2.3, 4.1
    mu, var = beta_logit_moments(a, b)
    numerical = quad(lambda x: logit(x) * beta.pdf(x, a, b), 0, 1)[0]
    numerical_var = quad(lambda x: (logit(x)-mu)**2 * beta.pdf(x, a, b), 0, 1)[0]
    assert mu == pytest.approx(numerical, abs=1e-8)
    assert var == pytest.approx(numerical_var, abs=1e-8)

def test_noise_correction_and_degenerate_source():
    mu, tau, vm = decompose_variation(np.array([0.,2.]), np.ones(2), np.ones(2))
    assert mu == 1
    assert tau == 1
    assert vm == 1
    _, tau, vm = decompose_variation(np.array([3.]), np.array([2.]), np.ones(1))
    assert tau == 0 and vm == 2

def test_projection_preserves_ratios_and_mass():
    p = project_composition({'a':.1,'b':.2,'c':.3,'d':.4}, {'a':2,'b':1}, .6)
    assert sum(p.values()) == pytest.approx(1)
    assert p['a']/p['b'] == pytest.approx(2)
    assert p['c']/p['d'] == pytest.approx(.75)
    assert p['a']+p['b'] == pytest.approx(.6)
    with pytest.raises(ValueError): project_composition({'a':1}, {'a':1}, .5)

def test_unknown_retention_and_prediction():
    rows=[FormulaRecord(str(i),str(i),str(i%2),'test',c) for i,c in enumerate([
        {'a':.5,'b':.5},{'a':.2,'b':.3,'c':.5},{'a':.2,'c':.3,'d':.5},{'b':.4,'c':.6}])]
    model=PosteriorStableGraphCompletion().fit(rows)
    k,p=model.unknown_count_distribution(1)
    prior=np.array([2.5,2.5])/(k+1)
    assert np.allclose(p,prior/prior.sum())
    result=model.predict_partial({'a':2})
    assert sum(result['composition'].values()) == pytest.approx(1)
    assert result['known_mass_source']=='training_neighbours'
    with pytest.raises(ValueError): model.predict_partial({'unknown':1})
