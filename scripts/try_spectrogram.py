# from https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.spectrogram.html

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
#from scipy.fft import fftshift
rng = np.random.default_rng()


# Generate random signal
fs = 10e3
N = 1e5
amp = 2 * np.sqrt(2)
noise_power = 0.01 * fs / 2
time = np.arange(N) / float(fs)
mod = 500*np.cos(2*np.pi*0.25*time)
carrier = amp * np.sin(2*np.pi*3e3*time + mod)
noise = rng.normal(scale=np.sqrt(noise_power), size=time.shape)
noise *= np.exp(-time/5)
x = carrier + noise

# Use loaded seismogram instead
st0 = st_triggering.copy()
tr = st0[1]
print(tr.stats)
tr.plot()

dt = tr.stats.starttime
print(dt)
tr.trim(dt, dt + 0.01)
print(tr.stats)



x = tr.data
print(x)
fs = np.round(tr.stats.sampling_rate)

# Plot spectrogram
f, t, Sxx = signal.spectrogram(x, fs)
plt.pcolormesh(t, f, Sxx, shading='gouraud')
plt.ylabel('Frequency [Hz]')
plt.xlabel('Time [sec]')
plt.show()


tr.plot()
tr.filter("lowpass", freq=1040, corners=2)
tr.plot()

#ObsPy dayplot
tr.plot(type="dayplot", interval=.01, right_vertical_labels=False,
        vertical_scaling_range=5e2, one_tick_per_line=True,
        color=['k', 'r', 'b', 'g'], show_y_UTC_label=False,
        events={'min_magnitude': 6.5})



# Amplitude spectrum
# sampling rate
sr = np.round(tr.stats.sampling_rate)
ts = 1.0/sr
t = np.arange(0,5,ts)

x = 3*np.sin(2*np.pi*1*t)
x += np.sin(2*np.pi*4*t)
x += 0.5* np.sin(2*np.pi*7*t)

plt.figure(figsize = (8, 6))
plt.plot(t, x, 'r')
plt.ylabel('Amplitude')

plt.show()


from numpy.fft import fft, ifft
from dug_seis.plotting.plotting import (
    plot_waveform_characteristic_function_magnitude,
    plot_time_waveform,
    plot_waveform_characteristic_function,
    get_time_vector
)

t = get_time_vector(st_triggering)
tr = st_triggering[1]
tr.filter("lowpass", freq=4e4, corners=2)
ns = 1e6
x = tr.data[0:1000]
t = t[0:1000]
fs = tr.stats.sampling_rate
len(tr)

X = fft(x)
N = len(X)
n = np.arange(N)
T = N/sr
freq = n/T

plt.figure(figsize = (12, 6))
plt.subplot(121)

plt.stem(freq, np.abs(X), 'b', markerfmt=" ", basefmt="-b")
plt.xlabel('Freq (Hz)')
plt.ylabel('FFT Amplitude |X(freq)|')
plt.yscale('log')
#plt.xlim(0, 10)

plt.subplot(122)
plt.plot(t, ifft(X), 'r')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.tight_layout()
plt.show()
