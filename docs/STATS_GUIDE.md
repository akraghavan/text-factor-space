# Estimators guide

The project's estimators live in `tfs_stats/`: three in `regression.py` and five in `rmt.py`, plus the custom ones listed near the end. Since decision D13 (28 Sep) the assistant writes them on standard libraries (statsmodels, linearmodels, scikit-learn, scipy, numpy), the way research code is written anywhere. Your job is different and harder: be able to explain every one of them in an interview, from the derivation to the conventions in the code. For each estimator this guide gives its job in the project, the math with the derivation, how the project computes it, what its test checks, the traps, and the questions an interviewer is likely to ask. One exercise stays hand-written because interviews test it directly: OLS by hand, batch and streaming (the Practice section, with a full walkthrough).

## How we work on these {#stats-workflow}

| Who | Does |
|---|---|
| You | Read each card, explain it back, answer its "Check yourself" questions, do the OLS practice |
| Coding assistant (in the repo) | Writes `tfs_stats/` on libraries, with a docstring per function that names the library call and every convention; tutors you in `practice/` without writing your solution |
| Reviewer (the dashboard session) | Writes and maintains these explanations, runs the explain-back sessions, checks the code against the cards, keeps the tracker current |

The loop for each estimator:

1. **Read the card.** The math first, then "How the project computes it".
2. **Read the code.** Open the function in `tfs_stats/`. It is short: mostly one library call plus the conventions around it.
3. **Explain it back.** In review, say "explain-back `<function>`" and explain in your own words what it computes, why this way, and one trap. I push back like an interviewer would and correct anything off.
4. **Answer the probes.** Work through "Check yourself" on paper; that is the interview material.
5. **Tracker.** When the explanation holds up, the tracker moves to "explained back".

The order follows the results: C and E need `ols_qr`, `vcov` and `fama_macbeth` first; B needs `mp_edges` and `ipr`; D (the stretch goal) needs `clip_correlation`, `min_var_weights` and `ledoit_wolf`.

| # | Estimator | Explain back by | Why then |
|---|---|---|---|
| 1 | `ols_qr` | Tue 29 Sep | Every regression in the project; also the practice exercise |
| 2 | `vcov` | Tue 29 Sep | Every standard error |
| 3 | `fama_macbeth`, EWC | Wed 30 Sep | The headline inference for C (Q1) and E (Q3) |
| 4 | `mp_edges`, `ipr` | Thu 1 Oct | B's noise edge and localisation |
| 5 | `clip_correlation`, `min_var_weights`, `ledoit_wolf` | Thu 1 Oct | D, if it stays in |

## Toolkit: reading the code and running the tests {#stats-toolkit}

Run tests from the repo root with the virtual environment active:

```text
source .venv/bin/activate
python -m pytest tests/test_rmt.py -k ipr -q                   # one test
python -m pytest tests/test_regression.py -k "vcov and HC1" -q  # one case of a parametrised test
python -m pytest tests/test_regression.py -k ill -q -s          # -s shows print() output
make test                                                       # everything
```

In the output, `s` means skipped (a function still raises `NotImplementedError`), `F` means the code disagreed with the reference or crashed, and `.` means passed.

The library calls you will see in `tfs_stats/`, and the numpy you need for reading them and for the practice. Try each on a 4×3 example in a Python shell:

| Job | Call | Note |
|---|---|---|
| OLS with a chosen covariance | `sm.OLS(y, X).fit(cov_type=...)` | `'nonrobust'`, `'HC1'`, `'cluster'` (with `cov_kwds={'groups': g}`), `'HAC'` (with `cov_kwds={'maxlags': L}`); `.params`, `.bse`, `.cov_params()` |
| Fama–MacBeth reference | `linearmodels.FamaMacBeth(y, X).fit(cov_type='kernel')` | Used in tests to check the project's own Fama–MacBeth |
| Ledoit–Wolf | `sklearn.covariance.LedoitWolf().fit(X).covariance_` | Identity target, `shrinkage_` holds δ |
| Least squares for many series at once | `np.linalg.lstsq(Z, Y)` or QR with `scipy.linalg.solve_triangular` | One factorisation of Z serves every column of Y |


| Need | numpy | Note |
|---|---|---|
| Matrix product, transpose | `A @ B`, `A.T` | `X.T @ y` with a 1-D `y` returns a 1-D array |
| Shapes | `X.shape`, `y.ndim` | Most bugs are shape bugs: `y` is `(n,)`, never `(n, 1)` |
| QR factorisation | `np.linalg.qr(X)` | Default reduced mode: `Q` is n×k, `R` is k×k |
| Scale each row | `X * e[:, None]` | Broadcasting: row i is multiplied by $e_i$ |
| Labels to integers | `np.unique(g, return_inverse=True)` | Any labels become codes 0…G−1 |
| Sum rows by group | `np.add.at` | Or sort by group and use `np.add.reduceat` |
| Symmetric eigenproblem | `np.linalg.eigh(C)` | Eigenvalues ascending; eigenvectors are the columns |
| Linear solve | `np.linalg.solve(A, b)` | Never form an inverse just to multiply by it |
| Compare arrays | `np.allclose(a, b, rtol=…, atol=…)` | What every test uses |

Habits that save hours: build a case small enough to check by hand (n = 5, k = 2); print shapes at each step; loop over small dimensions (k columns, T months) freely, but never over n, which reaches hundreds of thousands of rows in C.

## regression.py {#stats-regression}

Regression and inference. The three functions build on each other: `fama_macbeth` runs `ols_qr` once per period and uses the `vcov` logic for the standard error of the mean slope.

### ols_qr(X, y) → (beta, resid) {#fn-ols_qr}

**Job in the project.** The workhorse. `src/formation.residuals` already calls it once per stock per window: excess returns on $[1, f_t]$ with the six Fama–French and momentum factors over 252 trading days. Those residuals are B's correlation matrix and C's outcome variable. `fama_macbeth` calls it once per month for C and E. If `ols_qr` is wrong, everything downstream is wrong, which is why it comes first on the critical path.

**The math.** Least squares minimises $\lVert y - X\beta\rVert^2$. Setting the gradient to zero gives the normal equations $X^\top X\hat\beta = X^\top y$. Solving those directly is the textbook route and the numerically bad one. Write the SVD $X = U\Sigma V^\top$. Then $X^\top X = V\Sigma^2 V^\top$, so its singular values are the squares of those of $X$ and

$$\kappa(X^\top X) = \frac{\sigma_{\max}^2}{\sigma_{\min}^2} = \kappa(X)^2 .$$

