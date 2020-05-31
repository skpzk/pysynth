from pysynth import params
import time
from pysynth.midi import MidiController
from pysynth.audio_api import AudioApi
from pysynth.waveforms import *
from pysynth.filters import *

### Amplitude Modulation

def AM_mod_test(duration):
    source = SineWave(440)
    modulator = SineWave(0)
    modulated_sound = AmpModulationFilter(source=source, modulator=modulator)
    audio_interface.play(modulated_sound)
    time.sleep(duration)

### Frequency Modulation

def FM_mod_test(duration):
    source = SineWave(440)
    modulator = SineWave(60)
    modulated_sound = FreqModulationFilter(source=source, modulator=modulator)
    audio_interface.play(modulated_sound)
    time.sleep(duration)

def midi_controller():
    cont = MidiController()
    print(cont.input_devices)


if __name__ == '__main__':
    global audio_interface 
    audio_interface = AudioApi(framerate=params.framerate, blocksize=params.blocksize, channels=1)
    FM_mod_test(2.0)