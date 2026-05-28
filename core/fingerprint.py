from dataclasses import dataclass

from core.spectogram import extract_peak, spectogram_plot


@dataclass
class Peak:
    time: float
    freq: float


@dataclass
class Couple:
    anchor_time_ms: int
    song_id: int


MAX_FREQ_BITS = 9
MAX_DELTA_BITS = 14
TARGET_ZONE_SIZE = 5


def create_address(anchor: Peak, target: Peak) -> int:
    anchor_freq_bin = int(anchor.freq // 10)
    target_freq_bin = int(target.freq // 10)
    delta_ms_raw = int((target.time - anchor.time) * 1000)
    anchor_freq_bits = anchor_freq_bin & ((1 << MAX_FREQ_BITS) - 1)
    target_freq_bits = target_freq_bin & ((1 << MAX_FREQ_BITS) - 1)
    delta_bits = delta_ms_raw & ((1 << MAX_DELTA_BITS) - 1)

    address = (anchor_freq_bits << 23) | (target_freq_bits << 14) | delta_bits
    return address


def fingerprint(peaks: list[Peak], song_id: int) -> dict[int, Couple]:
    fingerprints = {}
    for i, anchor in enumerate(peaks):
        for j in range(i + 1, min(i + 1 + TARGET_ZONE_SIZE, len(peaks))):
            address = create_address(anchor, peaks[j])
            anchor_time_ms = int(anchor.time * 1000)
            fingerprints[address] = Couple(
                anchor_time_ms=anchor_time_ms, song_id=song_id
            )
    return fingerprints


def fingerprint_audio(audio_file: str, song_id: int) -> dict[int, Couple]:
    S, sr, duration = spectogram_plot(audio_file)
    raw_peaks = extract_peak(S, duration, sr)
    peaks = [Peak(time=t, freq=f) for t, f in raw_peaks]
    fingerprints = fingerprint(peaks, song_id)
    return fingerprints
