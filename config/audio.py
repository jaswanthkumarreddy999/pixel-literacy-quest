"""
audio.py — SoundManager for Pixel Literacy Quest
Synthesizes all sounds programmatically; no external audio files needed.
"""
import pygame
import math

_sounds = {}
_enabled = False

def _make_tone(freq, duration_ms, volume=0.4, wave='sine', sample_rate=44100):
    """Generate a pygame Sound object from a pure tone."""
    try:
        import numpy as np
        n = int(sample_rate * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, n, False)
        if wave == 'sine':
            arr = np.sin(2 * np.pi * freq * t)
        elif wave == 'square':
            arr = np.sign(np.sin(2 * np.pi * freq * t))
        elif wave == 'sawtooth':
            arr = 2 * (t * freq - np.floor(0.5 + t * freq))
        else:
            arr = np.sin(2 * np.pi * freq * t)
        # Fade out last 10% to avoid clicks
        fade = int(n * 0.1)
        arr[-fade:] *= np.linspace(1, 0, fade)
        arr = (arr * volume * 32767).astype(np.int16)
        stereo = np.column_stack([arr, arr])
        return pygame.sndarray.make_sound(stereo)
    except Exception:
        return None

def _make_chord(freqs, duration_ms, volume=0.3, sample_rate=44100):
    try:
        import numpy as np
        n = int(sample_rate * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, n, False)
        arr = np.zeros(n)
        for f in freqs:
            arr += np.sin(2 * np.pi * f * t)
        arr /= len(freqs)
        fade = int(n * 0.15)
        arr[-fade:] *= np.linspace(1, 0, fade)
        arr = (arr * volume * 32767).astype(np.int16)
        stereo = np.column_stack([arr, arr])
        return pygame.sndarray.make_sound(stereo)
    except Exception:
        return None


def init():
    """Initialize mixer and synthesize all game sounds."""
    global _sounds, _enabled
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        _sounds = {
            'coin':       _make_tone(880, 80, 0.3),
            'income':     _make_chord([523, 659, 784], 200, 0.25),
            'correct':    _make_chord([523, 659, 784, 1046], 350, 0.3),
            'wrong':      _make_tone(200, 400, 0.4, 'square'),
            'scam_alert': _make_chord([150, 180], 600, 0.45, ),
            'winner':     _make_chord([523, 659, 784, 1046, 1318], 800, 0.35),
            'event_good': _make_chord([659, 880], 250, 0.3),
            'event_bad':  _make_tone(220, 350, 0.4, 'sawtooth'),
            'budget':     _make_tone(440, 200, 0.25),
            'click':      _make_tone(600, 60, 0.2),
        }
        _enabled = True
    except Exception:
        _enabled = False


def play(name: str):
    """Play a named sound. Silently ignores missing sounds or disabled mixer."""
    if not _enabled:
        return
    snd = _sounds.get(name)
    if snd:
        try:
            snd.play()
        except Exception:
            pass
