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


def fft_amp(stream):
    """
    Performs Fast Fourier Transform on traces in stream
    """
    time = get_time_vector(stream) / 1000  # in seconds
    # fig = plt.figure(constrained_layout=False)
    # gspec = fig.add_gridspec(nrows=len(stream), ncols=1, left=0.08, right=0.95, wspace=0, hspace=0)
    col = 0
    plt.figure(figsize=(11.69/2, 8.27/2))
    Y = np.empty((0, int(len(stream.traces[0]) / 2 + 1)), dtype=float)
    N = int(len(stream.traces[0]) / 2 + 1)
    dt = time[1] - time[0]
    fa = 1.0 / dt
    for index, trace in enumerate(stream.traces):
        data = np.multiply(trace.data, 10000 / 32000)
        data = data - np.mean(data)
        hann = np.hanning(len(data))

        # FFT
        Yhann = np.fft.fft(hann * data)
        Y = np.append(Y, np.array([2.0 * np.abs(Yhann[:N]) / N]), axis=0)

    X = np.linspace(0, fa / 2, N, endpoint=True)
    # y_label = '{0}.{1}.{2}.{3}'.format(trace.stats.network,
    #                                     trace.stats.station,
    #                                     trace.stats.location,
    #                                     trace.stats.channel)
    # plt.plot(X, 2.0 * np.abs(Yhann[:N]) / N, linewidth=0.75, zorder=8, label=y_label)
    # plt.yscale('log')
    # plt.grid()
    # plt.legend(loc='lower right')
    # plt.xlim([50, 50000])
    # plt.ylim([10**-8, 10**-1])
    # plt.ylabel("$log_{10}(A)$ [mV/Hz]")
    # plt.xlabel("frequency [Hz]")


    return X,Y

        # plt.subplot(122)
        # plt.plot(X, 2.0 * np.abs(Yhann[:N]) / N)
        # plt.tight_layout()
        # plt.yscale('log')
        # plt.show()
        # x = 2







    # t = np.linspace(0, 1, 10000, endpoint=True)
    # f = 20  # Frequency in Hz
    # A = 100.0  # Amplitude in Unit
    # s = A * np.sin(2 * np.pi * f * t)  # Signal

    # plot time domain
    # plt.figure(figsize=(7, 3))
    # plt.subplot(121)
    # hann = np.hanning(len(s))
    # plt.plot(t, s)
    # plt.title('Time Domain Signal')
    # plt.ylim(np.min(s) * 3, np.max(s) * 3)
    # plt.xlabel('Time ($s$)')
    # plt.ylabel('Amplitude ($Unit$)')
    #
    # # FFT
    # dt = t[1] - t[0]
    # fa = 1.0 / dt
    #
    # # s = np.pad(s, (5000, 0), mode='constant') #zero pad
    # hann = np.hanning(len(s))
    # Yhann = np.fft.fft(hann * s)
    # # Yhann = np.fft.fft(s)
    # corr = 1.63
    # Y = np.fft.fft(s)
    # N = int(len(Y) / 2 + 1)
    # X = np.linspace(0, fa / 2, N, endpoint=True)
    #
    #
    # plt.subplot(122)
    # plt.plot(X, 2.0 * np.abs(Yhann[:N]) / N)
    # plt.title('Frequency Domain Signal')
    # plt.xlabel('Frequency ($Hz$)')
    # plt.ylabel('Amplitude ($Unit$)')
    # plt.xlim(0, f*2)
    #
    # plt.annotate("FFT",
    #              xy=(0.0, 0.1), xycoords='axes fraction',
    #              xytext=(-0.8, 0.2), textcoords='axes fraction',
    #              size=30, va="center", ha="center",
    #              arrowprops=dict(arrowstyle="simple",
    #                              connectionstyle="arc3,rad=0.2"))
    # plt.tight_layout()
    # plt.show()


def get_time_vector(stream):
    time = np.arange(0, stream[0].data.shape[0], 1) * stream[0].stats.delta * 1000

    if len(time) != stream.traces[0].stats.npts:
        if stream.traces[0].stats.npts > len(time):  # append to samp_v if too short
            time = np.append(time, time[len(time) - 1] + (time[len(time) - 1] - time[len(time) - 2]))
        else:
            time = time[:-1].copy()  # take one entry off
    return time


