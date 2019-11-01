# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////

import math
import sys
import time
import threading

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
import RPi.GPIO as GPIO
from pidev.stepper import stepper
from pidev.Cyprus_Commands import Cyprus_Commands_RPi as cyprus

# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
ON = True
OFF = True
HOME = True
TOP = False
OPEN = False
CLOSE = True
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
DEBOUNCE = 0.1
INIT_RAMP_SPEED = 150
RAMP_LENGTH = 725


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):
    def build(self):
        self.title = "Perpetual Motion"
        return sm


Builder.load_file('main.kv')
Window.clearcolor = (.1, .1, .1, 1)  # (WHITE)

cyprus.open_spi()

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////
sm = ScreenManager()
ramp = stepper(port=0, speed=INIT_RAMP_SPEED)

# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////


def debounce():
    pass


def toggle_gate():
    global CLOSE
    if CLOSE:
        cyprus.set_servo_position(2, 0)
    else:
        cyprus.set_servo_position(2, 0.5)
    CLOSE = not CLOSE


def toggle_staircase(speed):
    global ON
    if ON:
        cyprus.set_pwm_values(1, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
    else:
        cyprus.set_pwm_values(1, period_value=100000, compare_value=speed * 1000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
    ON = not ON


def move_ramp():
    pass


def set_ramp_speed(speed):
    pass


def set_staircase_speed(speed):
    print(speed)
    if ON:
        cyprus.set_pwm_values(1, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        cyprus.set_pwm_values(1, period_value=100000, compare_value=speed * 1000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)


def is_ball_at_bottom():
    return (cyprus.read_gpio() & 0b0010) == 0


def is_ball_at_top():
    return (cyprus.read_gpio() & 0b0001) == 0

# ////////////////////////////////////////////////////////////////
# //        DEFINE MAINSCREEN CLASS THAT KIVY RECOGNIZES        //
# //                                                            //
# //   KIVY UI CAN INTERACT DIRECTLY W/ THE FUNCTIONS DEFINED   //
# //     CORRESPONDS TO BUTTON/SLIDER/WIDGET "on_release"       //
# //                                                            //
# //   SHOULD REFERENCE MAIN FUNCTIONS WITHIN THESE FUNCTIONS   //
# //      SHOULD NOT INTERACT DIRECTLY WITH THE HARDWARE        //
# ////////////////////////////////////////////////////////////////


class MainScreen(Screen):
    version = cyprus.read_firmware_version()
    rampSpeed = INIT_RAMP_SPEED
    staircaseSpeed = 40

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    def toggleGate(self):
        toggle_gate()

    def toggleStaircase(self):
        toggle_staircase(self.staircaseSpeed)

    def toggleRamp(self):
        print("Move ramp up and down here")

    def auto(self):
        print("Run through one cycle of gatethe perpetual motion machine")

    def setRampSpeed(self, speed):
        self.rampSpeed = speed
        set_ramp_speed(self.rampSpeed)
        self.ids.rampSpeedLabel.text = 'Ramp Speed: ' + str(self.rampSpeed)

    def setStaircaseSpeed(self, speed):
        self.staircaseSpeed = speed
        set_staircase_speed(self.staircaseSpeed)
        self.ids.staircaseSpeedLabel.text = 'Staircase Speed: ' + str(self.staircaseSpeed)

    def initialize(self):
        toggle_gate()
        toggle_staircase(self.staircaseSpeed)
        print("Close gate, stop staircase and home ramp here")

    def resetColors(self):
        self.ids.gate.color = YELLOW
        self.ids.staircase.color = YELLOW
        self.ids.ramp.color = YELLOW
        self.ids.auto.color = BLUE

    def quit(self):
        print("Exit")
        MyApp().stop()


sm.add_widget(MainScreen(name='main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////

MyApp().run()
cyprus.close_spi()