Float64 carries about 16 digits and a solve loses roughly $\log_{10}\kappa$ of them. In the test's ill-conditioned case $\kappa(X) \approx 1.8\times10^{7}$, so $\kappa(X^\top X) \approx 3\times10^{14}$: the normal equations keep about 2 digits and QR keeps about 9.

QR avoids the squaring. Factor $X = QR$ with $Q$ (n×k) having orthonormal columns, $Q^\top Q = I_k$, and $R$ (k×k) upper triangular. Substitute into the normal equations:

$$R^\top Q^\top Q R\,\beta = R^\top Q^\top y \;\Rightarrow\; R^\top R\,\beta = R^\top Q^\top y \;\Rightarrow\; R\beta = Q^\top y ,$$

the last step because $R$ is invertible when $X$ has full column rank. The geometric view says the same thing. Split $y$ into its part in the column space of $X$ and the rest:

$$\lVert y - X\beta\rVert^2 = \lVert Q^\top y - R\beta\rVert^2 + \lVert (I - QQ^\top)\,y\rVert^2 .$$

The second term does not depend on $\beta$, and the first is zero at the solution. So the residual is $(I - QQ^\top)y$.

$R\beta = c$ with $c = Q^\top y$ is solved from the bottom row up, by back-substitution:

$$\beta_k = \frac{c_k}{R_{kk}}, \qquad \beta_i = \frac{1}{R_{ii}}\Big(c_i - \sum_{j>i} R_{ij}\,\beta_j\Big), \quad i = k-1, \dots, 1 .$$

Residuals are $e = y - X\hat\beta$, which equals $y - Qc$ because $X\hat\beta = QR\hat\beta = Qc$.

**What the test checks.** `test_beta`: n = 500, an intercept and three normal regressors, heteroskedastic noise; $\hat\beta$ must match statsmodels to `atol=1e-10`. `test_ill_conditioned`: the third column is the second plus $10^{-7}$ noise; $\hat\beta$ must match `np.linalg.lstsq` to `rtol=1e-3`. The normal equations usually fail this and QR passes. Run it with `-s` to see both errors printed.

**How the project computes it.** A QR factorisation from numpy with SciPy's triangular solve (`np.linalg.qr`, `scipy.linalg.solve_triangular`), accepting a matrix of responses so one factorisation of the factor matrix serves all 1,000 stocks in a window. That is the main speed-up in `formation.residuals`: the factors are the same for every stock, so only the right-hand side changes. The practice exercise below has you write the same thing by hand.

**Traps.**

- numpy's QR can put negative numbers on the diagonal of $R$. That is fine; the solution is unchanged.
- A zero or tiny $R_{ii}$ means a collinear column, such as two identical dummies. Raise a clear error when $|R_{ii}|$ is tiny relative to the largest $|R_{jj}|$, instead of dividing by almost zero.
- If `y` arrives as `(n, 1)`, `Q.T @ y` becomes `(k, 1)` and later lines broadcast silently. Check `y.ndim`.

**Check yourself.**

- Why is $\kappa(X^\top X) = \kappa(X)^2$?
- $Q^\top$ is k×n. Why is $\lVert y - X\beta\rVert \neq \lVert Q^\top y - R\beta\rVert$ in general, and what is the missing piece?
- What do QR and back-substitution cost in n and k? Which dominates for a 252×7 regression?

**Read.** Trefethen & Bau, Lectures 7 (QR), 11 (least squares), 17 (back-substitution), 18–19 (conditioning and stability of least squares). The numpy `qr` docs. To see a production implementation: statsmodels `linear_model.py`, where `OLS.fit(method="qr")` does the same thing.

### vcov(X, resid, kind, groups, lags) → V {#fn-vcov}

**Job in the project.** The uncertainty of $\hat\beta$. Every t-statistic in the project divides a coefficient by the square root of a diagonal element of this matrix. `fama_macbeth` uses it for the standard error of the mean slope, which is the standard error on the headline numbers of C and E.

**The math: one sandwich, four fillings.** From $\hat\beta = (X^\top X)^{-1}X^\top y$ and $y = X\beta + \varepsilon$,

$$\hat\beta - \beta = (X^\top X)^{-1}X^\top\varepsilon \;\Rightarrow\; \operatorname{Var}(\hat\beta\mid X) = \underbrace{(X^\top X)^{-1}}_{\text{bread}}\;\underbrace{X^\top\Omega X}_{\text{meat}}\;\underbrace{(X^\top X)^{-1}}_{\text{bread}}, \qquad \Omega = \operatorname{E}[\varepsilon\varepsilon^\top\mid X] .$$

Written out, the meat is $X^\top\Omega X = \sum_i\sum_j \omega_{ij}\,x_i x_j^\top$. The four kinds differ only in which $\omega_{ij}$ they allow to be non-zero, and each estimates $\omega_{ij}$ by $e_i e_j$:

| kind | Assumption on $\Omega$ | Meat | Factor |
|---|---|---|---|
| `classical` | $\sigma^2 I$ | $s^2 X^\top X$, $s^2 = e^\top e/(n-k)$, so $V = s^2 (X^\top X)^{-1}$ | none |
| `HC1` | diagonal, any values | $\sum_i e_i^2\, x_i x_i^\top$ | $n/(n-k)$ |
| `cluster` | non-zero only within a group | $\sum_g u_g u_g^\top$, $u_g = \sum_{i\in g} x_i e_i$ | $\frac{G}{G-1}\cdot\frac{n-1}{n-k}$ |
| `NW` | non-zero only for $\lvert t-s\rvert \le L$ | $\Gamma_0 + \sum_{l=1}^{L} w_l(\Gamma_l + \Gamma_l^\top)$ | none |

For the cluster row, keeping only same-group pairs gives $\sum_g\sum_{i,j\in g} e_i e_j\, x_i x_j^\top = \sum_g \big(\sum_{i\in g} x_i e_i\big)\big(\sum_{j\in g} x_j e_j\big)^\top$, which is the $u_g u_g^\top$ form. For Newey–West, $\Gamma_l = \sum_{t=l+1}^{n} e_t e_{t-l}\, x_t x_{t-l}^\top$ and $w_l = 1 - \frac{l}{L+1}$. The Bartlett weights are what make the estimate positive semi-definite (Newey & West 1987). The unweighted sum can produce negative variances.

One object unifies all four. Stack the **scores** $g_i = e_i x_i$ as rows of an n×k matrix $G$. Then the HC meat is $G^\top G$; the cluster meat is the same product after first summing the rows of $G$ within each group; and $\Gamma_l$ is $G^\top G$ between $G$ and itself shifted by $l$ rows. Once you see that, each kind is a few lines.

**The bread without `inv`.** $X^\top X = R^\top Q^\top Q R = R^\top R$, so $(X^\top X)^{-1} = R^{-1}R^{-\top}$. Get $R^{-1}$ by back-substitution against each column of the identity, never with `inv`.