def ax_plot_x_y_data(ax, x_data, y_data, unit_pa='c', format_pa='.3f', markers='no'):
    if markers == 'yes':
        ax.plot(x_data, y_data, linewidth=0.75, zorder=8, marker='.')
    else:
        ax.plot(x_data, y_data, linewidth=0.75, zorder=8)

    ax.set_xlim([np.min(x_data), np.max(x_data)])
    p = np.percentile(y_data, 95)
    amp_max = format(np.nanmax(np.absolute(y_data)), format_pa) # .1f
    props = dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='none')
    plt.text(1, 0.5, 'PA: ' + str(amp_max) + ' ' + unit_pa,
             horizontalalignment='right',
             verticalalignment='center',
             transform=ax.transAxes, color='black', fontsize=10, bbox=props, zorder=10)
    # basic plotting options
    ax.grid(b=None, which='major', axis='x', color='silver', linestyle='-', linewidth=0.25)
    ax.set_axisbelow(True)
    ax.axhline(color='black', linewidth=0.4, zorder=5)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.tick_params(top=False)
    ax.tick_params(right=False)
    # y-axis
    ax.set_yticklabels([])
    ax.set_yticks([])
    # get y axis centered at origin
    ylim = ax.get_ylim()
    ind_ylim_max = np.argmax(np.abs(ylim))
    ax.set_ylim(bottom=-np.abs(ylim[ind_ylim_max]), top=np.abs(ylim[ind_ylim_max]))


def plot_time_waveform(stream, markers='no'):
    # chose plotting style
    plt.style.use('seaborn-bright')
    # get time vector
    time = get_time_vector(stream)
    # generate figure with subplots
    fig = plt.figure(constrained_layout=False)
    gspec = fig.add_gridspec(nrows=len(stream), ncols=1, left=0.08, right=0.95, wspace=0, hspace=0)
    col = 0
    for index, trace in enumerate(stream.traces):
        ax = fig.add_subplot(gspec[index, col])
        # plot data * 10000 / 32000 mV
        if 'XB.01' in trace.id:
            data = np.multiply(trace.data, 50 / 2**16)
        else:
            data = np.multiply(trace.data, 10000 / 2 ** 16)
        # elif trace.id == 'XB.01.16.001' or trace.id == 'XB.01.24.001':
        #     data = np.multiply(trace.data, 100 / 2 ** 16)
        # elif trace.id == 'XB.01.17.001' or trace.id == 'XB.01.25.001':
        #     data = np.multiply(trace.data, 250 / 2 ** 16)
        # elif trace.id == 'XB.01.18.001' or trace.id == 'XB.01.26.001':
        #     data = np.multiply(trace.data, 500 / 2 ** 16)
        # elif trace.id == 'XB.01.19.001' or trace.id == 'XB.01.27.001':
        #     data = np.multiply(trace.data, 1000 / 2 ** 16)
        # elif trace.id == 'XB.01.20.001' or trace.id == 'XB.01.28.001':
        #     data = np.multiply(trace.data, 2000 / 2 ** 16)
        # elif trace.id == 'XB.01.21.001' or trace.id == 'XB.01.29.001':
        #     data = np.multiply(trace.data, 5000 / 2 ** 16)
        # else:
        #     data = np.multiply(trace.data, 10000 / 2**16)

        data = data - np.mean(data)
        ax_plot_x_y_data(ax, time, data, unit_pa='mV', markers=markers)

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
            ax.spines['bottom'].set_visible(False)
        else:
            ax.set_xlabel('time [ms]')
    # plt.suptitle('time-waveform \nstarttime: ' + str(stream[0].stats.starttime), fontsize=10)
    plt.suptitle('time-waveform \nstarttime: ' + str(stream[0].stats.starttime), fontsize=10)
    return fig


def plot_time_characteristic_function(stream, nsta, nlta):
    # chose plotting style
    plt.style.use('seaborn-bright')
    # get time vector
    time = get_time_vector(stream)
    # generate figure with subplots
    fig = plt.figure(constrained_layout=False)
    gspec = fig.add_gridspec(nrows=len(stream), ncols=1, left=0.08, right=0.95, wspace=0, hspace=0)
    col = 0
    for index, trace in enumerate(stream.traces):
        ax = fig.add_subplot(gspec[index, col])
        data_cft = recursive_sta_lta(trace.data, nsta, nlta)
        # plot data
        ax_plot_x_y_data(ax, time, data_cft, unit_pa='', format_pa='.1f', markers='no')
        # plot specific settings
        # y-axis
        plot_y_labels(trace, ax)

        if index < gspec.nrows - 1:
            ax.set_xticklabels([])
            # ax.set_xticks([])
            ax.spines['bottom'].set_visible(False)
        else:
            ax.set_xlabel('time [ms]')
    plt.suptitle('time-characterisitc function \nstarttime: ' + str(trace.stats.starttime), fontsize=10)
    return fig


def plot_y_labels(trace, ax):
    y_label = '{0}.{1}\n{2}.{3}'.format(trace.stats.network,
                                        trace.stats.station,
                                        trace.stats.location,
                                        trace.stats.channel)
    handle = plt.text(-0.08, 0.5, y_label, transform=ax.transAxes, fontsize=11,
             horizontalalignment='left', verticalalignment='center')
    return handle


