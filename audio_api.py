import sounddevice as sd
import numpy as np

class AudioApi:

    def __init__(self, framerate: int, blocksize: int, channels: int):
        self.framerate = framerate
        self.channels = channels        
        self.channel_mapping = np.arange(self.channels)
        self.blocksize = blocksize
        self.stream = self.initialize_stream()
        self.stream.start()
        self.data = None
        self.volume = 100.0

    def initialize_stream(self):
        """
        Initialize sounddevice OutputStream.
        """        
        stream = self.stream = sd.OutputStream(
            samplerate=self.framerate,
            channels=self.channels,
            blocksize=self.blocksize,
            callback=self.callback,
            #finished_callback=self.finished_callback,
            dtype='float32')

        return stream

    def prepare_data_blocks(self, data):
        """
        Puts data blocks into correct numpy format.
        The input data is in the form of a List[float].
        """
        data = np.asarray(data)
        if data.ndim < 2: data = data.reshape(-1, 1)
        return data

    def callback(self, outdata, frames, time, status):
        """
        PortAudio callback function for callback in OutputStream.
        """

        if not self.data:
            outdata[:self.blocksize, self.channel_mapping] = np.zeros((self.blocksize, self.channels))
        else:
            try: 
                data = next(self.data)
                data = self.prepare_data_blocks(data)
                outdata[:self.blocksize, self.channel_mapping] =  (self.volume / 100.0) * data
            except StopIteration:
                raise sd.CallbackStop

    def play(self, data):
        """
        Takes an audio data generator as input
        e.g an Oscillator object.
        """
        self.data = data.blocks()