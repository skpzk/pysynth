from pysynth.params import blocksize, framerate
from copy import deepcopy, copy
from pysynth.audio_api import AudioApi
from pysynth.filters import AmpModulationFilter, FreqModulationFilter, SumFilter, Envelope, PassFilter
from pysynth.routing import Routing


class Output:
    """
    Central output object for implementing the audio logic.
    Keeps a reference of all created oscillator and VoiceChannel objects and  
    sends data to PortAudio through the AudioApi object.
    """
    def __init__(self):
        self.audio_api = AudioApi(framerate=framerate, blocksize=blocksize, channels=1)
        self.am_modulator = None
        self.filter_type = "lowpass"
        self.filter_cutoff = 18000
        self.oscillators = []
        self.voices = []
        self.max_voices = 6

    def add_oscillator(self, oscillator, index):
        """
        Adds an oscillator to the list, and recalculates the routing.
        """
        self.oscillators.insert(index, oscillator)
        self.do_routing()

    def get_next_oscillators(self, osc):
        """
        Get the next oscillators in the sequence.
        The oscillators are ordered from left to right in the GUI.
        """
        index = self.oscillators.index(osc)
        return self.oscillators[index + 1:]

    def set_am_modulator(self, waveform):
        """
        This function is called when 
        """
        self.am_modulator = waveform
        self.do_routing()

    def add_new_voice(self, voice):
        """
        A new VoiceChannel object is created each time a key is pressed, and added to the voice list.
        """
        if len(self.voices) >= self.max_voices:
            self.voices.pop()
        self.voices.append(voice)

    def release_notes(self, frequency):
        """
        This function is called when a key is released, and the voice channel is removed.
        """
        for voice in self.voices:
            if voice.frequency == frequency: 
                voice.release_notes()
                self.voices.remove(voice)

    def tremolo(self, source):
        """
        Add a tremolo effect (amplitude modulation) to the audio data pipeline.
        """
        if self.am_modulator:
            return AmpModulationFilter(source=source, modulator=self.am_modulator)
        else:
            return source

    def pass_filter(self, source):
        """
        Add a filter (butterworth) to the audio data pipeline.
        """
        if self.filter_type == "lowpass": return PassFilter.lowpass(source, self.filter_cutoff)
        elif self.filter_type == "highpass": return PassFilter.highpass(source, self.filter_cutoff)

    def do_routing(self):
        """
        Perform routing (creating the FM data pipeline).
        """
        for voice in self.voices:
            voice.do_routing()

    def apply_final_filters(self, signal):
        """
        Apply filters after routing.
        """
        final_output = self.tremolo(signal)
        final_output = self.pass_filter(final_output)
        return final_output

    def choose_algorithm(self, algo):
        """
        This function is called if the user picks a new FM algorithm in the gui.
        The appropriate function is obtained from an Algorithms class, which flags 
        each oscillator with their FM 'destination' where necessary.
        """
        algorithms = Algorithms(self.oscillators)
        algo_function = algorithms.algorithm_switch().get(algo)
        algo_function()
        self.do_routing()

    def get_output(self):
        """
        Before audio playback, create a generator summing the different voices.
        """
        outputs = [voice.filtered_output for voice in self.voices]
        return SumFilter(outputs)

    def play(self):
        """
        Perform routing, filtering and start playback.
        """
        output = self.get_output()
        final_output = self.apply_final_filters(output)
        self.audio_api.play(final_output)

    def stop(self):
        """
        Stop audio playback
        """
        self.audio_api.stop()


class Algorithms:
    """
    FM algorithm functions which defines an oscillator's FM 'destination' (to_oscillator)
    according to several different modulation patterns. 
    """
    def __init__(self, oscillators):
        assert(len(oscillators) == 4)
        self.oscillators = oscillators

    def stack(self):
        """
        1 carrier oscillator, 3 modulators in series.
        """
        for n, o in enumerate(self.oscillators):
            if n < len(self.oscillators) - 1:
                o.to_oscillators = [self.oscillators[n+1]]

    def parallel(self):
        """
        4 carrier oscillators in parallel.
        """
        for o in self.oscillators:
            o.to_oscillators = []

    def square(self):
        """
        2 carrier oscillators, each modulated.
        """
        for n, o in enumerate(self.oscillators):
            o.to_oscillators = []
            if n % 2 == 0:
                o.to_oscillators = [self.oscillators[n+1]]

    def three_to_one(self):
        """
        1 carrier oscillator, modulated by the other 3.
        """
        for n, o in enumerate(self.oscillators):
            o.to_oscillators = []
            if n < len(self.oscillators) - 1:
                o.to_oscillators = [self.oscillators[-1]]

    def algorithm_switch(self):
        return {
            "stack": self.stack,
            "parallel": self.parallel,
            "square": self.square,
            "3to1": self.three_to_one
        }


class VoiceChannel:
    """
    A VoiceChannel object is instantiated each time a key is pressed. Upon instantiation, 
    a deep copy is made of the synth's oscillators to ensure seperate data channels for each note,
    then the FM pipeline is generated.
    """
    def __init__(self, output, frequency):
        oscillators = deepcopy(output.oscillators)
        self.oscillators = [Envelope(o) for o in oscillators]
        self.set_frequency(frequency)
        self.frequency = frequency
        self.do_routing()

    def do_routing(self):
        """
        Instantiate a Routing object which outputs the carrier waves after FM modulation.
        The resulting waves are then summed.
        """
        routing = Routing(self.oscillators)
        carriers = routing.get_final_output()
        if len(carriers) > 1: 
            self.filtered_output = routing.sum_signals(carriers)
        else: self.filtered_output = carriers[0]

    def set_frequency(self, frequency):
        """
        Set frequency of oscillators from external source (e.g midi controller).
        """
        filtered_oscillators = [o for o in self.oscillators if not o.source.disabled]
        for o in filtered_oscillators:
            if o.source.fixed_frequency: pass
            else:
                ratio = o.source.frequency_ratio
                o.source.frequency = frequency * ratio

    def release_notes(self):
        """
        Upon release of the note, set oscillators to decay state.
        """
        for o in self.oscillators:
            o.state = 4