def plot_waveform_characteristic_function(stream, nsta, nlta):
    # chose plotting style
    plt.style.use('seaborn-bright')
    # get time vector
    time = get_time_vector(stream)
    # generate figure with subplots
    fig = plt.figure(constrained_layout=False)
    ncols = 2
    gspec = fig.add_gridspec(nrows=len(stream), ncols=ncols, left=0.08, right=0.95, wspace=0.1, hspace=0)
    for col in range(ncols):
        for index, trace in enumerate(stream.traces):
            ax = fig.add_subplot(gspec[index, col])
            if col == 0:
                ax_plot_x_y_data(ax, time, trace.data, unit_pa='c', format_pa='.1f', markers='no')
                # y-axis (only in time column)
                handle = plot_y_labels(trace, ax)
                handle.set_position((-0.13, 0.5))
            else:
                data_cft = recursive_sta_lta(trace.data, nsta, nlta)
                ax_plot_x_y_data(ax, time, data_cft, unit_pa='', format_pa='.1f', markers='no')
            if index < gspec.nrows - 1:
                ax.set_xticklabels([])
                # ax.set_xticks([])
                ax.spines['bottom'].set_visible(False)
            else:
                ax.set_xlabel('time [ms]')
    plt.suptitle('waveform-characterisitc function \nstarttime: ' + str(trace.stats.starttime), fontsize=10)
    return fig


def plot_waveform_fft_amplitude(stream):
    # chose plotting style
    plt.style.use('seaborn-bright')
    # get time vector
    time = get_time_vector(stream)
    # generate figure with subplots
    fig = plt.figure(constrained_layout=False)
    ncols = 2
    gspec = fig.add_gridspec(nrows=len(stream), ncols=ncols, left=0.08, right=0.95, wspace=0.1, hspace=0)
    for col in range(ncols):
        for index, trace in enumerate(stream.traces):
            ax = fig.add_subplot(gspec[index, col])
            if col == 0:
                ax_plot_x_y_data(ax, time, trace.data, unit_pa='c', format_pa='.1f', markers='no')
                # y-axis (only in time column)
                y_label = '{0}.{1}\n{2}.{3}'.format(trace.stats.network,
                                                    trace.stats.station,
                                                    trace.stats.location,
                                                    trace.stats.channel)
                ax.set_ylabel(y_label, rotation=0, fontsize=9)
                ax.yaxis.set_label_coords(-0.055, 0.27)
            else:
                data_cft = recursive_sta_lta(trace.data, nsta, nlta)
                ax_plot_x_y_data(ax, time, data_cft, unit_pa='', format_pa='.1f', markers='no')
            if index < gspec.nrows - 1:
                ax.set_xticklabels([])
                # ax.set_xticks([])
                ax.spines['bottom'].set_visible(False)
            else:
                ax.set_xlabel('time [ms]')
    plt.suptitle('waveform-characterisitc function \nstarttime: ' + str(trace.stats.starttime), fontsize=10)
    return fig


def plot_waveform_characteristic_function_magnitude(stream, nsta, nlta, tr_on, tr_off, event):
    figure = plot_waveform_characteristic_function(stream, nsta, nlta)

    # update title
    new_title = figure._suptitle._text + "\n" + "$M_A$ net: {:.2f}".format(event.magnitudes[0].mag)
    figure.suptitle(new_title)

    x_min, x_max = np.array(figure.axes[0].get_xlim())
    for index, pick in enumerate(event.picks):
        x_pick = (event.picks[index].time - stream[0].stats.starttime) * 1000
        x_swave = ((event.amplitudes[index].time_window.reference +
                    event.amplitudes[index].time_window.end) - stream[0].stats.starttime) * 1000
        y_max = figure.axes[index].get_ylim()[1] * 0.2

        # P-pick plotting
        figure.axes[index].scatter(x_pick, y_max, marker='v', color='red', zorder=10,
                                   alpha=.5, label='P-pick')

        # theoretical S-wave arrival
        figure.axes[index].scatter(x_swave, y_max, marker='v', color='black', zorder=10,
                                   alpha=.5, label='end P-window')

        figure.axes[index + len(event.picks)].hlines(tr_on, x_min, x_max, colors='red', linestyles='dashed',
                                                     zorder=10, alpha=.5, label='threshold on')
        figure.axes[index + len(event.picks)].hlines(tr_off, x_min, x_max, colors='green', linestyles='dashed',
                                                     zorder=10, alpha=.5, label='threshold off')

        # update text in first column of subplots
        new_text = "Dist.: {:.1f} m".format(event.origins[0].arrivals[index].distance) + "\n" + \
                   "SNR: {:.1f}".format(event.amplitudes[index].snr) + "\n" + \
                   "PA: {:.3f} corr".format(event.amplitudes[index].generic_amplitude) + "\n" + \
                   "$M_A$ sta.: {:.2f}".format(event.station_magnitudes[index].mag)

        figure.axes[index].texts[0].set_text(new_text)

        if index == 0:
            figure.axes[index].legend(loc='lower left')
            figure.axes[index].legend(loc='lower left', ncol=2)
            figure.axes[index + len(event.picks)].legend(loc='lower left', ncol=2)
        else:
            continue

    return figure
