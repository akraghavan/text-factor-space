"""CRSP CIZ universe (SPEC §3): US-incorporated operating common stock on NYSE, NYSE American or Nasdaq.
Equivalent to legacy SHRCD in {10, 11}; IssuerType excludes REITs (legacy 18) and funds. v0 omitted IssuerType and ConditionalType."""
def common_stock(m):
    """Rows of the CRSP monthly file (lower-case CIZ columns) that are in the universe that month."""
    return m[(m.sharetype=='NS')&(m.securitytype=='EQTY')&(m.securitysubtype=='COM')&(m.usincflg=='Y')
             &m.issuertype.isin(['ACOR','CORP'])&m.conditionaltype.isin(['RW','NW'])&m.primaryexch.isin(['N','A','Q'])]

def add_exit_months(raw, members):
    """Rows of `raw` (CRSP monthly, lower-case CIZ columns, with ym) for each permno's EXIT month: the month t after a
    month t-1 in which it was in the universe (`members`, the common_stock rows) when it is not in the universe at t.
    SPEC §3 applies the universe at formation only, so the return realised in month t by a firm formed at t-1 must be
    kept even if the firm leaves the universe in t. It matters above all for delistings: in the DelistingDt month CIZ
    blanks ShareType, SecurityType and ConditionalType (SecuritySubType UNK, USIncFlg N), so the month fails the
    universe filter, and 87% of delisting-month returns (with any DelRet CRSP folded in) were being dropped before
    30 Sep 2026. Returns rows flagged in_universe = False; universe_at selects in_universe rows only."""
    import pandas as pd
    raw = raw.sort_values(['permno', 'ym']).drop_duplicates(['permno', 'ym'], keep='last')
    inu = pd.MultiIndex.from_frame(members[['permno', 'ym']])
    nxt = pd.MultiIndex.from_arrays([members.permno.to_numpy(), (members.ym + 1).to_numpy()])
    k = pd.MultiIndex.from_frame(raw[['permno', 'ym']])
    out = raw[k.isin(nxt) & ~k.isin(inu)].copy(); out['in_universe'] = False
    return out

# D8 (SPEC §3): SPACs are excluded. A 10-K is a SPAC filing if its Item 1 describes a shell: "we are / is a blank check
# company" in the first 500 words, or "initial business combination" at least 3 times in the first 2,000 words.
# Checked against the company name at the filing date (SEC formerNames; "Acquisition"/"Merger"/"SPAC" = SPAC):
# - the broader /blank check|business combination|trust account/ rule within SIC 6770/6799 has precision 0.34: de-SPACed
#   operating firms keep CRSP SIC 6799 and recount their merger in Item 1;
# - this rule within SIC 6770/6799: precision 0.80 against the name label, ~0.97 after reading the disagreements (most
#   are SPACs without "Acquisition" in the name), recall 0.98;
# - no SIC condition: 95 filings with this language have other CRSP SICs (7389 x42, 6726, 6719, ...), ~85 of them SPACs.
# A permno-month is a SPAC month if its latest 10-K filed before the month ends (<= 15 months old) is a
# SPAC filing, or, with no such 10-K, if its SIC that month is 6770. A de-SPACed firm re-enters with its first operating
# 10-K. Build with `python src/universe.py` (after P2-P4): writes data/interim/spac_filings.parquet and
# data/processed/spac_months.parquet (permno, ym).
import re as _re
SPAC_SIC = (6770, 6799)
SPAC_ANY = _re.compile(r'(?i)blank[\s-]*check|business\s+combination|trust\s+account')      # broad screen (diagnostic)
SPAC_WEARE = _re.compile(r'(?i)\b(?:we are|the company is|is) an? (?:newly organized |newly incorporated |recently incorporated )?blank[\s-]*check company')
SPAC_IBC = _re.compile(r'(?i)initial\s+business\s+combination')
def spac_text(item1):
    w = str(item1).split()
    return bool(SPAC_WEARE.search(' '.join(w[:500]))) or len(SPAC_IBC.findall(' '.join(w[:2000]))) >= 3