**What the test checks.** n = 500, k = 4, errors scaled by $1 + \lvert x_1\rvert$ (so the classical formula is wrong for this data, which is the point), 40 random clusters, and NW with 5 lags. Each kind must match statsmodels to `rtol=1e-8`. That is effectively exact, so the finite-sample factors must be exactly the ones in the table and the docstring. The NW case matches statsmodels' `HAC` with `use_correction=False`, meaning no factor at all.

**How the project computes it.** statsmodels' sandwich estimators: `sm.OLS(y, X).fit(cov_type='nonrobust' | 'HC1' | 'cluster' | 'HAC')`, with `use_correction=False` for Newey–West so there is no finite-sample factor. The factors in the table above are exactly what statsmodels applies, which is why the test can require agreement to `rtol=1e-8`.

**Traps.**

- Group labels can be anything (strings, non-contiguous integers). Map them to codes first.
- NW assumes rows are in time order. An off-by-one in the shift is the classic bug, and so is writing $L$ instead of $L+1$ in the Bartlett denominator.
- $G$ in the cluster factor is the number of groups, not the score matrix.

**Check yourself.**

- In the test data, the noise grows with $\lvert x_1\rvert$. Which kinds are valid and which is not? Which standard error do you expect to be most wrong?
- If every observation is its own cluster, what does the cluster estimator become?
- With $L = 0$, what is NW?
- Why are Bartlett weights needed?

**Read.** Cameron & Miller (2015) is the best single read: a practitioner's guide with a free PDF. Also White (1980), MacKinnon & White (1985) for HC0–HC3, and Newey & West (1987, 1994). Petersen (2009) has a web page with test data and reference standard errors you can reproduce. To see a production implementation: statsmodels `sandwich_covariance.py` and the `get_robustcov_results` docs.

### fama_macbeth(y, X, t, nw_lags) → dict {#fn-fama_macbeth}

**Job in the project.** The headline inference. C (Q1): each month, regress the pair outcome $z_{ij,t}$ on text similarity and controls; the average monthly slope on similarity is $\bar b$. E (Q3): each month, regress stock returns on PEERMOM and controls. Returns within a month share market shocks, so observations inside a month are strongly correlated. Fama–MacBeth sidesteps that by letting each month contribute a single estimate, then doing inference on the time series of those estimates.

**The math.** For each period $t$, run OLS of $y$ on $[1, X]$ using that period's rows to get $\hat\lambda_t$ (length k+1). The estimate is $\bar\lambda = \frac1T\sum_t \hat\lambda_t$. Its variance is

$$\operatorname{Var}(\bar\lambda) = \frac{1}{T^2}\sum_{s}\sum_{u}\operatorname{Cov}(\lambda_s,\lambda_u) = \frac1T\Big[\gamma_0 + 2\sum_{l=1}^{T-1}\Big(1-\frac{l}{T}\Big)\gamma_l\Big],$$

