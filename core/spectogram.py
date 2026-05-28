import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import maximum_filter
from scipy.signal import butter, lfilter, spectrogram


def butter_lowpass(cutoff, sr, order=5):
    nyq = 0.5 * sr
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    return b, a


def lowpass_filter(data, cutoff, sr, order=5):
    b, a = butter_lowpass(cutoff, sr, order)
    y = lfilter(b, a, data)
    return y


def spectogram_plot(audio_file, cutoff=5000):

    y, sr = librosa.load(audio_file)
    duration = librosa.get_duration(y=y, sr=sr)
    y_filtered = lowpass_filter(y, cutoff, sr)
    print(sr)
    S = librosa.stft(y_filtered)
    S_db = librosa.amplitude_to_db(abs(S))
    return abs(S), sr, duration


def make_log_bands(n_bins, start=10):
    bands = []
    low = 0
    high = start
    while high < n_bins:
        bands.append((low, high))
        low = high
        high = min(2 * high, n_bins)
    if low < n_bins:
        bands.append((low, n_bins))
    return bands


def extract_peak(S, audioDuration, sampleRate):
    n_bins, lenS = S.shape

    peaks = []
    frame_duration = audioDuration / lenS
    n_fft = (S.shape[0] - 1) * 2
    freq_resolution = sampleRate / n_fft
    print(sampleRate)
    print(n_fft)
    print("freq_res=", freq_resolution)
    bands = make_log_bands(n_bins)
    print(bands)
    for frame_ind in range(lenS):
        frame = S[:, frame_ind]
        max_mags = []
        freq_indices = []
        for low, high in bands:
            band_slice = frame[low:high]

            idx = np.argmax(band_slice)
            max_mags.append(band_slice[idx])
            freq_indices.append(low + idx)
        avg = np.mean(max_mags)
        for mag, f_ind in zip(max_mags, freq_indices):
            if mag > avg:
                peak_time = frame_ind * frame_duration
                peak_freq = f_ind * freq_resolution
                peaks.append((peak_time, peak_freq))
    return peaks
