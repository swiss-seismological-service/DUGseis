from aurem.aurem import REC, AIC
from obspy import read, UTCDateTime


def test_aurem_rec():
    """Test REC function aganist obspy.read() Z channel"""
    errors = []
    st = read()

    # Process
    st.filter("highpass", freq=2, corners=4)
    st.trim(st[0].stats.starttime + 1, UTCDateTime("2009-08-24T00:20:11"))

    # Create instance + pick
    recobj = REC(st, channel="*Z")
    recobj.work()

    # Extract
    pt = recobj.get_pick()
    idx = recobj.get_pick_index()
    recobj.plot()

    # --- Test
    if not isinstance(pt, UTCDateTime):
        errors.append("Wrong out picktime object")
    if pt != UTCDateTime("2009-08-24T00:20:07.700000"):
        errors.append("PickTime do not match!")
    if idx != 370:
        errors.append("PickTime IDX do not match@")
    #
    assert not errors, "Errors occured:\n{}".format("\n".join(errors))


def test_aurem_aic():
    """Test REC function aganist obspy.read() Z channel"""
    errors = []
    st = read()

    # Process
    st.filter("highpass", freq=2, corners=4)
    st.trim(st[0].stats.starttime + 1, UTCDateTime("2009-08-24T00:20:11"))

    # Create Instance + picks
    aicobj = AIC(st, channel="*Z")
    aicobj.work()

    # Extract
    pt = aicobj.get_pick()
    idx = aicobj.get_pick_index()
    aicobj.plot()

    # --- Test
    if not isinstance(pt, UTCDateTime):
        errors.append("Wrong out picktime object")
    if pt != UTCDateTime("2009-08-24T00:20:07.700000"):
        errors.append("PickTime do not match!")
    if idx != 370:
        errors.append("PickTime IDX do not match@")
    #
    assert not errors, "Errors occured:\n{}".format("\n".join(errors))