with $\gamma_l$ the lag-$l$ autocovariance of the slope series. If the slopes are uncorrelated over time, the standard error is $\operatorname{sd}(\lambda)/\sqrt T$. If they are persistent, Newey–West truncates the sum at $L$ with Bartlett weights. The project uses the rule $L = \lfloor 4(T/100)^{2/9}\rfloor$: $L = 3$ at $T = 91$ (E's test period) and $L = 4$ at $T = 165$.

The trick that makes this short: **a mean is OLS on a constant.** Regress the slope series on a column of ones. The coefficient is $\bar\lambda$, the residuals are $\hat\lambda_t - \bar\lambda$, and `vcov` with `kind='NW'` returns exactly the Newey–West variance of the mean. So `fama_macbeth` is a loop of `ols_qr` calls followed by `vcov`.

**A convention to settle — settled 28 Sep (D13): $T/(T-1)$ at every lag, as linearmodels' `FamaMacBeth` does (checked in the tests).** With `nw_lags=0` the test expects $\operatorname{sd}(\lambda)$ with `ddof=1`, divided by $\sqrt T$. That equals `vcov(ones, λ − λ̄, 'classical')`. `vcov` with `'NW'` and $L = 0$ divides by $T$ instead of $T-1$, so it is smaller by the factor $(T-1)/T$. Two consistent options: use `classical` at $L = 0$ and `NW` above it, or multiply NW by $T/(T-1)$ at every $L$. The second is what Stata's `newey` does (its $n/(n-k)$ with $k = 1$) and makes $L = 0$ reproduce the test exactly. Apply the factor inside `fama_macbeth`; `vcov`'s own NW must stay uncorrected to pass its test.

**What the test checks.** T = 120 months, N = 300 observations a month, one regressor, true slopes $0.02 + 0.05\,\eta_t$. `coef[1]` must equal the mean of the per-month `np.polyfit` slopes, and `se[1]` must equal `std(ddof=1)/sqrt(T)` to `rtol=1e-6`. The output is a dict with `coef`, `se`, `tstat` (each k+1) and `lambdas` (T×(k+1)).

**How the project computes it.** One cross-sectional regression per period (`ols_qr`), then the slope series goes through statsmodels' HAC on a constant, with the $T/(T-1)$ factor applied (the convention above; the coding assistant records the choice in the docstring). For C the per-month regressions come from monthly sufficient statistics ($X^\top X$, $X^\top y$), because the stacked panel does not fit in memory; the inference on the slope series is the same. The test cross-checks against a per-period `polyfit` and against linearmodels' `FamaMacBeth`.

**Traps.**

- The panel is unbalanced: the number of rows per period varies.
- A period with fewer rows than k+1 cannot be estimated. Skip it and report how many were skipped.
- `X` may arrive 1-D. The intercept is added inside, so callers must not include one.
- Period labels need not be contiguous integers.

**Scale note for C.** C has 499,500 pairs a month over about 165 months. Stacked, that is about 82 million rows × roughly 15 columns, around 10 GB in float64, too much to pass as one array next to everything else in 24 GB. C will probably run `ols_qr` month by month and then only needs the "mean and NW standard error of a slope series" step. That argues for splitting `fama_macbeth` into two pieces: the per-period slopes, and the inference on a slope series. Decide it together when you get there.

**Check yourself.**

- Which correlation does Fama–MacBeth fix, and which does it not? Petersen (2009): a persistent firm or pair effect biases FM standard errors down, and NW on the slopes only partly repairs it.
- Why is the lag $L = 4$ at $T = 165$?
- Why does E report NW(2) at all? (For comparability with Hoberg & Phillips.)

**Read.** Fama & MacBeth (1973). Cochrane, *Asset Pricing*, ch. 12, §12.3. Petersen (2009), on why FM standard errors can still be too small. Newey & West (1994), on the lag rule. To compare: linearmodels' `FamaMacBeth` docs.

## rmt.py {#stats-rmt}

Random-matrix tools for B and the covariance estimators for D. `np.linalg.eigh` and `np.linalg.solve` are fine here.

### ipr(V) → array {#fn-ipr}

**Job in the project.** B's localisation measure. Is an eigenvector spread over the whole market (the market mode, or noise) or concentrated on a few stocks (a sector, or a cluster that text finds)?

**The math.** For a unit column $v$, $\text{IPR} = \sum_i v_i^4$, and $1/\text{IPR}$ is the effective number of stocks in the mode. A vector concentrated on one stock gives 1. One spread evenly over $m$ stocks, each component $\pm 1/\sqrt m$, gives $m\cdot 1/m^2 = 1/m$. So a perfectly flat vector over all $N$ gives $1/N$.

A *random* unit vector gives about $3/N$, not $1/N$. Write $v = g/\lVert g\rVert$ with $g$ standard normal in $\mathbb R^N$. The length $\lVert g\rVert$ is independent of the direction $v$, so $\operatorname{E} g_i^4 = \operatorname{E}\lVert g\rVert^4\cdot\operatorname{E} v_i^4$, which reads $3 = N(N+2)\,\operatorname{E} v_i^4$. Summing over $i$:

$$\operatorname{E}[\text{IPR}] = \frac{3}{N+2} \approx \frac3N .$$

Plerou et al. (2002) report an average IPR of about $3\times10^{-3}$ at $N = 1{,}000$ and describe it as "≈ 1/N"; the value is $3/N$. The SPEC repeated "≈ 1/N" and was corrected on 27 Sep. This $3/N$ is the noise baseline B compares its modes against.

**How the project computes it.** One line of numpy: the column sums of the fourth powers of the eigenvector matrix.

**What the test checks.** The columns of a 5×5 identity each give 1; a flat vector of length 100 gives 0.01.

**Traps.** `eigh` returns eigenvectors as columns (`V[:, k]`), so sum over the right axis and return one value per column.

**Check yourself.** What IPR does the market mode have if every stock loads about equally? Derive $\operatorname{E} g^4 = 3$ for a standard normal.

**Read.** Plerou et al. (2002), eq. (20) and the surrounding discussion.

### mp_edges(q, sigma2) → (λ₋, λ₊) {#fn-mp_edges}

**Job in the project.** B's noise line. A correlation matrix estimated from $T$ days is noisy: even when every true correlation is zero, its eigenvalues spread out. Marčenko–Pastur says how far. Eigenvalues above $\lambda_+$ are candidate structure (the market, sectors, perhaps text modes); the bulk below is indistinguishable from noise. `clip_correlation` uses the same edge.

**The math.** Let $X$ be T×N with independent entries of variance $\sigma^2$ and $C = X^\top X/T$. As $N, T\to\infty$ with $q = N/T \le 1$ fixed, the eigenvalues of $C$ fill $[\lambda_-, \lambda_+]$ with density

$$\rho(\lambda) = \frac{\sqrt{(\lambda_+ - \lambda)(\lambda - \lambda_-)}}{2\pi q\sigma^2\lambda}, \qquad \lambda_\pm = \sigma^2\big(1 \pm \sqrt q\big)^2 .$$

You can check the spread from the first two moments without the full derivation. The mean eigenvalue is $\operatorname{tr}(C)/N = \sigma^2$. For the second moment, $\operatorname{tr}(C^2)/N = \frac1N\sum_{ij} C_{ij}^2$. The $N$ diagonal terms are each about $\sigma^4$. Each of the $N(N-1)$ off-diagonal terms is an average of $T$ independent products, with variance $\sigma^4/T$. So $\operatorname{tr}(C^2)/N \approx \sigma^4\big(1 + \tfrac{N-1}{T}\big) \approx \sigma^4(1+q)$, and the variance of the eigenvalues is $\sigma^4 q$: the spread grows like $\sqrt q$. The edges themselves come from the Stieltjes transform (Potters & Bouchaud 2020, ch. 4).

The function is one line. The understanding is the work. SPEC §6's table follows from it: $N = 500$, $T = 756$ gives $q = 0.661$ and $\lambda_+ = 3.288$.

**How the project computes it.** The closed form above, one line.

**What the test checks.** $N = 400$, $T = 1{,}600$ ($q = 0.25$): $\lambda_+$ must be exactly 2.25, and on pure noise the largest sample eigenvalue must stay below $1.05\,\lambda_+$ and the smallest above $0.9\,\lambda_-$.

**Where the project goes further.** In B the caller adjusts two inputs: $\sigma^2 = 1 - \lambda_{\max}/N$, iterated, because the market mode takes $\lambda_{\max}$ of the trace; and $q_{\text{eff}} = N/(T-K-1)$ for residuals from a K-factor regression.

**Traps.** $q > 1$ (more stocks than days): $N - T$ eigenvalues are exactly zero and the formula for $\lambda_-$ no longer describes the smallest eigenvalue. `mp_edges` raises a `ValueError` (decided 28 Sep).

**Two companions in `tfs_stats/rmt.py` (added 28 Sep).**

- `mp_sigma2_iterated(eigs, q)` runs the iteration $\sigma^2 = 1 - \sum_{\lambda_k > \lambda_+(\sigma^2)}\lambda_k/N$. The map is monotone: a lower $\sigma^2$ lowers the edge, which lets more eigenvalues above it, which lowers $\sigma^2$ again. It converges when the bulk really is MP-shaped and runs away when the bulk is wider (heavy tails, volatility clustering): the edge walks into the bulk. On a runaway it returns Laloux's one-step value with `converged=False`. In B the iteration ran away in every year 2014–2025, on raw and residual spectra, which is the practical argument for the next function.
- `circular_shift_edge(Z, draws, quantile)` builds the noise edge from the data: shift each stock's series in time by an independent random offset (wrapping around), recompute the top eigenvalue, repeat 200 times, take the 95th percentile. Each series keeps its own fat tails and autocorrelation; only the synchrony between stocks is destroyed. In B it comes out at 3.32–3.35 for N = 500, T = 756, a little above the MP edge 3.29. Test: on iid data it lands between $\lambda_+$ and $1.15\lambda_+$.

**Check yourself.** Why is $\sigma^2 = 1 - \lambda_1/N$ the right variance once the market mode is removed? Why do heteroskedasticity and autocorrelation widen the bulk?

**Read.** Laloux, Cizeau, Bouchaud & Potters (1999): four pages, read it whole. Potters & Bouchaud (2020), ch. 4. Bouchaud & Potters (2009) for the finance applications. Marčenko & Pastur (1967) is the original.

### clip_correlation(C, T) → C̃ {#fn-clip_correlation}

**Job in the project.** D's RMT estimator (SPEC §8, estimator 5), and a cleaned matrix for B: keep the eigen-directions above the noise edge and flatten the rest.

**The math.** Decompose $C = V\Lambda V^\top$. Take $\lambda_+$ from `mp_edges(N/T)`. Keep every $\lambda_k > \lambda_+$. Replace every $\lambda_k \le \lambda_+$ by the average of those bulk eigenvalues. The trace is the sum of the eigenvalues, so replacing a group by its average keeps $\operatorname{tr} = N$. Rebuild $\tilde C = V\tilde\Lambda V^\top$. Its diagonal is no longer exactly 1, so rescale: $\tilde C \leftarrow D^{-1/2}\tilde C D^{-1/2}$ with $D = \operatorname{diag}(\tilde C)$.

Why the average and not zero: zeros would make the matrix singular, and a minimum-variance portfolio would load on the zeroed directions without limit. Why rescale: a correlation matrix has a unit diagonal by definition.

**What the test checks.** $N = 200$, $T = 500$, a one-factor model: the result must have a unit diagonal, be symmetric, and have a strictly positive smallest eigenvalue.

**How the project computes it.** `np.linalg.eigh`, the edge from `mp_edges`, bulk eigenvalues replaced by their mean, rebuilt, rescaled to a unit diagonal and symmetrised. There is no standard library function for clipping; it is a few lines of numpy.

**Traps.** `eigh` sorts eigenvalues in ascending order. If no eigenvalue is above the edge the answer is essentially the identity, which is correct. For residual correlation matrices the caller should pass the effective sample size, $T-K-1$.

**Check yourself.** Why is the result positive definite, and why does the rescaling keep it so? What does clipping do to a minimum-variance portfolio built on it?

**Read.** Laloux et al. (1999; 2000). Bun, Bouchaud & Potters (2017), the clipping section. Bouchaud & Potters (2009).

### min_var_weights(S) → w {#fn-min_var_weights}

**Job in the project.** D's portfolio. For each covariance estimator, D forms the global minimum-variance portfolio and measures its realised out-of-sample volatility. GMV weights depend only on $\hat\Sigma$, so realised volatility isolates the quality of the covariance estimate (SPEC §8).

**The math.** Minimise $w^\top S w$ subject to $\mathbf 1^\top w = 1$. With $\mathcal L = w^\top S w - 2\gamma(\mathbf 1^\top w - 1)$, the first-order condition is $2Sw - 2\gamma\mathbf 1 = 0$, so $Sw = \gamma\mathbf 1$ and $w = \gamma S^{-1}\mathbf 1$. The constraint fixes $\gamma = 1/(\mathbf 1^\top S^{-1}\mathbf 1)$. The minimum variance itself is $w^\top S w = \gamma^2\,\mathbf 1^\top S^{-1}\mathbf 1 = \gamma$.

Compute it with one linear solve, $Sz = \mathbf 1$, then $w = z/\sum_i z_i$. Never form $S^{-1}$: a solve is cheaper and more accurate than an inverse followed by a product.

**How the project computes it.** `np.linalg.solve(S, ones)` and a normalisation.

**What the test checks.** $S = AA^\top + 50I$ with $N = 50$: the weights sum to 1, and every component of $Sw$ is equal (the first-order condition).

**Traps.** A singular $S$ (a sample covariance with $N \ge T$) makes the solve fail or explode, which is exactly why D shrinks before it optimises. Weights can be negative: this is unconstrained GMV, with short positions allowed.

**Check yourself.** What is the portfolio's variance in terms of $\gamma$? Why do long-only constraints act like shrinkage (Jagannathan & Ma 2003)?

**Read.** Markowitz (1952). Jagannathan & Ma (2003). Engle, Ledoit & Wolf (2019) for the evaluation protocol D follows.

### ledoit_wolf(X) → Σ̂ {#fn-ledoit_wolf}

**Job in the project.** D's classic benchmark (SPEC §8, estimator 2), and the template for the project's own text-target shrinkage, which uses the same bias–variance logic with a different target.

**The math (Ledoit & Wolf 2004).** Demean the columns of $X$ (T×N). The sample covariance is $S = X^\top X/T$, dividing by $T$ and not $T-1$. The target is $\mu I$ with $\mu = \operatorname{tr}(S)/N$. The estimator is

$$\hat\Sigma = \delta\,\mu I + (1-\delta)\,S, \qquad \delta\in[0,1].$$

Ledoit–Wolf measure matrices with the Frobenius norm scaled by $N$: $\langle A, B\rangle = \operatorname{tr}(AB^\top)/N$ and $\lVert A\rVert^2 = \langle A, A\rangle$, so quantities stay of order one as $N$ grows. Three numbers:

- $d^2 = \lVert S - \mu I\rVert^2$: how far the sample covariance is from the target.
- $\bar b^2 = \frac{1}{T^2}\sum_t \lVert x_t x_t^\top - S\rVert^2$: how noisy $S$ is, and $b^2 = \min(\bar b^2, d^2)$.
- $\delta = b^2/d^2$.

This is the same trade-off as SPEC §8's one-entry derivation, $\delta^* = \operatorname{Var}(u)/[\operatorname{Var}(u) + (t-\rho)^2]$: $b^2$ plays the variance and $d^2 - b^2$ the squared distance between target and truth.

**The computational trick.** Never build $T$ matrices of size N×N. Expand the sum, using $\sum_t x_t x_t^\top = TS$:

$$\sum_t\lVert x_t x_t^\top - S\rVert^2 = \sum_t\lVert x_t x_t^\top\rVert^2 - 2\Big\langle\sum_t x_t x_t^\top, S\Big\rangle + T\lVert S\rVert^2 = \sum_t\lVert x_t x_t^\top\rVert^2 - T\lVert S\rVert^2 ,$$

and $\lVert x_t x_t^\top\rVert^2 = (x_t^\top x_t)^2/N$. So $\bar b^2$ needs only the row sums of squares of $X$ and $\operatorname{tr}(S^2)$. Work this through on paper; it is the whole trick, and a good interview answer to "how would you compute this for 3,000 stocks?"

**How the project computes it.** scikit-learn's `LedoitWolf().fit(X)`, whose `covariance_` is $\hat\Sigma$ and `shrinkage_` is $\delta$. The derivation above is what that call computes, convention for convention.

**What the test checks.** $T = 60$, $N = 100$, so $S$ is singular and shrinkage is essential; $\delta$ comes out close to 1. The result must equal scikit-learn's `LedoitWolf().fit(X).covariance_` to `rtol=1e-8`, so the conventions must match exactly: demean, divide by $T$, cap $b^2$ at $d^2$.

**Traps.** `np.cov` divides by $T-1$ and fails the test. The "Honey, I shrunk the sample covariance matrix" paper shrinks towards a *constant-correlation* target, which is a different estimator (SPEC §8, estimator 4). Here you implement the identity target from the 2004 JMVA paper.

**Check yourself.** Why is $\delta$ near 1 when $N > T$? What happens to $\delta$ as $T\to\infty$ with $N$ fixed?

**Read.** Ledoit & Wolf (2004, JMVA; free PDF), the section that defines the estimator. "Honey, I shrunk…" (2004) for intuition. To see a production implementation: scikit-learn's `ledoit_wolf_shrinkage` in `_shrunk_covariance.py`, to compare conventions line by line.

## Practice: OLS by hand {#stats-practice}

Two Sigma's later coding round reportedly asks candidates to implement linear regression efficiently, including a streaming version (Glassdoor and WSO reports, not the firm's own words). This is the one piece worth writing yourself. The coding assistant puts stubs and tests in `practice/ols_by_hand.py` and `practice/test_ols_by_hand.py`; you fill them in. For each step: try it first, then open the walkthrough. Run the tests with `python -m pytest practice -q`.

