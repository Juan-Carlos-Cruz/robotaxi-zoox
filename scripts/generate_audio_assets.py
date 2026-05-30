from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path


RATE = 22050
ROOT = Path(__file__).resolve().parents[1] / "audio"


def clamp(sample: float) -> float:
    return max(-1.0, min(1.0, sample))


def write_wav(path: Path, frames: list[tuple[float, float]], rate: int = RATE) -> None:
    with wave.open(str(path), "w") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(rate)
        payload = bytearray()
        for left, right in frames:
            payload.extend(struct.pack("<h", int(clamp(left) * 32767)))
            payload.extend(struct.pack("<h", int(clamp(right) * 32767)))
        wav_file.writeframes(payload)


def periodic_components(duration: float, rng: random.Random, count: int, start_hz: float, end_hz: float, gain: float) -> list[tuple[float, float, float]]:
    components = []
    start_index = max(1, int(start_hz * duration))
    end_index = max(start_index + 1, int(end_hz * duration))
    for _ in range(count):
        harmonic_index = rng.randint(start_index, end_index)
        frequency = harmonic_index / duration
        amplitude = gain * (0.45 + rng.random() * 0.55)
        phase = rng.random() * math.tau
        components.append((frequency, amplitude, phase))
    return components


def periodic_noise(t: float, components: list[tuple[float, float, float]]) -> float:
    return sum(amplitude * math.sin(math.tau * frequency * t + phase) for frequency, amplitude, phase in components)


def triangle_wave(frequency: float, t: float, phase: float = 0.0) -> float:
    return (2.0 / math.pi) * math.asin(math.sin(math.tau * frequency * t + phase))


def soft_clip(value: float, drive: float = 1.0) -> float:
    return math.tanh(value * drive)


def envelope(t: float, duration: float, attack: float, release: float) -> float:
    attack_gain = min(1.0, t / max(attack, 1e-6))
    release_gain = min(1.0, (duration - t) / max(release, 1e-6))
    return max(0.0, min(attack_gain, release_gain, 1.0))


def build_lofi_ambient(duration: float = 12.0) -> list[tuple[float, float]]:
    rng = random.Random(11)
    chords = [
        (220.00, 261.63, 329.63),
        (196.00, 246.94, 293.66),
        (174.61, 220.00, 261.63),
        (196.00, 233.08, 293.66),
    ]
    arp_patterns = [
        (0, 1, 2, 1, 2, 1, 0, 1),
        (0, 1, 2, 1, 2, 1, 0, 1),
        (0, 1, 2, 1, 2, 1, 0, 2),
        (0, 1, 2, 1, 2, 1, 0, 1),
    ]
    beat = 60.0 / 88.0
    step = beat / 2.0
    section = duration / len(chords)
    left_noise = periodic_components(duration, rng, 8, 220.0, 900.0, 0.00065)
    right_noise = periodic_components(duration, rng, 8, 240.0, 980.0, 0.00065)
    frames = []

    for i in range(int(duration * RATE)):
        t = i / RATE
        chord_index = min(len(chords) - 1, int(t / section))
        chord = chords[chord_index]
        pattern = arp_patterns[chord_index]
        local_section_t = t - chord_index * section

        pad = 0.0
        for index, frequency in enumerate(chord):
            detune = 1.0 + (0.0012 if index % 2 else -0.0009)
            chorus = 1.0 + 0.0015 * math.sin(math.tau * (0.09 + index * 0.02) * t)
            pad += (0.12 / (1.08 + index)) * math.sin(math.tau * frequency * detune * chorus * t + index * 0.22)
            pad += (0.05 / (1.18 + index)) * math.sin(math.tau * (frequency * 2.0) * t + index * 0.41)
            pad += (0.035 / (1.2 + index)) * math.sin(math.tau * (frequency * 0.5) * t + index * 0.17)
        pad *= 0.78 + 0.22 * math.sin(math.tau * (1 / section) * local_section_t)

        bass_note = chord[0] / 2.0
        bass_phase = (t % beat) / beat
        bass_gate = 1.0 if bass_phase < 0.78 else 0.0
        bass_env = math.exp(-3.1 * bass_phase)
        bass = 0.082 * math.sin(math.tau * bass_note * t + 0.14) * bass_gate * bass_env
        bass += 0.026 * math.sin(math.tau * (bass_note * 2.0) * t + 0.05) * bass_gate * bass_env

        step_index = int(t / step)
        local_step = t - step_index * step
        note_index = pattern[step_index % len(pattern)]
        arp_freq = chord[note_index] * (2.0 if step_index % 4 in (1, 3) else 1.0)
        arp_env = math.exp(-4.8 * (local_step / max(step, 1e-6)))
        arp = 0.085 * math.sin(math.tau * arp_freq * t + 0.18) * arp_env
        arp += 0.032 * math.sin(math.tau * (arp_freq * 2.0) * t + 0.1) * arp_env

        accent = 0.0
        if step_index % 8 in (3, 7):
            accent = 0.028 * math.sin(math.tau * (arp_freq * 1.5) * t + 0.25) * arp_env

        beat_pos = (t % beat) / beat
        kick = 0.028 * math.sin(math.tau * 52.0 * t) * math.exp(-10.5 * beat_pos)
        snap = 0.005 * math.sin(math.tau * 3200.0 * t) * math.exp(-28.0 * beat_pos) if step_index % 4 == 2 else 0.0
        tape_left = periodic_noise(t, left_noise)
        tape_right = periodic_noise(t, right_noise)
        env = envelope(t, duration, attack=1.0, release=1.15)

        center = soft_clip(pad + bass + arp + accent + kick + snap, drive=1.08) * env * 0.5
        stereo_pad = 0.015 * math.sin(math.tau * 0.24 * t)
        left = center * (1.0 - stereo_pad) + tape_left
        right = center * (1.0 + stereo_pad) + tape_right
        frames.append((left, right))

    return frames


