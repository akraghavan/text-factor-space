import numpy as np, statsmodels.api as sm, pytest
from tfs_stats.regression import ols_qr, vcov, fama_macbeth
rng=np.random.default_rng(0)
n,k=500,4
X=np.column_stack([np.ones(n),rng.normal(size=(n,k-1))]); e=rng.normal(size=n)*(1+np.abs(X[:,1]))
y=X@np.array([0.5,1.0,-2.0,0.0])+e
g=rng.integers(0,40,size=n)
def test_beta():
    b,r=ols_qr(X,y); assert np.allclose(b,sm.OLS(y,X).fit().params,atol=1e-10)
def test_ill_conditioned():  # cond(X) ~ 1e7, so cond(X'X) ~ 1e14: normal equations lose ~14 of 16 digits, QR keeps ~9
    t=np.linspace(0,1,n); Z=np.column_stack([np.ones(n),t,t+1e-7*rng.normal(size=n)])
    beta=np.array([1.,2.,3.]); yy=Z@beta+1e-9*rng.normal(size=n)
    ref=np.linalg.lstsq(Z,yy,rcond=None)[0]
    b,_=ols_qr(Z,yy); assert np.allclose(b,ref,rtol=1e-3)
    ne=np.linalg.solve(Z.T@Z,Z.T@yy)          # for comparison only: typically off in the leading digit
    print("QR err",np.abs(b-beta).max(),"normal-eq err",np.abs(ne-beta).max())

@pytest.mark.parametrize("kind,kw,ref",[("classical",{},dict()),("HC1",{},dict(cov_type="HC1")),
    ("cluster",{"groups":g},dict(cov_type="cluster",cov_kwds={"groups":g})),
    ("NW",{"lags":5},dict(cov_type="HAC",cov_kwds={"maxlags":5,"use_correction":False}))])
def test_vcov(kind,kw,ref):
    b,r=ols_qr(X,y); V=vcov(X,r,kind,**kw); R=sm.OLS(y,X).fit(**ref).cov_params()
    assert np.allclose(V,R,rtol=1e-8)
def test_fama_macbeth():
    T,N=120,300; t=np.repeat(np.arange(T),N); x=rng.normal(size=T*N); lam=0.02+0.05*rng.normal(size=T)
    yy=lam[t]*x+rng.normal(size=T*N)
    out=fama_macbeth(yy,x[:,None],t,nw_lags=0)
    per=np.array([np.polyfit(x[t==s],yy[t==s],1)[0] for s in range(T)])
    assert np.isclose(out["coef"][1],per.mean()) and np.isclose(out["se"][1],per.std(ddof=1)/np.sqrt(T),rtol=1e-6)