### Step 1: one regressor, no intercept {#fn-practice-1d}

Minimise $\sum_i (y_i - \beta x_i)^2$. The derivative is $-2\sum_i x_i(y_i - \beta x_i) = 0$, so

$$\hat\beta = \frac{\sum_i x_i y_i}{\sum_i x_i^2}.$$

Streaming is immediate: keep the two running sums $S_{xy}$ and $S_{xx}$, add $x_i y_i$ and $x_i^2$ as each point arrives, and divide whenever asked. Memory is two numbers, whatever $n$ is.

<details markdown="1"><summary>Walkthrough</summary>

```python
def ols_1d_no_intercept(x, y):
    return (x @ y) / (x @ x)
```

`x @ y` is $\sum_i x_i y_i$ for 1-D arrays. An interviewer's follow-up: what if $\sum x_i^2 = 0$? (All $x_i = 0$: $\beta$ is not identified; raise.)

</details>

### Step 2: many regressors, batch, via QR {#fn-practice-qr}

The derivation is on the `ols_qr` card: $X = QR$ turns the normal equations into $R\beta = Q^\top y$, solved from the bottom row up. Write `back_substitute(R, c)` yourself with a loop from the last row to the first, then `ols_qr_by_hand(X, y)` using `np.linalg.qr`.

