# DUGSeis
# Copyright (C) 2021 DUGSeis Authors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Script that contains various plotting functions.
"""
import numpy as np
import matplotlib.pyplot as plt
from obspy.signal.trigger import recursive_sta_lta


def nextpow2(N):
    """ Function for finding the next power of 2 """
    n = 1
    while n < N: n *= 2
    return n


def cm_to_inch(value):
    return value/2.54


def amp_fft(signal, sampling_rate, pad=1, window=False, resample_log=False):
    """ Function to get single sided fft"""
    signal = signal - np.mean(signal)  # detrend
    hann = np.hanning(len(signal))
    total_length_signal = nextpow2(len(signal) * pad)

    if window is True:
        signal_fft = np.fft.fft(signal * hann, n=total_length_signal)
    elif window is False:
        signal_fft = np.fft.fft(signal, n=total_length_signal)

    signal_fft = signal_fft[0:int(total_length_signal / 2 + 1)]
    signal_fft = signal_fft / len(signal)  # normalise
    signal_fft[1:-1] = signal_fft[1:-1] * 2  # single sided, that is why times two
    freq = np.arange(0, sampling_rate / 2 + sampling_rate / total_length_signal, sampling_rate / total_length_signal)
    res = freq[1:2][0]

    if resample_log:
        freq_int = np.logspace(0.1, 5, num=10000)
        signal_fft_interp = np.interp(freq_int, freq, signal_fft, left=None, right=None, period=None)
        return signal_fft_interp, freq_int, res
    else:
        return signal_fft, freq, res


def get_time_vector(stream):
    time = np.arange(0, stream[0].data.shape[0], 1) * stream[0].stats.delta * 1000

    if len(time) != stream.traces[0].stats.npts:
        if stream.traces[0].stats.npts > len(time):  # append to samp_v if too short
            time = np.append(
                time, time[len(time) - 1] + (time[len(time) - 1] - time[len(time) - 2])
            )
        else:
            time = time[:-1].copy()  # take one entry off
    return time


def ax_plot_x_y_data(ax, x_data, y_data, unit_pa="c", format_pa=".1f", markers="no"):
    if markers == "yes":
        ax.plot(x_data, y_data, linewidth=0.75, zorder=8, marker=".")
    else:
        ax.plot(x_data, y_data, linewidth=0.75, zorder=8)

    ax.set_xlim([np.min(x_data), np.max(x_data)])
    # p = np.percentile(y_data, 95)
    amp_max = format(np.nanmax(np.absolute(y_data)), format_pa)  # .1f
    props = dict(boxstyle="round", facecolor="white", alpha=0.8, edgecolor="none")
    plt.text(
        1,
        0.5,
        "PA: " + str(amp_max) + " " + unit_pa,
        horizontalalignment="right",
        verticalalignment="center",
        transform=ax.transAxes,
        color="black",
        fontsize=10,
        bbox=props,
        zorder=10,
    )
    # basic plotting options
    ax.grid(
        which="major", axis="x", color="silver", linestyle="-", linewidth=0.25
    )
    ax.set_axisbelow(True)
    ax.axhline(color="black", linewidth=0.4, zorder=5)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.tick_params(top=False)
    ax.tick_params(right=False)
    # y-axis
    ax.set_yticklabels([])
    ax.set_yticks([])
    # get y axis centered at origin
    ylim = ax.get_ylim()
    ind_ylim_max = np.argmax(np.abs(ylim))
    ax.set_ylim(bottom=-np.abs(ylim[ind_ylim_max]), top=np.abs(ylim[ind_ylim_max]))


def plot_time_waveform(stream, markers="no"):
    # chose plotting style
    plt.style.use("seaborn-bright")
    # get time vector
    time = get_time_vector(stream)
    # generate figure with subplots
    fig = plt.figure(constrained_layout=False)
    gspec = fig.add_gridspec(
        nrows=len(stream), ncols=1, left=0.08, right=0.95, wspace=0, hspace=0
    )
    col = 0
    # stream.detrend("linear")
    # stream.taper(max_percentage=0.05, type="hann")
    # stream.filter("bandpass", freqmin=50, freqmax=10000)
    for index, trace in enumerate(stream.traces):
        ax = fig.add_subplot(gspec[index, col])
        data = trace.data
        # data = data - np.mean(data)
        ax_plot_x_y_data(ax, time, data, markers=markers)

        # Percentiles
        # p = np.percentile(data, 95)
        # ax.axhline(y=p, color='black', linestyle='-', zorder=9)
        # ax.axhline(y=-p, color='black', linestyle='-', zorder=9)
        # plot specific settings
        # y-axis
        plot_y_labels(trace, ax)

        if index < gspec.nrows - 1:
            ax.set_xticklabels([])
            # ax.set_xticks([])
            ax.spines["bottom"].set_visible(False)
        else:
            ax.set_xlabel("time [ms]")
    # plt.suptitle('time-waveform \nstarttime: ' + str(stream[0].stats.starttime), fontsize=10)
    plt.suptitle(
        "time-waveform \nstarttime: " + str(stream[0].stats.starttime), fontsize=10
    )
    return fig

def plot_time_waveform_picks(stream, picks):
    fig = plot_time_waveform(stream)
    for index_pick, pick in enumerate(picks):
        pick_id = picks[index_pick].waveform_id.id
        for index_trace, trace in enumerate(stream):
            if pick_id == stream.traces[index_trace].id:
                time = (pick.time - trace.stats.starttime) * 1000  # relative pick time in ms
                fig.axes[index_trace].vlines(
                    time, fig.axes[index_trace].get_ylim()[0] * 0.5,
                    fig.axes[index_trace].get_ylim()[1] * 0.5,
                    color="r", linewidth=4)
            else:
                continue
    fig.set_size_inches(11.69, 8.27)
    return fig


def plot_time_characteristic_function(stream, nsta, nlta):
    # chose plotting style
    plt.style.use("seaborn-bright")
    # get time vector
    time = get_time_vector(stream)
    # generate figure with subplots
    fig = plt.figure(constrained_layout=False)
    gspec = fig.add_gridspec(
        nrows=len(stream), ncols=1, left=0.08, right=0.95, wspace=0, hspace=0
    )
    col = 0
    for index, trace in enumerate(stream.traces):
        ax = fig.add_subplot(gspec[index, col])
        data_cft = recursive_sta_lta(trace.data, nsta, nlta)
        # plot data
        ax_plot_x_y_data(ax, time, data_cft, unit_pa="", format_pa=".1f", markers="no")
        # plot specific settings
        # y-axis
        plot_y_labels(trace, ax)

        if index < gspec.nrows - 1:
            ax.set_xticklabels([])
            # ax.set_xticks([])
            ax.spines["bottom"].set_visible(False)
        else:
            ax.set_xlabel("time [ms]")
    plt.suptitle(
        "time-characterisitc function (r_sta/lta: " + str(nsta) + "/" + str(nlta) + ") \nstarttime: " + str(trace.stats.starttime),
        fontsize=10,
    )
    return fig


def plot_y_labels(trace, ax):
    y_label = "{0}.{1}".format(
        trace.stats.station,
        trace.stats.location,
    )
    # y_label = "{0}.{1}\n{2}.{3}".format(
    #     trace.stats.network,
    #     trace.stats.station,
    #     trace.stats.location,
    #     trace.stats.channel,
    # )
    handle = plt.text(
        -0.08,
        0.5,
        y_label,
        transform=ax.transAxes,
        fontsize=11,
        horizontalalignment="left",
        verticalalignment="center",
    )
    return handle


def plot_waveform_characteristic_function(stream, nsta, nlta):
    # chose plotting style
    plt.style.use("seaborn-bright")
    # get time vector
    time = get_time_vector(stream)
    # generate figure with subplots
    fig = plt.figure(constrained_layout=False)
    ncols = 2
    gspec = fig.add_gridspec(
        nrows=len(stream), ncols=ncols, left=0.08, right=0.95, wspace=0.1, hspace=0
    )
    for col in range(ncols):
        for index, trace in enumerate(stream.traces):
            ax = fig.add_subplot(gspec[index, col])
            if col == 0:
                ax_plot_x_y_data(
                    ax, time, trace.data, unit_pa="c", format_pa=".1f", markers="no"
                )
                # y-axis (only in time column)
                handle = plot_y_labels(trace, ax)
                handle.set_position((-0.13, 0.5))
            else:
                data_cft = recursive_sta_lta(trace.data, nsta, nlta)
                ax_plot_x_y_data(
                    ax, time, data_cft, unit_pa="", format_pa=".1f", markers="no"
                )
            if index < gspec.nrows - 1:
                ax.set_xticklabels([])
                # ax.set_xticks([])
                ax.spines["bottom"].set_visible(False)
            else:
                ax.set_xlabel("time [ms]")
    plt.suptitle(
        "waveform-characterisitc function \nstarttime: " + str(trace.stats.starttime),
        fontsize=10,
    )
    fig.set_size_inches(11.69, 8.27)
    return fig


def plot_waveform_fft_amplitude(stream):
    # chose plotting style
    plt.style.use("seaborn-bright")
    # get time vector
    time = get_time_vector(stream)
    # generate figure with subplots
    fig = plt.figure(constrained_layout=False)
    ncols = 2
    gspec = fig.add_gridspec(
        nrows=len(stream), ncols=ncols, left=0.08, right=0.95, wspace=0.1, hspace=0
    )
    for col in range(ncols):
        for index, trace in enumerate(stream.traces):
            ax = fig.add_subplot(gspec[index, col])
            if col == 0:
                ax_plot_x_y_data(
                    ax, time, trace.data, unit_pa="c", format_pa=".1f", markers="no"
                )
                # y-axis (only in time column)
                y_label = "{0}.{1}\n{2}.{3}".format(
                    trace.stats.network,
                    trace.stats.station,
                    trace.stats.location,
                    trace.stats.channel,
                )
                ax.set_ylabel(y_label, rotation=0, fontsize=9)
                ax.yaxis.set_label_coords(-0.055, 0.27)
            else:
                # XXX: nsta and nlta are not defined so this would always fail.
                data_cft = recursive_sta_lta(trace.data, nsta, nlta)  # NOQA
                ax_plot_x_y_data(
                    ax, time, data_cft, unit_pa="", format_pa=".1f", markers="no"
                )
            if index < gspec.nrows - 1:
                ax.set_xticklabels([])
                # ax.set_xticks([])
                ax.spines["bottom"].set_visible(False)
            else:
                ax.set_xlabel("time [ms]")
    plt.suptitle(
        "waveform-characterisitc function \nstarttime: " + str(trace.stats.starttime),
        fontsize=10,
    )
    fig.set_size_inches(11.69, 8.27)
    return fig


def plot_waveform_characteristic_function_magnitude(
    stream, nsta, nlta, tr_on, tr_off, event
):
    figure = plot_waveform_characteristic_function(stream, nsta, nlta)

    # update title
    new_title = (
        figure._suptitle._text
        + "\n"
        + "$M_A$ net: {:.2f}".format(event.magnitudes[0].mag)
    )
    figure.suptitle(new_title)

    x_min, x_max = np.array(figure.axes[0].get_xlim())
    # get all waveform id's for which a pick exists

    amplitude_w_ids = []
    for index, amplitude in enumerate(event.amplitudes):
        amplitude_w_ids.append(amplitude.waveform_id.id)

    count = 0
    for index, pick in enumerate(event.picks):
        x_pick = (event.picks[index].time - stream[0].stats.starttime) * 1000

        y_max = figure.axes[index].get_ylim()[1] * 0.2

        # P-pick plotting
        figure.axes[index].scatter(
            x_pick, y_max, marker="v", color="red", zorder=10, alpha=0.5, label="P-pick"
        )

        figure.axes[index + len(event.picks)].hlines(
            tr_on,
            x_min,
            x_max,
            colors="red",
            linestyles="dashed",
            zorder=10,
            alpha=0.5,
            label="threshold on",
        )
        figure.axes[index + len(event.picks)].hlines(
            tr_off,
            x_min,
            x_max,
            colors="green",
            linestyles="dashed",
            zorder=10,
            alpha=0.5,
            label="threshold off",
        )

        # update text in first column of subplots
        if (
            pick.waveform_id.id in amplitude_w_ids
        ):  # only print mag if mag, resp. amplitude exists
            new_text = (
                "Dist.: {:.1f} m".format(event.origins[0].arrivals[index].distance)
                + "\n"
                + "SNR: {:.1f}".format(event.amplitudes[count].snr)
                + "\n"
                + "PA: {:.3f} corr".format(event.amplitudes[count].generic_amplitude)
                + "\n"
                + "$M_A$ sta.: {:.2f}".format(event.station_magnitudes[count].mag)
            )
            x_swave = (
                (
                    event.amplitudes[count].time_window.reference
                    + event.amplitudes[count].time_window.end
                )
                - stream[0].stats.starttime
            ) * 1000
            # theoretical S-wave arrival
            figure.axes[index].scatter(
                x_swave,
                y_max,
                marker="v",
                color="black",
                zorder=10,
                alpha=0.5,
                label="end P-window",
            )
            count += 1
        else:
            new_text = (
                "Dist.: {:.1f} m".format(event.origins[0].arrivals[index].distance)
                + "\n"
                + "used for location but no magnitude computed"
            )

        figure.axes[index].texts[0].set_text(new_text)

        if index == 0:
            figure.axes[index].legend(loc="lower left")
            figure.axes[index].legend(loc="lower left", ncol=2)
            figure.axes[index + len(event.picks)].legend(loc="lower left", ncol=2)
        else:
            continue

    return figure
