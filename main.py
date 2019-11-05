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
TOP = True
OPEN = True
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
DEBOUNCE = 0.1
INIT_RAMP_SPEED = 25
RAMP_LENGTH = 225
INIT_SC_SPEED = 40


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
ramp = stepper(port=0, micro_steps=32, hold_current=20, run_current=20, accel_current=20, deaccel_current=20,
               steps_per_unit=25, speed=INIT_RAMP_SPEED)

# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////


def debounce(is_top):
    if is_top:
        if is_ball_at_top():
            sleep(DEBOUNCE)
            if is_ball_at_top():
                return True
    else:
        if is_ball_at_bottom():
            sleep(DEBOUNCE)
            if is_ball_at_bottom():
                return True
    return False


def toggle_gate():
    global OPEN
    if OPEN:
        cyprus.set_servo_position(2, 0.05)
    else:
        cyprus.set_servo_position(2, 0.5)
    OPEN = not OPEN


def toggle_staircase(speed):
    global ON
    if ON:
        cyprus.set_pwm_values(1, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
    else:
        cyprus.set_pwm_values(1, period_value=100000, compare_value=speed*1000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
    ON = not ON


def move_ramp():
    global TOP
    if TOP:
        ramp.home(0)
    else:
        ramp.start_go_to_position(RAMP_LENGTH)
    TOP = not TOP


def set_ramp_speed(speed):
    ramp.set_speed(speed)


def set_staircase_speed(speed):
    if ON:
        cyprus.set_pwm_values(1, period_value=100000, compare_value=speed*1000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
    else:
        cyprus.set_pwm_values(1, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)


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
    staircaseSpeed = INIT_SC_SPEED

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    def toggleGate(self):
        toggle_gate()
        if OPEN:
            self.ids.gate.text = "Close Gate"
        else:
            self.ids.gate.text = "Open Gate"

    def toggleStaircase(self):
        toggle_staircase(self.staircaseSpeed)
        if ON:
            self.ids.staircase.text = "Staircase Off"
        else:
            self.ids.staircase.text = "Staircase On"

    def toggleRamp(self):
        move_ramp()
        if TOP:
            self.ids.ramp.text = "Ramp to Home"
        else:
            self.ids.ramp.text = "Ramp to Top"

    def auto(self):
        global ON
        global OPEN
        global TOP
        ON = True
        OPEN = True
        TOP = True
        sc_temp = self.staircaseSpeed
        ramp_temp = self.rampSpeed
        self.staircaseSpeed = INIT_SC_SPEED
        self.rampSpeed = INIT_RAMP_SPEED
        set_staircase_speed(self.staircaseSpeed)
        set_ramp_speed(self.rampSpeed)
        self.initialize()
        while not debounce(False):
            print("Please place ball at home.")
            sleep(1)
        move_ramp()
        while ramp.is_busy():
            sleep(0.1)
        toggle_staircase(self.staircaseSpeed)
        move_ramp()
        toggle_staircase(self.staircaseSpeed)
        toggle_gate()

        self.staircaseSpeed = sc_temp
        self.rampSpeed = ramp_temp
        set_staircase_speed(self.staircaseSpeed)
        set_ramp_speed(self.rampSpeed)

    def setRampSpeed(self, speed):
        self.rampSpeed = speed
        set_ramp_speed(self.rampSpeed)
        self.ids.rampSpeedLabel.text = 'Ramp Speed: ' + str(self.rampSpeed)

    def setStaircaseSpeed(self, speed):
        self.staircaseSpeed = speed
        set_staircase_speed(self.staircaseSpeed)
        self.ids.staircaseSpeedLabel.text = 'Staircase Speed: ' + str(self.staircaseSpeed)

    def initialize(self):
        move_ramp()
        toggle_gate()
        toggle_staircase(self.staircaseSpeed)

    def resetColors(self):
        self.ids.gate.color = YELLOW
        self.ids.staircase.color = YELLOW
        self.ids.ramp.color = YELLOW
        self.ids.auto.color = BLUE

    def quit(self):
        print("Exit")
        ramp.free_all()
        GPIO.cleanup()
        GPIO.cleanup()
        cyprus.close()
        MyApp().stop()


sm.add_widget(MainScreen(name='main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////

MyApp().run()
cyprus.close_spi()
