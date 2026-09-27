"""CRSP CIZ universe (SPEC §3): US-incorporated operating common stock on NYSE, NYSE American or Nasdaq.
Equivalent to legacy SHRCD in {10, 11}; IssuerType excludes REITs (legacy 18) and funds. v0 omitted IssuerType and ConditionalType."""
def common_stock(m):
    """Rows of the CRSP monthly file (lower-case CIZ columns) that are in the universe that month."""
    return m[(m.sharetype=='NS')&(m.securitytype=='EQTY')&(m.securitysubtype=='COM')&(m.usincflg=='Y')
             &m.issuertype.isin(['ACOR','CORP'])&m.conditionaltype.isin(['RW','NW'])&m.primaryexch.isin(['N','A','Q'])]