<details markdown="1"><summary>Walkthrough</summary>

```python
import numpy as np

def back_substitute(R, c):
    k = len(c)
    b = np.zeros(k)
    for i in range(k - 1, -1, -1):              # last row first
        b[i] = (c[i] - R[i, i+1:] @ b[i+1:]) / R[i, i]
    return b

def ols_qr_by_hand(X, y):
    Q, R = np.linalg.qr(X)                      # reduced: Q is n×k, R is k×k
    beta = back_substitute(R, Q.T @ y)
    return beta, y - X @ beta
```

Row $i$ of $R\beta = c$ reads $R_{ii}\beta_i + \sum_{j>i} R_{ij}\beta_j = c_i$; the $\beta_j$ with $j > i$ are already known when you reach row $i$, which is the whole algorithm. Cost: $O(nk^2)$ for QR, $O(k^2)$ for the solve. On the test's ill-conditioned case ($\kappa(X) \approx 1.8\times10^7$) this matches the exact least-squares answer to about $3\times10^{-10}$, while `np.linalg.solve(X.T @ X, X.T @ y)` is off by about $4\times10^{-2}$: the $\kappa^2$ effect, measured.

</details>

### Step 3: streaming OLS {#fn-practice-stream}

Rows arrive one at a time (or in blocks) and you may not store them. Everything OLS needs is in three running sums:

$$A = \sum_i x_i x_i^\top = X^\top X \ (k\times k), \qquad b = \sum_i x_i y_i = X^\top y, \qquad S_{yy} = \sum_i y_i^2 .$$

At any time $\hat\beta = A^{-1}b$ (a solve, not an inverse). The residual sum of squares needs no residuals: $e^\top e = y^\top y - 2\hat\beta^\top X^\top y + \hat\beta^\top X^\top X\hat\beta$, and at the optimum $X^\top X\hat\beta = X^\top y$, so

$$e^\top e = S_{yy} - \hat\beta^\top b, \qquad s^2 = \frac{e^\top e}{n-k}.$$

Memory is $O(k^2)$ and each update costs $O(k^2)$, independent of $n$. Write a class `StreamingOLS(k)` with `update(X_rows, y_rows)`, `coef()` and `sigma2()`.

<details markdown="1"><summary>Walkthrough</summary>

```python
class StreamingOLS:
    def __init__(self, k):
        self.A = np.zeros((k, k)); self.b = np.zeros(k); self.yy = 0.0; self.n = 0

    def update(self, X, y):                      # one row or a block of rows
        X = np.atleast_2d(X); y = np.atleast_1d(y)
        self.A += X.T @ X
        self.b += X.T @ y
        self.yy += y @ y
        self.n += len(y)

    def coef(self):
        return np.linalg.solve(self.A, self.b)

    def sigma2(self):
        beta = self.coef()
        return (self.yy - beta @ self.b) / (self.n - len(beta))
```