def spac_filings(lk, m, item1):
    """lk: tenk_linked (accession, permno, filing_date); m: crsp_monthly (permno, ym, sic); item1: accession -> text."""
    import pandas as pd
    f = lk[['accession', 'permno', 'filing_date']].copy(); f['ym'] = f.filing_date.dt.to_period('M')
    s = m[['permno', 'ym', 'sic']].dropna().copy(); s['t'] = s.ym.dt.to_timestamp(); f['t'] = f.ym.dt.to_timestamp()
    f = pd.merge_asof(f.sort_values('t'), s.sort_values('t')[['permno', 't', 'sic']], on='t', by='permno', direction='nearest')
    text = item1.reindex(f.accession.to_numpy()).fillna('').to_numpy()
    f['spac_any'] = [bool(SPAC_ANY.search(' '.join(str(t).split()[:2000]))) for t in text]
    f['spac_text'] = [spac_text(t) for t in text]
    f['sic_spac'] = f.sic.isin(SPAC_SIC)
    f['is_spac'] = f.spac_text
    return f.drop(columns='t')

def spac_months(f, m):
    """Permno-months (universe rows of m) that are SPAC months under the D8 rule."""
    import pandas as pd
    u = m[['permno', 'ym', 'sic']].copy(); u['t'] = (u.ym + 1).dt.to_timestamp()          # filings before month end
    g = f[['permno', 'filing_date', 'is_spac']].rename(columns={'filing_date': 't'}).sort_values('t')
    u = pd.merge_asof(u.sort_values('t'), g, on='t', by='permno', direction='backward', tolerance=pd.Timedelta(days=457))
    has = u.is_spac.notna()
    u['spac'] = (has & u.is_spac.fillna(False).astype(bool)) | (~has & (u.sic == 6770))
    return u.loc[u.spac, ['permno', 'ym']].reset_index(drop=True)

def exclude_spacs(df, months=None):
    """Drop SPAC permno-months from a frame with permno and ym (Period[M]) columns."""
    import pandas as pd
    if months is None:
        from paths import PROCESSED; months = pd.read_parquet(PROCESSED / 'spac_months.parquet')
    k = df.set_index(['permno', 'ym']).index.isin(months.set_index(['permno', 'ym']).index)
    return df[~k]

if __name__ == '__main__':
    import glob, pandas as pd
    from paths import INTERIM, PROCESSED
    lk = pd.read_parquet(INTERIM / 'tenk_linked.parquet', columns=['accession', 'permno', 'filing_date'])
    m = pd.read_parquet(PROCESSED / 'crsp_monthly.parquet', columns=['permno', 'ym', 'sic'])
    t = pd.concat(pd.read_parquet(p, columns=['accession', 'item1', 'n_words']) for p in glob.glob(str(INTERIM / 'item1' / 'shard_*.parquet')))
    t = t[t.n_words >= 0].drop_duplicates('accession', keep='last').set_index('accession').item1
    f = spac_filings(lk, m, t); f.to_parquet(INTERIM / 'spac_filings.parquet')
    sm = spac_months(f, m); sm.to_parquet(PROCESSED / 'spac_months.parquet')
    y = f.filing_date.dt.year
    print('SPAC filings by filing year:', f[f.is_spac].groupby(y[f.is_spac]).size().to_dict())
    print(f"SPAC filings {int(f.is_spac.sum())} (of which SIC 6770/6799 {int((f.is_spac & f.sic_spac).sum())}); SIC 6770/6799 filings {int(f.sic_spac.sum())}, "
          f"of which not SPAC {int((f.sic_spac & ~f.spac_text).sum())}; "
          f"SIC 6770 without the language {int(((f.sic == 6770) & ~f.spac_text).sum())}; shell language outside 6770/6799 {int((~f.sic_spac & f.spac_text).sum())}; "
          f"broad any-mention rule would flag {int((f.sic_spac & f.spac_any).sum())}")
    ms = sm.groupby(sm.ym.dt.year).size(); tot = m.groupby(m.ym.dt.year).size()
    print('SPAC permno-months by year (share of universe rows):', {k: f'{v} ({v / tot[k]:.1%})' for k, v in ms.items()})
