import obspy
import pytest

from dug_seis.event_processing.picking.dug_picker import dug_picker


# The sta_lta picker changed at some point. This test will have to be adapted.
@pytest.mark.xfail
def test_dug_picker_sta_lta():
    st = obspy.read()

    picks = dug_picker(
        st=st,
        pick_algorithm="sta_lta",
        picker_opts={
            "st_window": 70,
            "lt_window": 700,
            "thresholds": [3.0]*len(st),
        },
    )

    assert len(picks) == 3
    assert [p.waveform_id.id for p in picks] == [
        "BW.RJOB..EHZ",
        "BW.RJOB..EHN",
        "BW.RJOB..EHE",
    ]

    for p in picks:
        assert p.phase_hint == "P"
        assert p.method_id == "recursive_sta_lta"
        assert p.evaluation_mode == "automatic"
        assert st[0].stats.starttime < p.time < st[0].stats.endtime


# Stop ignoring once good parameters are found.
@pytest.mark.filterwarnings("ignore:.*")
def test_dug_picker_fb():
    """
    Really just a coverage test.
    """
    st = obspy.read()

    picks = dug_picker(st=st, pick_algorithm="fb")

    # Should be changed when configured properly.
    assert len(picks) == 0


# Stop ignoring once good parameters are found.
@pytest.mark.filterwarnings("ignore:.*")
def test_dug_picker_kt():
    """
    Really just a coverage test.
    """
    st = obspy.read()

    picks = dug_picker(st=st, pick_algorithm="kt")

    # Should be changed when configured properly.
    assert len(picks) == 0


@pytest.mark.xfail
# Stop ignoring once good parameters are found.
@pytest.mark.filterwarnings("ignore:.*")
def test_dug_picker_aicd():
    """
    Really just a coverage test.

    Currently in PhasePaPy code.
    """
    st = obspy.read()

    picks = dug_picker(
        st=st,
        pick_algorithm="aicd",
        picker_opts={
            "t_ma": 3 / 1000,
            "nsigma": 8,
            "t_up": 0.78 / 1000,
            "nr_len": 2,
            "nr_coeff": 2,
            "pol_len": 10,
            "pol_coeff": 10,
            "uncert_coeff": 3,
            "bandpass_f_min": 0.1,
            "bandpass_f_max": 2.0,
        },
    )

    # Should be changed when configured properly.
    assert len(picks) == 0


@pytest.mark.filterwarnings("ignore:.*parameter will change.*")
def test_dug_picker_pphase():
    st = obspy.read()

    picks = dug_picker(st=st, pick_algorithm="pphase")

    assert len(picks) == 3

    assert [p.waveform_id.id for p in picks] == [
        "BW.RJOB..EHZ",
        "BW.RJOB..EHN",
        "BW.RJOB..EHE",
    ]

    for p in picks:
        assert p.phase_hint == "P"
        assert p.method_id == "pphase"
        assert p.evaluation_mode == "automatic"
        assert st[0].stats.starttime < p.time < st[0].stats.endtime
