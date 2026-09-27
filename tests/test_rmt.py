import numpy as np
from sklearn.covariance import LedoitWolf
from tfs_stats.rmt import mp_edges, ipr, clip_correlation, ledoit_wolf, min_var_weights
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
