# Vibe coding some firmware because python is boring 🤑
import keypad
import touchio
from adafruit_midi.control_change import ControlChange
from microcontroller import pin
from adafruit_midi.pitch_bend import PitchBend
from kmk.extensions.media_keys import MediaKeys
from kmk.extensions.rgb import RGB, AnimationModes
from kmk.keys import KC
from kmk.kmk_keyboard import KMKKeyboard
from kmk.modules.encoder import EncoderHandler
from kmk.modules.midi import MidiKeys
from kmk.modules.potentiometer import PotentiometerHandler
from kmk.scanners import Scanner
from kmk.scanners.keypad import KeysScanner


# KMK doesn't have a scanner for touch pads, so here's a tiny one.
# Don't touch the pads while the board boots - they calibrate on startup!
class TouchScanner(Scanner):
    def __init__(self, pins):
        self.pads = [touchio.TouchIn(p) for p in pins]
        self.pressed = [False] * len(pins)

    @property
    def key_count(self):
        return len(self.pads)

    def scan_for_changes(self):
        for i, pad in enumerate(self.pads):
            touched = pad.value
            if touched != self.pressed[i]:
                self.pressed[i] = touched
                return keypad.Event(i + self.offset, touched)


keyboard = KMKKeyboard()
# These have to be created before we use KC.MIDI_NOTE / KC.VOLU below
midi = MidiKeys()
media_keys = MediaKeys()

keyboard.matrix = [
    # Touch pads 1-7 (keys 0-6)
    TouchScanner([pin.GPIO1, pin.GPIO2, pin.GPIO3, pin.GPIO4, pin.GPIO5, pin.GPIO6, pin.GPIO7]),
    # Switches SW1-SW3 (keys 7-9)
    KeysScanner([pin.GPIO44, pin.GPIO43, pin.GPIO13], value_when_pressed=False, pull=True),
]

# Touch pads play a C major scale, switches play drum sounds
keyboard.keymap = [[
    KC.MIDI_NOTE(60), KC.MIDI_NOTE(62), KC.MIDI_NOTE(64), KC.MIDI_NOTE(65),
    KC.MIDI_NOTE(67), KC.MIDI_NOTE(69), KC.MIDI_NOTE(71),
    KC.MIDI_NOTE(36), KC.MIDI_NOTE(38), KC.MIDI_NOTE(42),  # kick, snare, hi-hat
]]

# Rotary encoder controls your computer's volume
encoder = EncoderHandler()
encoder.pins = ((pin.GPIO8, pin.GPIO9, None),)  # A = TX, B = RX, no button
encoder.map = [((KC.VOLD, KC.VOLU, KC.NO),)]

# Slider 1 sends pitch bend; slider 2 sends CC7 (volume)
sliders = PotentiometerHandler()
sliders.pins = (
    (pin.GPIO10, lambda state: midi.send(PitchBend(state.position * 16383 // 127))),
    (pin.GPIO11, lambda state: midi.send(ControlChange(7, state.position))),
)

keyboard.modules = [midi, encoder, sliders]
keyboard.extensions = [
    media_keys,
    RGB(pixel_pin=pin.GPIO12, num_pixels=3, val_default=80, animation_mode=AnimationModes.RAINBOW),
]

if __name__ == '__main__':
    keyboard.go()
