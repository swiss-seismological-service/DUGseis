import numpy as np
import obspy
from scipy import signal

from obspy.core.event import WaveformStreamID, Pick
from obspy.signal.invsim import cosine_taper
from obspy.signal.filter import bandpass


def filter(tr, freqmin, cnr, perc_taper):
    """Filter data for each band."""
    n_bands = N_bands(tr, freqmin)
    LEN = tr.stats.npts
    df = tr.stats.sampling_rate

    # create zeros 2D array for BF
    BF = np.zeros(shape=(n_bands, LEN))
    fcenter = np.zeros(n_bands)

    for j in range(n_bands):
        octave_high = (freqmin + freqmin * 2.0) / 2.0 * (2**j)
        octave_low = octave_high / 2.0
        fcenter[j] = (octave_low + octave_high) / 2.0
        BF[j] = bandpass(
            tr.data,
            octave_low,
            octave_high,
            df,
            corners=cnr,
            zerophase=False,
        )
        BF[j] = cosine_taper(LEN, perc_taper) * BF[j]

    return BF, fcenter


def inc_zeros(small_v, n, i):
    if len(small_v) > n:
        big_v = small_v
    else:
        b = len(small_v)
        if i < 1:
            big_v = np.concatenate((small_v, np.zeros(n - (b + i))), axis=0)
        else:
            big_v = np.concatenate(
                (np.zeros(i - 1), small_v, np.zeros(n - (b + i) + 1)), axis=0
            )
    return big_v


def N_bands(tr, freqmin):
    """
    Determine number of band n_bands in term of sampling rate.
    Args:
        freqmin: The center frequency of first octave filtering band.
    """
    df = tr.stats.sampling_rate
    Nyquist = df / 2.0
    n_bands = int(np.log2(Nyquist / 1.5 / freqmin)) + 1
    return n_bands


def KurtoFreq(tr, freqmin, t_long, cnr, perc_taper):
    """
    Calculate statistics for each band.
    """
    n_bands = N_bands(tr, freqmin)
    dt = tr.stats.delta
    npts_t_long = int(t_long / dt) + 1

    # BF: band filtered data
    BF, fcenter = filter(tr, freqmin, cnr, perc_taper)

    # FC = KurtoF(BF, t_long, delta, LEN, sampling_rate, n_bands)
    FC = KurtoF(BF, npts_t_long, n_bands)

    return FC, BF, n_bands, fcenter


def KurtoF(data, window_sample, n_bands):
    kt = []
    Nwin = window_sample
    if window_sample == 1:  # Function doesn't work with window sample<2
        print("window sample=1 doesn't work. Put to 2")
        window_sample = 2.0
    for j in range(n_bands):
        # Change length of trace
        v = data[j]
        idx = np.array(np.nonzero(np.isnan(v) == 0))
        a = idx[0, 0]  # first element != NaN
        b = idx[0, -1]  # last element != NaN
        inp = v[a : b + 1]
        # Compute Kurtosis
        average = signal.lfilter(np.ones([Nwin]) / Nwin, 1, inp)
        m_2 = signal.lfilter(np.ones([Nwin]) / Nwin, 1, ((inp - average) ** 2))
        m_4 = signal.lfilter(np.ones([Nwin]) / Nwin, 1, ((inp - average) ** 4))
        out = m_4 / (m_2**2)
        out = inc_zeros(out[Nwin - 1 :], len(inp), Nwin + (a + 1) - 1)
        kt.append(out)

    return kt


def rolling_window(a, window):
    """
    Efficient rolling statistics with NumPy: This is applied to
    Picker._statistics() to calculate statistics and
    Summary.threshold() to calcuate threshold to trigger event
    Reference from:
    http://www.rigtorp.se/2011/01/01/rolling-statistics-numpy.html
    """
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)

    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


def threshold(tr, HOS, t_ma, nsigma):
    """
    Control the threshold level with nsigma.
    """
    dt = tr.stats.delta
    npts_Tma = int(round(t_ma / dt, 0))
    LEN = tr.stats.npts
    # print "npts_Tma: ",npts_Tma
    threshold = np.zeros(LEN)
    # threshold[0:npts_Tma] = 1
    # threshold[npts_Tma:LEN] = (
    #     rms(rolling_window(HOS[0 : LEN - 1], npts_Tma), -1)
    #     * nsigma
    # )
    threshold[npts_Tma:LEN] = (
        np.mean(rolling_window(HOS[0 : LEN - 1], npts_Tma), -1) * nsigma
    )

    return threshold