The trade-off to say out loud: this *is* the normal equations, so it squares the condition number. Remedies, in order of effort: centre and scale the regressors (running means with Welford's update), or keep a QR or Cholesky factor and update it with Givens rotations instead of accumulating $X^\top X$.

</details>

### Step 4: recursive least squares (the version for rolling betas) {#fn-practice-rls}

Sometimes you want $\hat\beta$ after every row without a $k\times k$ solve each time, or you want old data to fade (time-varying betas). Keep $P = A^{-1}$ and update it with the Sherman–Morrison identity:

$$(A + xx^\top)^{-1} = P - \frac{P x x^\top P}{1 + x^\top P x}.$$

With the gain $g = Px/(1 + x^\top P x)$ this is $P \leftarrow P - g\,(Px)^\top$. For the coefficients, $\beta_{\text{new}} = P_{\text{new}}(b + xy)$. Two facts do the work: $P_{\text{new}}\,b = \beta - g\,x^\top\beta$, and $P_{\text{new}}\,x = g$. Together:

$$\beta \leftarrow \beta + g\,(y - x^\top\beta),$$

a correction proportional to the prediction error. With a forgetting factor $\lambda < 1$ (so $A_t = \lambda A_{t-1} + xx^\top$), the gain becomes $g = Px/(\lambda + x^\top Px)$ and $P \leftarrow (P - g(Px)^\top)/\lambda$: old rows are down-weighted geometrically, an exponentially weighted rolling beta. Start from $P = \delta I$ with $\delta$ large, which is a weak prior centred on zero.

<details markdown="1"><summary>Walkthrough</summary>

```python
class RLS:
    def __init__(self, k, lam=1.0, delta=1e6):
        self.P = delta * np.eye(k); self.beta = np.zeros(k); self.lam = lam

    def update(self, x, y):
        Px = self.P @ x
        g = Px / (self.lam + x @ Px)
        self.beta = self.beta + g * (y - x @ self.beta)
        self.P = (self.P - np.outer(g, Px)) / self.lam
```

With $\lambda = 1$ and $n = 500$, $k = 4$, this agrees with batch OLS to about $5\times10^{-9}$ (the residual difference comes from the $\delta I$ prior). Interview follow-ups: why is each update $O(k^2)$? (Matrix–vector products only.) What does $\lambda = 0.99$ mean? (An effective window of about $1/(1-\lambda) = 100$ observations.)

</details>

## Custom estimators (no library version) {#stats-missing}

The SPEC's inference also needs estimators that no standard library provides. The coding assistant writes them in `tfs_stats/` with tests against simulations whose answer is known, and each gets a card here when it lands.

| Estimator | Used in | When |
|---|---|---|
| EWC standard errors (Lazarus, Lewis, Stock & Watson 2018) | C and E, reported next to NW | Done 28 Sep: `ewc` ([card](#fn-ewc)) |
| Fama–MacBeth on monthly sufficient statistics | C (half a million pairs a month) | Done 28 Sep: `fm_from_moments` ([card](#fn-fm_moments)) |
| Dyadic-robust standard errors | C, robustness 2 | After Fall Break (PLAN) |
| MRQAP permutation test | C, robustness 1 | After Fall Break (PLAN) |
| Text-target shrinkage, variance-difference test | D | With D, if it stays in |

### fm_inference(lambdas, nw_lags) and fm_from_moments(XtX, Xty, n, nw_lags) {#fn-fm_moments}

**Job in the project.** The two halves of `fama_macbeth`, split so C can run at scale. `fm_inference` is the second FM step on its own: given a T×p series of per-period slopes, return the mean, its Newey–West standard error with the $T/(T-1)$ factor, and the t-statistic. `fm_from_moments` produces those slopes from per-month sufficient statistics $X_t^\top X_t$ and $X_t^\top y_t$, so the 499,500-pair months never have to be stacked (about 10 GB).

**The math.** Each month's OLS slope depends on the data only through $X_t^\top X_t$ and $X_t^\top y_t$: $\hat\lambda_t = (X_t^\top X_t)^{-1}X_t^\top y_t$. Accumulate those two small matrices (p×p and p) month by month, even chunk by chunk within a month, and solve at the end. The inference step is unchanged: it only sees the slope series.

**How the project computes it.** `scipy.linalg.cho_factor` / `cho_solve` on each month's $X^\top X$ (symmetric positive definite), skipping months with fewer rows than columns or a condition number above $10^{10}$; the condition numbers are returned so they can be checked. Then `fm_inference`, which is `vcov(ones, λ − λ̄, 'NW', L)` × $T/(T-1)$ per column (statsmodels HAC on a constant).

**The trade-off to be able to explain.** This is the normal-equations route that `ols_qr` avoids: $\operatorname{cond}(X^\top X) = \operatorname{cond}(X)^2$. It is acceptable here because C's regressors are standardised within month (similarity z-scores, ranks in [0, 1], 0/1 dummies), so $\operatorname{cond}(X)$ is small; where a month fits in memory, the QR path (`fama_macbeth`) is used instead, and the test checks that both give the same slopes to 1e-10.

**What the test checks.** Moments path = stacked `fama_macbeth` (slopes to 1e-10, standard errors to 1e-10 relative), and `fama_macbeth` = linearmodels `FamaMacBeth(cov_type='kernel', kernel='bartlett', bandwidth=L)` at L = 0 and 3. linearmodels applies the same $T/(T-1)$ factor at every bandwidth, which is independent confirmation of the convention.

### ewc(u, nu) {#fn-ewc}

**Job in the project.** The honest standard error next to Newey–West for C's and E's slope series (SPEC §7, §9; PREREG). Short-lag NW over-rejects when the series is persistent; EWC keeps the size close to nominal by using a fixed number of low-frequency cosine projections and Student-t critical values (Lazarus, Lewis, Stock & Watson 2018).

**The math.** Project the demeaned series on the first $\nu$ cosines: $\Lambda_j = \sqrt{2/T}\sum_{t=1}^{T}\cos\big(\pi j (t-\tfrac12)/T\big)(u_t-\bar u)$, $j = 1..\nu$. For a stationary series each $\Lambda_j$ is approximately $N(0, \Omega)$, independent across $j$, where $\Omega$ is the long-run variance (the spectral density at frequency zero, times $2\pi$). So $\hat\Omega = \frac1\nu\sum_j\Lambda_j^2$ is approximately $\Omega\,\chi^2_\nu/\nu$, and $t = \bar u/\sqrt{\hat\Omega/T}$ is approximately Student $t_\nu$. That exact small-sample distribution is the point: NW's variance estimate is noisy too, but it is compared with normal critical values as if it were not.

**Choice of $\nu$.** $\nu = \lfloor 0.4\,T^{2/3}\rfloor$: 12 at T = 165 (C), 8 at T = 91 (E's test period). Larger $\nu$ means lower variance of $\hat\Omega$ but more bias from higher frequencies.

**How the project computes it.** Custom (no library has it): a ν×T cosine weight matrix times the demeaned series, in numpy; p-values from `scipy.stats.t`.

**What the test checks.** On iid data with variance 4 (T = 165, 2,000 draws), the average $\hat\Omega$ is within 3% of 4. On AR(1) data with $\phi = 0.5$, T = 165, the 95% interval covers the true mean 94.7% of the time (4,000 draws), against 89.2% for NW(4) with normal critical values.

**Check yourself.** Why are the cosine projections approximately independent? Why does using $t_\nu$ instead of $N(0,1)$ fix most of the over-rejection? What happens to EWC if you set $\nu = T-1$?

**Read.** Lazarus, Lewis, Stock & Watson (2018), JBES, "HAR Inference: Recommendations for Practice" (sections 2–3 and the recommendations). Müller (2007) for the fixed-b idea behind it.

## Reading list {#stats-reading}

Read the papers and book chapters alongside the cards. The reference implementations are what `tfs_stats/` calls; read them when you want to see a convention in code.

| Topic | Source | Link |
|---|---|---|
| Least squares, QR, back-substitution | Trefethen & Bau, *Numerical Linear Algebra* (SIAM 1997), Lectures 7, 11, 17–19 | [doi:10.1137/1.9780898719574](https://doi.org/10.1137/1.9780898719574) |
| Least squares and robust errors, textbook | Hansen, *Econometrics* (Princeton 2022), ch. 3–4 (§4.13–4.23 on covariance and clustering), §14.34–14.35 on HAC | [Princeton UP](https://press.princeton.edu/books/hardcover/9780691235899/econometrics) |
| Heteroskedasticity-robust errors | White (1980), *Econometrica* 48(4):817–838 | [doi:10.2307/1912934](https://doi.org/10.2307/1912934) |
| HC0–HC3 finite-sample versions | MacKinnon & White (1985), *J. Econometrics* 29(3):305–325 | [doi:10.1016/0304-4076(85)90158-7](https://doi.org/10.1016/0304-4076(85)90158-7) |
| Newey–West | Newey & West (1987), *Econometrica* 55(3):703–708 | [doi:10.2307/1913610](https://doi.org/10.2307/1913610) |
| NW lag selection | Newey & West (1994), *Rev. Econ. Studies* 61(4):631–653 | [doi:10.2307/2297912](https://doi.org/10.2307/2297912) |
| Clustering, practical guide | Cameron & Miller (2015), *J. Human Resources* 50(2):317–372 | [free PDF](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015_February.pdf) |
| Standard errors in finance panels | Petersen (2009), *RFS* 22(1):435–480 | [doi:10.1093/rfs/hhn053](https://doi.org/10.1093/rfs/hhn053) |
| Reference data to test your SEs | Petersen's test data and reference standard errors | [Kellogg page](https://www.kellogg.northwestern.edu/faculty/petersen/htm/papers/se/test_data.htm) |
| Fama–MacBeth, original | Fama & MacBeth (1973), *JPE* 81(3):607–636 | [doi:10.1086/260061](https://doi.org/10.1086/260061) |
| Fama–MacBeth, textbook | Cochrane, *Asset Pricing* (rev. ed. 2005), ch. 12, §12.3 | [Princeton UP](https://press.princeton.edu/books/hardcover/9780691121376/asset-pricing) |
| EWC and why short NW lags over-reject | Lazarus, Lewis, Stock & Watson (2018), *JBES* 36(4):541–559 | [doi:10.1080/07350015.2018.1506926](https://doi.org/10.1080/07350015.2018.1506926) |
| Marčenko–Pastur, original | Marčenko & Pastur (1967), *Math. USSR-Sbornik* 1(4):457–483 | [doi:10.1070/SM1967v001n04ABEH001994](https://doi.org/10.1070/SM1967v001n04ABEH001994) |
| RMT in finance, the first paper | Laloux, Cizeau, Bouchaud & Potters (1999), *PRL* 83(7):1467 | [arXiv:cond-mat/9810255](https://arxiv.org/abs/cond-mat/9810255) |
| Clipping | Laloux, Cizeau, Potters & Bouchaud (2000), *IJTAF* 3(3):391–397 | [doi:10.1142/S0219024900000255](https://doi.org/10.1142/S0219024900000255) |
| IPR, deviating eigenvectors | Plerou et al. (2002), *Phys. Rev. E* 65:066126 | [arXiv:cond-mat/0108023](https://arxiv.org/abs/cond-mat/0108023) |
| RMT review for finance | Bouchaud & Potters (2009), "Financial applications of random matrix theory: a short review" | [arXiv:0910.1205](https://arxiv.org/abs/0910.1205) |
| Cleaning correlation matrices | Bun, Bouchaud & Potters (2017), *Physics Reports* 666:1–109 | [arXiv:1610.08104](https://arxiv.org/abs/1610.08104) |
| RMT textbook | Potters & Bouchaud (2020), *A First Course in Random Matrix Theory*, ch. 4 (Marčenko–Pastur), ch. 20 (finance) | [doi:10.1017/9781108768900](https://doi.org/10.1017/9781108768900) |
| Ledoit–Wolf identity target | Ledoit & Wolf (2004), *J. Multivariate Analysis* 88(2):365–411 | [free PDF](https://www.econ.uzh.ch/dam/jcr:ffffffff-935a-b0d6-ffff-ffffceb83f14/wellCond.pdf) |
| Shrinkage intuition | Ledoit & Wolf (2004), "Honey, I Shrunk the Sample Covariance Matrix", *JPM* 30(4):110–119 | [free PDF](https://www.econ.uzh.ch/dam/jcr:8a18d37f-3238-4c14-a276-66392e82961b/jpm_2004..pdf) |
| GMV evaluation protocol | Engle, Ledoit & Wolf (2019), *JBES* 37(2):363–375 | [doi:10.1080/07350015.2017.1345683](https://doi.org/10.1080/07350015.2017.1345683) |
| Why constraints help | Jagannathan & Ma (2003), *J. Finance* 58(4):1651–1683 | [doi:10.1111/1540-6261.00580](https://doi.org/10.1111/1540-6261.00580) |
| Mean–variance, original | Markowitz (1952), *J. Finance* 7(1):77–91 | [doi:10.1111/j.1540-6261.1952.tb01525.x](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x) |

Reference implementations (what `tfs_stats/` calls):

| Function | Where to compare | Link |
|---|---|---|
| `ols_qr` | numpy `qr` docs; statsmodels `linear_model.py` (`OLS.fit(method="qr")`) | [numpy](https://numpy.org/doc/stable/reference/generated/numpy.linalg.qr.html) · [statsmodels](https://github.com/statsmodels/statsmodels/blob/main/statsmodels/regression/linear_model.py) |
| back-substitution | SciPy's `solve_triangular` documents what yours does | [scipy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_triangular.html) |
| `vcov` | statsmodels `sandwich_covariance.py`; `get_robustcov_results` docs | [source](https://github.com/statsmodels/statsmodels/blob/main/statsmodels/stats/sandwich_covariance.py) · [docs](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html) |
| `fama_macbeth` | linearmodels `FamaMacBeth` | [docs](https://bashtage.github.io/linearmodels/panel/panel/linearmodels.panel.model.FamaMacBeth.html) |
| `clip_correlation`, `ipr` | numpy `eigh` docs | [numpy](https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigh.html) |
| `min_var_weights` | numpy `solve` docs | [numpy](https://numpy.org/doc/stable/reference/generated/numpy.linalg.solve.html) |
| `ledoit_wolf` | scikit-learn `LedoitWolf` docs; `ledoit_wolf_shrinkage` in `_shrunk_covariance.py` | [docs](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html) · [source](https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/covariance/_shrunk_covariance.py) |