def build_engine_loop(duration: float = 2.0) -> list[tuple[float, float]]:
    rng = random.Random(23)
    engine_cycle = 73.5
    road_left = periodic_components(duration, rng, 26, 180.0, 1500.0, 0.0048)
    road_right = periodic_components(duration, rng, 26, 190.0, 1600.0, 0.0048)
    wind_left = periodic_components(duration, rng, 16, 800.0, 2600.0, 0.0023)
    wind_right = periodic_components(duration, rng, 16, 820.0, 2550.0, 0.0023)
    frames = []

    for i in range(int(duration * RATE)):
        t = i / RATE
        engine = (
            0.16 * math.sin(math.tau * engine_cycle * t)
            + 0.11 * math.sin(math.tau * (engine_cycle * 2.0) * t + 0.16)
            + 0.06 * math.sin(math.tau * (engine_cycle * 3.0) * t + 0.31)
            + 0.035 * math.sin(math.tau * (engine_cycle * 4.0) * t + 0.58)
        )
        sub_rumble = 0.08 * math.sin(math.tau * 36.75 * t + 0.4 * math.sin(math.tau * 2.0 * t))
        intake = 0.045 * math.sin(math.tau * 147.0 * t + 0.12 * math.sin(math.tau * 5.0 * t))
        chassis = 0.024 * math.sin(math.tau * 9.0 * t) * math.sin(math.tau * 49.0 * t + 0.25)
        suspension = 0.018 * math.sin(math.tau * 13.5 * t + 0.4) * math.sin(math.tau * 61.0 * t)
        road_l = periodic_noise(t, road_left)
        road_r = periodic_noise(t, road_right)
        wind_l = periodic_noise(t, wind_left)
        wind_r = periodic_noise(t, wind_right)
        stereo_sway = 0.05 * math.sin(math.tau * 0.5 * t)

        center = 0.64 * (engine + sub_rumble + intake) + chassis + suspension
        left = center * (1.0 - stereo_sway) + road_l + wind_l
        right = center * (1.0 + stereo_sway) + road_r + wind_r

        frames.append((left * 0.78, right * 0.78))

    return frames