def virginie_picker(
    st: obspy.Stream,
    number_of_parallel_jobs: int,
    t_win: float,
    freqmin: float,
    cnr: float,
    perc_taper: float,
    nsigma: float,
    t_ma: float,
    t_Tr: float,
    ncum0: float,
    ncum1: float,
):
    """
    Main entry point for the picker.
    Should likely be renamed.
    Will run in parallel using joblib.
    Args:
        st: The waveforms to pick on.
        number_of_parallel_jobs: Parallelize the picker.
        t_win: ...
        freqmin: ...
        cnr: ...
        perc_taper: ...
        nsigma: ...
        t_ma: ...
        t_Tr: ...
        ncum0: ...
        ncum1: ...
    """
    args = (t_win, freqmin, cnr, perc_taper, nsigma, t_ma, t_Tr, ncum0, ncum1)
    if number_of_parallel_jobs > 1:
        # The first execution will be fairly slow as the pool of workers has to be
        # created. It should (if not: there are other strategies) cache that worker
        # pool and reuse it upon subsequent calls.
        # Thus all calls after the first should scale decently with the number of
        # workers.
        # Import here to not depend on joblib.
        from joblib import Parallel, delayed  # NOQA

        results = Parallel(n_jobs=number_of_parallel_jobs)(
            delayed(virginie_picker_per_trace)(tr, *args) for tr in st
        )
    elif number_of_parallel_jobs == 1:
        # Fall back to a list-comprehension for serial execution - this makes
        # debugging the algorithm simpler as it does not run through joblib in
        # that case.
        results = [virginie_picker_per_trace(tr, *args) for tr in st]
    else:
        raise ValueError("Invalid number of parallel jobs.")

    # Get rid of all results that returned None.
    return [r for r in results if r is not None]


def virginie_picker_per_trace(
    tr: obspy.Trace,
    t_win: float,
    freqmin: float,
    cnr: float,
    perc_taper: float,
    nsigma: float,
    t_ma: float,
    t_Tr: float,
    ncum0: float,
    ncum1: float,
):

    time1 = []
    fTimePick = 0
    SNR = 0

    # Characteristic function
    HOS, _, _, _ = KurtoFreq(tr, freqmin, t_win, cnr, perc_taper)

    # Summary characteristic function
    HOS_max = np.amax(HOS, axis=0)

    dt = tr.stats.delta
    LEN = tr.stats.npts
    threshold_HOS_max = threshold(tr, HOS_max, t_ma, nsigma)

    cHOS = np.cumsum(HOS_max)
    cHOS_detrend = signal.detrend(cHOS)

    # trigger the earthquakes
    t_Tr = 0.01
    nptsTr = int(round(t_Tr / dt, 0))
    trigger_ptnl_index = np.where(
        (HOS_max[nptsTr:LEN] > threshold_HOS_max[nptsTr:LEN])
        & (cHOS_detrend[nptsTr:LEN] < 0)
    )
    trigger_ptnl_index = trigger_ptnl_index + np.array(nptsTr)

    time_array = np.arange(tr.stats.npts) / tr.stats.sampling_rate

    if len(trigger_ptnl_index[0]) > 0:
        time1.append(time_array[trigger_ptnl_index[0]])
        if trigger_ptnl_index[0][0] > ncum0:
            # time_array_Pick = time_array[
            #     trigger_ptnl_index[0][0]
            #     - ncum0 : trigger_ptnl_index[0][0]
            #     + ncum1
            # ]
            HOSPick = HOS_max[
                trigger_ptnl_index[0][0] - ncum0 : trigger_ptnl_index[0][0] + ncum1
            ]  # portion of HOS to compute pick
            # cte = trigger_ptnl_index[0][0] - ncum0
        else:
            # time_array_Pick = time_array[
            #     trigger_ptnl_index[0][0] : trigger_ptnl_index[0][0] + ncum1
            # ]
            HOSPick = HOS_max[
                trigger_ptnl_index[0][0] : trigger_ptnl_index[0][0] + ncum1
            ]  # portion of HOS to compute pick
            # cte = trigger_ptnl_index[0][0]

        cHOSPick = np.cumsum(HOSPick)
        cHOSPick_detrend = signal.detrend(cHOSPick)
        fPick = np.argmin(cHOSPick_detrend) + trigger_ptnl_index[0][0] - ncum0
        fTimePick = time_array[fPick]

    if fTimePick != 0:
        Noise0 = tr.stats.starttime + fTimePick - 0.01
        Noise1 = tr.stats.starttime + fTimePick - 0.0005
        Signal0 = tr.stats.starttime + fTimePick - 0.0004
        Signal1 = tr.stats.starttime + fTimePick + 0.01
        trNoise = tr.slice(starttime=Noise0, endtime=Noise1)
        trSignal = tr.slice(starttime=Signal0, endtime=Signal1)

        SNR = np.mean(abs(trSignal.data)) / np.mean(abs(trNoise.data))

        if SNR >= 1.3:
            t_pick_UTC = tr.stats.starttime + fTimePick
            return Pick(
                time=t_pick_UTC,
                waveform_id=WaveformStreamID(
                    network_code=tr.stats.network,
                    station_code=tr.stats.station,
                    location_code=tr.stats.location,
                    channel_code=tr.stats.channel,
                ),
                method_id="FBKT",
                phase_hint="P",
                evaluation_mode="automatic",
            )
