"""Module containing audio playing functionality."""

from pygame import mixer


AUDIO_PATH = "./res/audio/"

mixer.init()
mixer.music.set_volume(0.2)


def play_sfx_put() -> None:
    mixer.music.load(AUDIO_PATH + "put.wav")
    mixer.music.play(loops=1)


def play_sfx_break() -> None:
    mixer.music.load(AUDIO_PATH + "break.wav")
    mixer.music.play(loops=1)
