from random import choice

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

        self.bubbles_01 = GameSound("./wav//bubbles_01.wav", self)
        # self.bubbles_02 = GameSound("./wav//bubbles_02.wav", self)
        self.bubbles_03 = GameSound("./wav//bubbles_03.wav", self)
        # self.bubbles_04 = GameSound("./wav//bubbles_04.wav", self) # ?
        self.bubbles_05 = GameSound("./wav//bubbles_05.wav", self)
        # self.bubbles_06 = GameSound("./wav//bubbles_06.wav", self)
        self.bubbles_07 = GameSound("./wav//bubbles_07.wav", self)
        # self.bubbles_08 = GameSound("./wav//bubbles_08.wav", self)
        self.bubbles_09 = GameSound("./wav//bubbles_09.wav", self)

    def bubbles_play(self):
        sound = choice([self.bubbles_01,
                       # self.bubbles_02,
                       self.bubbles_03,
                       # self.bubbles_04,
                       self.bubbles_05,
                       # self.bubbles_06,
                       self.bubbles_07,
                       # self.bubbles_08,
                       self.bubbles_09])
        print(sound.fileName())
        sound.play()

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
