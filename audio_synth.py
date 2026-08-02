"""Процедурная генерация SFX, если файлов нет в assets/audio/sfx."""

import array
import math

SAMPLE_RATE = 44100


def _to_stereo_buffer(samples):
    buf = array.array("h")
    for sample in samples:
        value = max(-32767, min(32767, int(sample)))
        buf.append(value)
        buf.append(value)
    return buf


def _envelope(index, total, attack=0.08, release=0.35):
    if total <= 0:
        return 0.0
    t = index / total
    attack_amt = min(1.0, t / attack) if attack > 0 else 1.0
    release_start = 1.0 - release
    release_amt = 1.0
    if t > release_start and release > 0:
        release_amt = max(0.0, 1.0 - (t - release_start) / release)
    return attack_amt * release_amt


def _mix_tone(samples, freq, start, length, volume, wave="sine", detune=0.0):
    end = min(len(samples), start + length)
    for i in range(start, end):
        t = (i - start) / SAMPLE_RATE
        env = _envelope(i - start, end - start, 0.02, 0.45)
        phase = 2 * math.pi * freq * t
        if wave == "sine":
            value = math.sin(phase)
        elif wave == "triangle":
            value = 2 * abs(2 * (freq * t - math.floor(freq * t + 0.5))) - 1
        else:
            value = 1.0 if math.sin(phase) > 0 else -0.35
        shimmer = 1.0 + 0.12 * math.sin(2 * math.pi * 6 * t)
        samples[i] += env * volume * value * shimmer
        if detune:
            samples[i] += env * volume * 0.35 * math.sin(phase * (1 + detune))


def _mix_noise(samples, start, length, volume, decay=0.92):
    end = min(len(samples), start + length)
    noise = 0.0
    for i in range(start, end):
        env = _envelope(i - start, end - start, 0.01, 0.25)
        noise = decay * noise + (1 - decay) * (math.sin(i * 12.9898) * 43758.5453 % 1 * 2 - 1)
        samples[i] += env * volume * noise


def build_potion_pickup_sound():
    """Лёгкий «бульк» и восходящие ноты при подборе."""
    duration = 0.42
    count = int(SAMPLE_RATE * duration)
    samples = [0.0] * count
    _mix_noise(samples, 0, int(SAMPLE_RATE * 0.05), 0.18, decay=0.85)
    notes = (660, 880, 1175, 1480)
    step = int(SAMPLE_RATE * 0.07)
    for idx, freq in enumerate(notes):
        _mix_tone(samples, freq, idx * step, int(SAMPLE_RATE * 0.16), 0.16, wave="sine")
    return _to_stereo_buffer(samples)


def build_potion_drink_sound():
    """Глоток + мягкий исцеляющий перелив."""
    duration = 0.55
    count = int(SAMPLE_RATE * duration)
    samples = [0.0] * count
    _mix_noise(samples, 0, int(SAMPLE_RATE * 0.07), 0.22, decay=0.8)
    _mix_tone(samples, 180, int(SAMPLE_RATE * 0.04), int(SAMPLE_RATE * 0.12), 0.12, wave="triangle")
    heal_start = int(SAMPLE_RATE * 0.12)
    for freq in (523, 659, 784, 988):
        _mix_tone(samples, freq, heal_start, int(SAMPLE_RATE * 0.28), 0.11, wave="sine", detune=0.003)
        heal_start += int(SAMPLE_RATE * 0.05)
    return _to_stereo_buffer(samples)


def build_relic_pickup_sound():
    """Магический перелив при получении реликвии."""
    duration = 0.55
    count = int(SAMPLE_RATE * duration)
    samples = [0.0] * count
    notes = (523, 659, 784, 988, 1175)
    step = int(SAMPLE_RATE * 0.08)
    for idx, freq in enumerate(notes):
        _mix_tone(samples, freq, idx * step, int(SAMPLE_RATE * 0.18), 0.13, wave="sine", detune=0.004)
    _mix_tone(samples, 880, int(SAMPLE_RATE * 0.35), int(SAMPLE_RATE * 0.15), 0.08, wave="triangle")
    return _to_stereo_buffer(samples)


def build_sword_swing_sound():
    """Свист взмаха."""
    duration = 0.18
    count = int(SAMPLE_RATE * duration)
    samples = [0.0] * count
    for i in range(count):
        t = i / count
        env = _envelope(i, count, 0.01, 0.55)
        freq = 900 + 1400 * t
        samples[i] += env * 0.14 * math.sin(2 * math.pi * freq * (i / SAMPLE_RATE))
    _mix_noise(samples, 0, count, 0.08, decay=0.94)
    return _to_stereo_buffer(samples)


def build_sword_hit_sound():
    """Удар по цели — короткий металлический щелчок."""
    duration = 0.14
    count = int(SAMPLE_RATE * duration)
    samples = [0.0] * count
    _mix_noise(samples, 0, int(SAMPLE_RATE * 0.04), 0.35, decay=0.75)
    for freq in (420, 680, 920):
        _mix_tone(samples, freq, 0, int(SAMPLE_RATE * 0.08), 0.12, wave="triangle")
    return _to_stereo_buffer(samples)


def build_enemy_death_sound():
    """Короткий глухой удар при смерти врага."""
    duration = 0.22
    count = int(SAMPLE_RATE * duration)
    samples = [0.0] * count
    _mix_noise(samples, 0, int(SAMPLE_RATE * 0.08), 0.28, decay=0.82)
    for freq in (120, 180, 260):
        _mix_tone(samples, freq, 0, int(SAMPLE_RATE * 0.12), 0.14, wave="triangle")
    return _to_stereo_buffer(samples)


def build_coin_sound():
    """Звон монеты / подбора предмета."""
    duration = 0.18
    count = int(SAMPLE_RATE * duration)
    samples = [0.0] * count
    for freq in (880, 1175, 1480):
        _mix_tone(samples, freq, int(SAMPLE_RATE * 0.02), int(SAMPLE_RATE * 0.12), 0.11, wave="sine")
    return _to_stereo_buffer(samples)


def build_level_up_sound():
    """Восходящий аккорд при повышении уровня."""
    duration = 0.65
    count = int(SAMPLE_RATE * duration)
    samples = [0.0] * count
    notes = (523, 659, 784, 988, 1175)
    step = int(SAMPLE_RATE * 0.09)
    for idx, freq in enumerate(notes):
        _mix_tone(samples, freq, idx * step, int(SAMPLE_RATE * 0.22), 0.12, wave="sine", detune=0.002)
    return _to_stereo_buffer(samples)
