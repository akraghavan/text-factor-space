"""Element D inputs (SPEC §8; PREREG Element D; D20(f)): the rebalance schedule, the universe and the windows.
  schedule(T)  rebalance days every 21 trading days from the first CRSP trading day of July 2012 to the end of the daily
               data (2026-03-31); a rebalance needs T estimation days plus the 252-day target-fit window before them
               (so with T = 504 the first rebalance comes later; reported)
  inputs(k, N, T)  for the rebalance on trading day k:
      universe   formation.universe_at(calendar month of day k) (SPAC months excluded, one security per company, a 10-K
                 vintage), restricted to firms with all T daily returns in the estimation window [k - T, k) (a complete
                 PAST window, never a complete future one), then the N largest by ME at t-1
      X          T x N raw daily returns of the estimation window (no gaps by construction)
      Xfit       252 x N raw daily returns of the target-fit window [k - T - 252, k - T) (gaps allowed; pairs need >= 200
                 common days, D20(b))
      F, Ffit    the FF5 + momentum daily factors over the two windows (for the FF6 models)
      hold       H x N raw daily returns of the holding period [k, k + 21) (the next rebalance), a missing return replaced
                 by that day's risk-free rate (a delisted or halted position earns the risk-free rate); H < 21 at the end
      G_dense    networks.dense of the N firms' vintages (centred cosine Gram, PSD, unit diagonal)
      G_bow      raw BoW cosine Gram (networks.bow_sim(..., 'raw')), diagonal set to 1
      B_ind      same-SIC-3 0/1 with ones on the diagonal (firms without a SIC code are their own block)
Raw (not excess) daily returns throughout: subtracting the common risk-free rate barely moves correlations, and the
GMV portfolio's realised return is what is evaluated. Dates before 2018-12-01 are development, the rest test (PREREG)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import formation as F, networks as N

HOLD, FIT, MIN_FIT_OBS = 21, 252, 200
FIRST, DEV_END = pd.Timestamp('2012-07-01'), pd.Timestamp('2018-12-01')

def schedule(T=252):
    dates, _, _ = F.daily_wide(); k0 = dates.searchsorted(FIRST)
    return [k for k in range(k0, len(dates), HOLD) if k - T - FIT >= 0]

def inputs(k, N_firms=500, T=252):
    dates, cols, R = F.daily_wide(); ff = F.factors_daily().reindex(dates)
    t = pd.Period(dates[k], 'M'); u = F.universe_at(t)
    pos = cols.get_indexer(pd.Index(u.permno)); u, pos = u[pos >= 0], pos[pos >= 0]
    full = np.isfinite(R[k - T:k][:, pos]).all(0); u, pos = u[full], pos[full]
    top = np.argsort(-u.me.to_numpy(), kind='stable')[:N_firms]; u, pos = u.iloc[top].reset_index(drop=True), pos[top]
    k1 = min(k + HOLD, len(dates)); rf = ff.RF.to_numpy()[k:k1]
    hold = R[k:k1][:, pos].astype(np.float64); miss = ~np.isfinite(hold); hold[miss] = np.broadcast_to(rf[:, None], hold.shape)[miss]
    acc = u.accession.to_numpy(); G_bow = N.bow_sim(pd.Timestamp(dates[k]).normalize().replace(day=1), acc, 'raw').astype(np.float64)
    np.fill_diagonal(G_bow, 1.0)
    sic3 = np.floor(u.sic.to_numpy(dtype=float) / 10); B = (sic3[:, None] == sic3[None, :]) & np.isfinite(sic3)[:, None]
    B = B.astype(np.float64); np.fill_diagonal(B, 1.0)
    return {'k': k, 'date': dates[k], 'end': dates[k1 - 1], 'firms': u[['permno', 'me', 'sic', 'accession']],
            'X': R[k - T:k][:, pos].astype(np.float64), 'Xfit': R[k - T - FIT:k - T][:, pos].astype(np.float64),
            'F': ff[F.FACTORS].to_numpy(np.float64)[k - T:k], 'Ffit': ff[F.FACTORS].to_numpy(np.float64)[k - T - FIT:k - T],
            'hold': hold, 'hold_dates': dates[k:k1], 'missing_hold': int(miss.sum()), 'rf': rf,
            'G_dense': N.dense(acc).astype(np.float64), 'G_bow': G_bow, 'B_ind': B}

def pair_corr(X, min_obs=MIN_FIT_OBS):
    """Pairwise-complete Pearson correlations of the columns of X (pandas DataFrame.corr(min_periods)), NaN where a pair
    has fewer than min_obs common days. A descriptive statistic, not an estimator."""
    if np.isfinite(X).all(): return np.corrcoef(X, rowvar=False)
    return pd.DataFrame(X).corr(min_periods=min_obs).to_numpy()
