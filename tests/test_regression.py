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

# ---- added with D13 (library-backed tfs_stats): multi-series OLS, rank check, FM vs linearmodels, moments path, EWC
from tfs_stats.regression import fm_inference, fm_from_moments, ewc, nw_lags_rule, ewc_nu_rule

def test_ols_qr_many_series():
    Y=np.column_stack([X@rng.normal(size=k)+rng.normal(size=n) for _ in range(7)])
    B,E=ols_qr(X,Y); ref=np.linalg.lstsq(X,Y,rcond=None)[0]
    assert B.shape==(k,7) and E.shape==(n,7) and np.allclose(B,ref,atol=1e-10) and np.allclose(X.T@E,0,atol=1e-8)

def test_ols_qr_rank_deficient_raises():
    Z=np.column_stack([X,X[:,1]*2.0])
    with pytest.raises(np.linalg.LinAlgError): ols_qr(Z,y)

@pytest.mark.parametrize("L",[0,3])
def test_fama_macbeth_vs_linearmodels(L):
    import pandas as pd
    from linearmodels import FamaMacBeth
    T,N=120,300; t=np.repeat(np.arange(T),N); ent=np.tile(np.arange(N),T)
    x=rng.normal(size=(T*N,2)); lam=0.02+0.05*rng.normal(size=T)
    yy=lam[t]*x[:,0]-0.01*x[:,1]+rng.normal(size=T*N)
    ours=fama_macbeth(yy,x,t,nw_lags=L)
    df=pd.DataFrame({'y':yy,'x0':x[:,0],'x1':x[:,1],'const':1.0},index=pd.MultiIndex.from_arrays([ent,t]))
    ref=FamaMacBeth(df.y,df[['const','x0','x1']]).fit(cov_type='kernel',kernel='bartlett',bandwidth=L)
    assert np.allclose(ours['coef'],ref.params.values,rtol=1e-10) and np.allclose(ours['se'],ref.std_errors.values,rtol=1e-8)

def test_fm_unbalanced_and_skips():
    t=np.r_[np.repeat(np.arange(30),50),[99]]; x=rng.normal(size=len(t)); yy=0.3*x+rng.normal(size=len(t))
    out=fama_macbeth(yy,x,t); assert out['n_skipped']==1 and out['lambdas'].shape==(30,2) and 99 not in out['periods']

def test_fm_from_moments_equals_stacked():
    T,N=40,200; t=np.repeat(np.arange(T),N); x=rng.normal(size=(T*N,3)); yy=x@[0.1,-0.2,0.05]+rng.normal(size=T*N)
    D=np.column_stack([np.ones(T*N),x])
    XtX=np.stack([D[t==s].T@D[t==s] for s in range(T)]); Xty=np.stack([D[t==s].T@yy[t==s] for s in range(T)])
    a=fama_macbeth(yy,x,t,nw_lags=2); b=fm_from_moments(XtX,Xty,np.full(T,N),nw_lags=2)
    assert np.allclose(a['lambdas'],b['lambdas'],atol=1e-10) and np.allclose(a['se'],b['se'],rtol=1e-10)

def test_lag_rules():
    assert nw_lags_rule(165)==4 and nw_lags_rule(91)==3 and ewc_nu_rule(165)==12 and ewc_nu_rule(91)==8

def test_ewc_iid_variance():
    # iid N(0, 4): Omega_hat is unbiased for the long-run variance 4 (average over many draws)
    om=[ewc(2*rng.normal(size=165))['omega'] for _ in range(2000)]
    assert abs(np.mean(om)/4-1)<0.03

def test_ewc_ar1_coverage():
    # AR(1) phi = 0.5, T = 165: EWC with t_nu critical values keeps close to nominal 95% coverage of the true mean 0;
    # NW(4) with normal critical values under-covers (the LLSW point)
    T,phi,reps=165,0.5,3000; cov_e=cov_nw=0
    from scipy import stats as st
    for _ in range(reps):
        e=rng.normal(size=T+50); u=np.zeros(T+50)
        for s in range(1,T+50): u[s]=phi*u[s-1]+e[s]
        u=u[50:]; r=ewc(u); cov_e+=abs(r['tstat'])<st.t.ppf(0.975,r['df'])
        f=fm_inference(u,nw_lags=4); cov_nw+=abs(f['tstat'][0])<1.96
    assert 0.93<cov_e/reps<0.97 and cov_nw/reps<cov_e/reps
