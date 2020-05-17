import tkinter as tk
from tkinter import ttk
from waveforms import SineWave, SquareWave
from filters import FreqModulationFilter

class OscillatorGUI(ttk.LabelFrame):
    """
    GUI unit for an oscillator panel.
    """
    def __init__(self, master_frame, output, name):
        super().__init__(master_frame, text=name)
        self.name = name
        self.output = output
        self.osc = None
        self.UI()
        self.to_oscillator = None

    def UI(self):
        """
        Generate UI.
        """
        # Waveform choice
        self.waveforms = {
            "sine": SineWave,  
            "square": SquareWave,
            "triangle": None,
            "sawtooth": None,
            "noise": None
            }
        self.input_waveformtype = tk.StringVar()
        self.waveform = ttk.OptionMenu(self, self.input_waveformtype, 'sine', *self.waveforms.keys(), command=self.create_osc)
        self.waveform.pack(padx=10, pady=10)
        
        # Set frequency
        self.freq_frame = tk.Frame(self)
        self.freq_label = tk.Label(self.freq_frame, text="Freq (Hz)")
        self.freq_label.grid(row=0, column=0)
        self.frequency = tk.IntVar(value=440)
        self.input_freq = tk.Entry(self.freq_frame, width=10, textvariable=self.frequency)
        self.input_freq.grid(row=0, column=1, pady=10)
        self.input_freq.bind('<Return>', self.set_frequency)

        # Create oscillator object on creation.
        # Defaults to sine.
        self.create_osc()

    def FM_frame(self):
        self.fm_frame = tk.Frame(self)
        self.fm_frame.pack()
        self.fm_label = tk.Label(self.fm_frame, text="FM to : ")
        self.fm_label.grid(row=0, column=0)
        self.osc_input = tk.StringVar() 
        self.oscillator_list = {str(o.osc): o for o in self.output.get_next_oscillators(self)}
        self.oscillator_menu = ttk.OptionMenu(self.fm_frame, self.osc_input, 'None', 'None', *self.oscillator_list.keys(), command=self.do_modulate)        
        self.oscillator_menu.grid(row=0, column=1)

    def do_modulate(self, *args):
        if self.osc:
            if self.osc_input.get() == 'None':
                self.to_oscillator = None
            else:
                self.to_oscillator = self.oscillator_list[self.osc_input.get()]
            self.output.play()

    def create_osc(self, *args):
        """
        Instantiate oscillator after waveform type selection.
        """
        waveform = self.waveforms[self.input_waveformtype.get()]
        self.osc = waveform(name=self.name)
        self.output.add_oscillator(self)
        self.set_frequency()
        self.freq_frame.pack()

    def set_frequency(self, *args):
        """
        Set frequency to input value.
        """
        if self.osc: self.osc.frequency= int(self.input_freq.get())
