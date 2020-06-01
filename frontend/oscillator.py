import tkinter as tk
import string
from tkinter import ttk
from pysynth.waveforms import SineWave, SquareWave
from pysynth.filters import FreqModulationFilter
from PIL import ImageTk, Image


class FmButton(tk.Frame):

    def __init__(self, master, gui, oscillator):
        super().__init__(master)
        self.master = master
        self.gui = gui
        self.output = gui.output
        self.oscillator = oscillator
        self.osc_input = tk.IntVar()
        self.to_option = tk.Checkbutton(self, text=str(oscillator.osc),
                                        command=self.do_modulate, 
                                        variable=self.osc_input)
        self.to_option.grid(row=0, column=1)

    def do_modulate(self):
        """
        Callback function from Checkbutton object.
        Adds the given oscillator to the list of destination oscillators in the parent.
        """
        if self.osc_input.get():
            self.gui.to_oscillators.append(self.oscillator)
        else:
            self.gui.to_oscillators.remove(self.oscillator)
        self.gui.output.route_and_filter()


class OscillatorGUI(ttk.LabelFrame):
    """
    GUI unit for an oscillator panel.
    """
    def __init__(self, master_frame, output, number):
        super().__init__(master_frame)
        self.number = number
        self.name = f'Oscillator {string.ascii_uppercase[number]}'
        self.output = output
        self.osc = None        
        self.to_oscillators = []
        self.fm_frame = None
        self.UI()

    def UI(self):
        """
        Generate UI.
        """
        self.images = [
            r'static\oscillators\osA.png',  
            r'static\oscillators\osB.png',
            r'static\oscillators\osC.png',
            r'static\oscillators\osD.png'
            ]
        self.wave_frame = tk.Frame(self)
        self.wave_frame.pack(padx=10, pady=10)
        self.wave_icon = ImageTk.PhotoImage(Image.open(self.images[self.number]).convert('RGBA').resize((20,20)))
        self.image_panel = tk.Label(self.wave_frame, image=self.wave_icon)
        self.image_panel.grid(row=0, column=0)
        
        # Waveform choice
        self.waveforms = {
            "sine": SineWave,  
            "square": SquareWave
            # "triangle": None,
            # "sawtooth": None,
            # "noise": None
            }
        self.input_waveformtype = tk.StringVar()
        self.waveform = ttk.OptionMenu(self.wave_frame, self.input_waveformtype, 'sine', *self.waveforms.keys(), command=self.create_osc)
        self.waveform.grid(row=0, column=1)
        
        # Generate frequency frame
        self.set_freq_frame()

        # Create oscillator object on creation.
        # Defaults to sine.
        self.create_osc()

    def set_freq_frame(self):
        self.freq_frame = tk.Frame(self)
        self.fixed_var = tk.BooleanVar(value=0)
        self.freq_fixed = tk.Checkbutton(self.freq_frame, text="Fixed", variable=self.fixed_var, command=self.set_ratio_frame)
        self.freq_fixed.pack()
        self.input_freq_frame = tk.Frame(self.freq_frame)
        self.freq_label = tk.Label(self.input_freq_frame, text="Freq. (Hz)")
        self.freq_label.grid(row=1, column=0)
        self.frequency_var = tk.IntVar(value=440)
        self.input_freq = tk.Entry(self.input_freq_frame, width=10, textvariable=self.frequency_var)
        self.input_freq.grid(row=1, column=1, pady=10)
        self.input_freq.bind('<Return>', self.set_frequency)
        self.input_freq_frame.pack()
        self.ratio_frame = tk.Frame(self.freq_frame)
        self.ratio_label = tk.Label(self.ratio_frame, text="Freq. ratio")
        self.ratio_label.grid(row=0, column=0)
        self.ratio_var = tk.DoubleVar(value=1.0)
        self.input_ratio = tk.Entry(self.ratio_frame, width=10, textvariable=self.ratio_var)
        self.input_ratio.grid(row=0, column=1, pady=10)
        self.set_ratio_frame()

    def ratio(self):
        return self.ratio_var.get()

    def fixed_frequency(self):
        return self.fixed_var.get()

    def set_ratio_frame(self):
        """
        Callback method from fix frequency checkbutton.
        If frequency is fixed, entry widget is enabled and user can input frequency.
        Otherwise enty widget is disabled and user can input a ratio.
        """
        if self.fixed_var.get() == 0:
            self.input_freq['state'] = "disabled"
            self.ratio_frame.pack()
        else:
            self.input_freq['state'] = "normal"
            self.ratio_frame.pack_forget()

    def FM_frame(self):
        """
        Generate FM frame.
        """
        # FM frame
        self.fm_frame = tk.Frame(self)
        self.fm_frame.pack()
        self.fm_label = tk.Label(self.fm_frame, text="FM to : ", anchor='n')
        self.fm_label.pack(pady=10)

        # FM options frame        
        self.op_frame = tk.Frame(self.fm_frame)
        self.op_frame.pack()

        for oscillator in self.output.get_next_oscillators(self):
            self.fm_button = FmButton(self.op_frame, self, oscillator)
            self.fm_button.pack()

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
