"""D12 daily Amihud path on synthetic fixtures (no WRDS data): price/volume conversion and the ILLIQ arithmetic."""
import gzip, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import convert_wrds, formation

def test_convert_pv(tmp_path):
    csv = ('PERMNO,HdrCUSIP,Ticker,PERMCO,DlyCalDt,DlyPrc,DlyVol\n'
           '10001,X,AAA,1,2015-01-02,-10.5,1000\n'        # negative price = bid/ask midpoint -> |p|
           '10001,X,AAA,1,2015-01-05,11,0\n'
           '10002,Y,BBB,2,2015-01-02,,500\n'               # missing price stays NaN
           '10002,Y,BBB,2,2015-01-02,20,500\n')            # duplicate key dropped
    src = tmp_path / 'crsp_dsf_pv_2015_2015.csv.gz'
    with gzip.open(src, 'wt') as fh: fh.write(csv)
    ret = tmp_path / 'crsp_dsf_2015_2015.parquet'
    pd.DataFrame({'permno': np.int32([10001, 10001, 10002]), 'date': pd.to_datetime(['2015-01-02', '2015-01-05', '2015-01-06'])}).to_parquet(ret)
    d = convert_wrds.convert_pv(str(src), str(tmp_path / 'out.parquet'), str(ret))
    assert list(d.columns) == ['permno', 'date', 'prc', 'vol']
    assert d.permno.dtype == np.int32 and d.prc.dtype == np.float32 and d.vol.dtype == np.float32
    assert len(d) == 3 and d.prc.iloc[0] == 10.5
    assert d[(d.permno == 10002)].prc.isna().all()

def test_amihud_arithmetic():
    R = np.array([[0.02, -0.01], [-0.04, np.nan], [0.01, 0.03], [0.00, 0.02]])
    P = np.array([[10., 5.], [10., 5.], [-1, 5.], [20., 5.]])      # a non-positive price is not a valid day
    V = np.array([[100., 0.], [200., 10.], [50., 10.], [10., 20.]])  # zero volume skipped
    got = formation.amihud_from_arrays(R, P, V, min_obs=2)
    want0 = np.mean([0.02 / 1000, 0.04 / 2000, 0.0 / 200])           # days 1, 2, 4 valid for stock 0
    want1 = np.mean([0.03 / 50, 0.02 / 100])                         # days 3, 4 valid for stock 1 (day 2 has no return)
    assert np.allclose(got, [want0, want1])
    assert np.isnan(formation.amihud_from_arrays(R, P, V, min_obs=3)[1])
