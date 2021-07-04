from PyQt5.QtCore import QObject
from PyQt5.QtMultimedia import QSound


class Sounds(QObject):
    def __init__(self, audio_on=True, *args, **kwargs):
        super(Sounds, self).__init__(*args, **kwargs)
        self.audio_on = audio_on
        self.tick = GameSound("./wav//tick.wav", self)
        self.tick2 = GameSound("./wav//tick2.wav", self)
        self.line_cleared = GameSound("./wav//line_cleared.wav", self)
        self.restart = GameSound("./wav//restart.wav", self)

    def play(self):
        if self.parent.audio_on:
            super(Sounds, self).play()

    def toggle_sound(self, toggle: bool):
        self.audio_on = toggle


class GameSound(QSound):
    def __init__(self, filename, parent):
        super(GameSound, self).__init__(filename)
        self.parent = parent

    def play(self):
        if self.parent.audio_on:
            super(GameSound, self).play()
