import numpy as np
from sklearn.covariance import LedoitWolf
from tfs_stats.rmt import mp_edges, ipr, clip_correlation, ledoit_wolf, min_var_weights, mp_sigma2_iterated, circular_shift_edge, pca_factors
rng=np.random.default_rng(1)
def test_mp_noise():
    N,T=400,1600; X=rng.normal(size=(T,N)); C=np.corrcoef(X,rowvar=False); lam=np.linalg.eigvalsh(C)
    lo,hi=mp_edges(N/T); assert np.isclose(hi,(1+0.5)**2) and lam.max()<hi*1.05 and lam.min()>lo*0.9
def test_ipr():
    V=np.eye(5); assert np.allclose(ipr(V),1); v=np.ones((100,1))/10; assert np.isclose(ipr(v)[0],0.01)
def test_clip():
    N,T=200,500; f=rng.normal(size=(T,1)); X=f@np.ones((1,N))*0.5+rng.normal(size=(T,N))
    C=np.corrcoef(X,rowvar=False); Cc=clip_correlation(C,T)
    assert np.allclose(np.diag(Cc),1) and np.allclose(Cc,Cc.T) and np.linalg.eigvalsh(Cc).min()>0
def test_lw():
    X=rng.normal(size=(60,100)); assert np.allclose(ledoit_wolf(X),LedoitWolf().fit(X).covariance_,rtol=1e-8)
def test_minvar():
    A=rng.normal(size=(50,50)); S=A@A.T+50*np.eye(50); w=min_var_weights(S)
    assert np.isclose(w.sum(),1); g=S@w; assert np.allclose(g,g[0])   # first-order condition: S w proportional to 1

def test_mp_q_above_one_raises():
    import pytest
    with pytest.raises(ValueError): mp_edges(1.2)
def test_sigma2_iterated():
    # pure noise: nothing above the edge, sigma2 stays 1; one strong factor: sigma2 = 1 - lambda_1/N (approximately)
    N,T=200,800; X=rng.normal(size=(T,N)); lam=np.linalg.eigvalsh(np.corrcoef(X,rowvar=False))
    s2,hi,k,ok=mp_sigma2_iterated(lam,N/T); assert ok and k==0 and s2==1.0
    Y=X+rng.normal(size=(T,1))*0.8; lam=np.linalg.eigvalsh(np.corrcoef(Y,rowvar=False))
    s2,hi,k,ok=mp_sigma2_iterated(lam,N/T); assert ok and k>=1 and np.isclose(s2,1-lam[lam>hi].sum()/N)
def test_circular_shift_edge_on_noise():
    # on iid data the shifted-null edge sits just above the MP edge (finite-N fluctuations)
    N,T=100,400; X=rng.normal(size=(T,N)); e,_=circular_shift_edge(X,draws=100,seed=1)
    assert mp_edges(N/T)[1] < e < 1.15*mp_edges(N/T)[1]

def test_pca_factors_recovers_planted_factors():
    T, N = 300, 80; f = rng.normal(size=(T, 2)); L = rng.normal(size=(N, 2)); Z = f @ L.T + 0.3 * rng.normal(size=(T, N))
    Z = (Z - Z.mean(0)) / Z.std(0); V, F, share = pca_factors(Z, 2)
    _, s, _ = np.linalg.svd(np.linalg.lstsq(f, F, rcond=None)[0]); assert np.allclose(V.T @ V, np.eye(2)) and share.sum() > 0.6
    resid = F - f @ np.linalg.lstsq(f, F, rcond=None)[0]; assert resid.var() / F.var() < 0.05   # PCs span the true factors