def build_horn(duration: float, freqs: tuple[float, float], pulse_count: int, gap: float, harshness: float) -> list[tuple[float, float]]:
    total_samples = int(duration * RATE)
    pulse_length = (duration - gap * (pulse_count - 1)) / pulse_count
    frames = []

    for i in range(total_samples):
        t = i / RATE
        pulse_index = min(pulse_count - 1, int(t / (pulse_length + gap)))
        pulse_start = pulse_index * (pulse_length + gap)
        local_t = t - pulse_start

        if local_t < 0 or local_t > pulse_length:
            frames.append((0.0, 0.0))
            continue

        env = envelope(local_t, pulse_length, attack=0.012, release=0.08)
        flutter = 1.0 + 0.012 * math.sin(math.tau * 5.4 * local_t)
        slide = 1.0 - 0.035 * (local_t / max(pulse_length, 1e-6))

        tone = 0.0
        for idx, frequency in enumerate(freqs):
            freq = frequency * slide * flutter
            primary = math.sin(math.tau * freq * t + idx * 0.14)
            companion = math.sin(math.tau * (freq * 1.01) * t + idx * 0.37)
            second = math.sin(math.tau * (freq * 2.0) * t + idx * 0.22)
            low_body = math.sin(math.tau * (freq * 0.5) * t + idx * 0.12)
            tone += 0.22 * primary + 0.14 * companion + harshness * second + 0.04 * low_body

        rasp = 0.015 * math.sin(math.tau * 33.0 * t) * math.sin(math.tau * 470.0 * t)
        value = soft_clip(tone + rasp, drive=1.9) * env * 0.86
        stereo = 0.012 * math.sin(math.tau * 4.0 * t)
        frames.append((value * (1.0 - stereo), value * (1.0 + stereo)))

    return frames


def build_ui_click(duration: float = 0.11) -> list[tuple[float, float]]:
    total_samples = int(duration * RATE)
    frames = []

    for i in range(total_samples):
        t = i / RATE
        env = envelope(t, duration, attack=0.002, release=0.07)
        body = 0.18 * math.sin(math.tau * 1040.0 * t)
        sparkle = 0.10 * math.sin(math.tau * 1560.0 * t + 0.18)
        tail = 0.06 * math.sin(math.tau * 780.0 * t + 0.11) * math.exp(-10.0 * t / max(duration, 1e-6))
        tick = 0.035 * math.sin(math.tau * 2400.0 * t) * math.exp(-22.0 * t / max(duration, 1e-6))
        value = soft_clip(body + sparkle + tail + tick, drive=1.25) * env * 0.72
        stereo = 0.02 * math.sin(math.tau * 18.0 * t)
        frames.append((value * (1.0 - stereo), value * (1.0 + stereo)))

    return frames


def build_finish_jingle() -> list[tuple[float, float]]:
    note_specs = [
        (659.25, 0.11, 0.00),
        (783.99, 0.11, 0.09),
        (987.77, 0.14, 0.18),
        (1318.51, 0.22, 0.30),
    ]
    tail = 0.22
    duration = note_specs[-1][2] + note_specs[-1][1] + tail
    total_samples = int(duration * RATE)
    frames = []

    for i in range(total_samples):
        t = i / RATE
        value = 0.0

        for idx, (freq, length, start) in enumerate(note_specs):
            local_t = t - start
            if local_t < 0 or local_t > length:
                continue

            env = envelope(local_t, length, attack=0.01, release=0.09)
            sparkle = math.exp(-3.2 * local_t / max(length, 1e-6))
            voice = 0.18 * math.sin(math.tau * freq * t + idx * 0.15)
            voice += 0.09 * math.sin(math.tau * (freq * 2.0) * t + idx * 0.28)
            voice += 0.05 * triangle_wave(freq * 0.5, t, idx * 0.11)
            value += soft_clip(voice, drive=1.15) * env * sparkle

        ambience = 0.018 * math.sin(math.tau * 7.5 * t) * math.sin(math.tau * 520.0 * t)
        value = soft_clip(value + ambience, drive=1.05) * 0.9
        stereo = 0.03 * math.sin(math.tau * 3.2 * t)
        frames.append((value * (1.0 - stereo), value * (1.0 + stereo)))

    return frames


def main() -> None:
    ROOT.mkdir(exist_ok=True)
    write_wav(ROOT / "lofi_ambient.wav", build_lofi_ambient())
    write_wav(ROOT / "road_loop.wav", build_engine_loop())
    write_wav(ROOT / "pickup_horn.wav", build_horn(0.34, (380.0, 478.0), pulse_count=1, gap=0.05, harshness=0.09))
    write_wav(ROOT / "traffic_horn.wav", build_horn(0.46, (370.0, 466.0), pulse_count=2, gap=0.06, harshness=0.11))
    write_wav(ROOT / "ui_click.wav", build_ui_click())
    write_wav(ROOT / "finish_jingle.wav", build_finish_jingle())
    print(f"Audio generado en {ROOT}")


if __name__ == "__main__":
    main()
