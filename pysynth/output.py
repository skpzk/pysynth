from pysynth.params import blocksize, framerate
from copy import copy
from pysynth.audio_api import AudioApi
from pysynth.filters import AmpModulationFilter, FreqModulationFilter, SumFilter
from pysynth.routing import Routing


class Algorithms:

    def __init__(self, oscillators):
        assert(len(oscillators) == 4)
        self.oscillators = oscillators

    def stack(self):
        for n, o in enumerate(self.oscillators):
            if n < len(self.oscillators) - 1:
                o.to_oscillators = [self.oscillators[n+1]]

    def parallel(self):
        for o in self.oscillators:
            o.to_oscillators = []
            

class Output:

    def __init__(self):
        self.audio_api = AudioApi(framerate=framerate, blocksize=blocksize, channels=1)
        self.am_modulator = None
        self.oscillators = []
        self.filtered_ouput = None

    def set_am_modulator(self, waveform):
        self.am_modulator = waveform
        self.route_and_filter()

    def get_next_oscillators(self, osc):
        """
        Get the next oscillators in the sequence.
        The oscillators are ordered from left to right in the GUI.
        """
        index = self.oscillators.index(osc)
        return self.oscillators[index + 1:]

    def add_oscillator(self, oscillator):
        self.oscillators.append(oscillator)
        self.route_and_filter()

    def tremolo(self, source):
        """
        Apply a tremolo effect.
        """
        if self.am_modulator:
            return AmpModulationFilter(source=source, modulator=self.am_modulator)
        else:
            return source

    def route_and_filter(self):
        """
        Instantiate a Routing object which outputs the carrier waves after FM modulation.
        The resulting waves are then summed, and filters applied.
        """
        routing = Routing(self.oscillators)
        carriers = routing.get_final_output()
        if len(carriers) > 1: 
            output = routing.sum_signals(carriers)
        else: output = carriers[0]
        self.filtered_ouput = self.apply_filters(output)
        if self.audio_api.playing == True:
            self.play()

    def apply_filters(self, signal):
        """
        Apply filters after routing.
        """
        modulated_output = self.tremolo(signal)
        return modulated_output

    def set_output_frequency(self, frequency):
        """
        Set frequency of (non-modulating) oscillators from external source (e.g midi controller).
        """
        for o in self.oscillators:
            if o.to_oscillators: pass
            else: 
                o.osc.frequency = frequency
                o.frequency.set(frequency)

    def choose_algorthm(self, algo):
        algorithms = Algorithms(self.oscillators)
        if algo == 'stack':
            algorithms.stack()
        if algo == 'parallel':
            algorithms.parallel()
        self.route_and_filter()

    def play(self):
        """
        Perform modulation, filtering and start playback.
        """
        self.audio_api.play(self.filtered_ouput)

    def stop(self):
        """
        Stop audio playback
        """
        self.audio_api.stop()