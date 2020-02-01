import threading
import pyaudio
import numpy as np
import time
import SWHear
import operator

FREQ_BASE = 19020
FREQ_DIFF = 60
TONE_DURATION = 1000
NUM_OF_FREQS = 18
RECOGNIZE_THRESH = 0.4

BYTE_BUF_SIZE = 4

FREQ_0 = FREQ_BASE
FREQ_1 = FREQ_0 + FREQ_DIFF
FREQ_2 = FREQ_1 + FREQ_DIFF
FREQ_3 = FREQ_2 + FREQ_DIFF
FREQ_4 = FREQ_3 + FREQ_DIFF
FREQ_5 = FREQ_4 + FREQ_DIFF
FREQ_6 = FREQ_5 + FREQ_DIFF
FREQ_7 = FREQ_6 + FREQ_DIFF
FREQ_8 = FREQ_7 + FREQ_DIFF
FREQ_9 = FREQ_8 + FREQ_DIFF
FREQ_A = FREQ_9 + FREQ_DIFF
FREQ_B = FREQ_A + FREQ_DIFF
FREQ_C = FREQ_B + FREQ_DIFF
FREQ_D = FREQ_C + FREQ_DIFF
FREQ_E = FREQ_D + FREQ_DIFF
FREQ_F = FREQ_E + FREQ_DIFF
FREQ_T1 = FREQ_F + FREQ_DIFF
FREQ_T2 = FREQ_T1 + FREQ_DIFF

T1 = 16
T2 = 17

byte_to_freq = {
    0: FREQ_0, 1: FREQ_1, 2: FREQ_2, 3: FREQ_3, 4: FREQ_4,
    5: FREQ_5, 6: FREQ_6, 7: FREQ_7, 8: FREQ_8, 9: FREQ_9,
    10: FREQ_A, 11: FREQ_B, 12: FREQ_C, 13: FREQ_D, 14: FREQ_E,
    15: FREQ_F, T1: FREQ_T1, T2: FREQ_T2
}

freq_to_byte = dict((y,x) for x,y in byte_to_freq.items())

def get_freq_from_byte(byte):
    top = (byte & 0b11110000) >> 4
    bottom = byte & 0b00001111

    return (byte_to_freq[top], byte_to_freq[bottom])

def play_tones(f1):
    p = pyaudio.PyAudio()

    volume = 1     # range [0.0, 1.0]
    fs = 44100       # sampling rate, Hz, must be integer
    duration = 1   # in seconds, may be float
    f = 3000        # sine frequency, Hz, may be float

    # generate samples, note conversion to float32 array
    samples = (np.sin(2*np.pi*np.arange(fs*duration)*f1/fs)).astype(np.float32)

    # for paFloat32 sample values must be in range [-1.0, 1.0]
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=fs,
                    output=True)

    # play. May repeat with different volume values (if done interactively)
    stream.write(volume*samples)

    stream.stop_stream()
    stream.close()

    p.terminate()
    time.sleep(0.05)

def send_byte(byte):
    top, bottom = get_freq_from_byte(byte)
    play_tones(FREQ_T1)
    play_tones(top)
    play_tones(FREQ_T2)
    play_tones(bottom)

class ByteRingBuffer:
    def __init__(self, size):
        self.index = 0
        self.size = size
        self.buffer = [0 for i in range(size)]

    def add(self, new_byte):
        inc_index = lambda inc : (self.index + inc) % self.size

        self.buffer[self.index] = new_byte
        self.index = inc_index(1)

        if self.buffer[self.index] == T1 and self.buffer[inc_index(2)] == T2:
            return (self.buffer[inc_index(1)] << 4) | self.buffer[inc_index(3)]

        return None

class Listener:
    def __init__(self, callback):
        self.ear = SWHear.SWHear(rate=44100, updatesPerSecond=20, frequencySpacing=FREQ_DIFF, callback=self.update)
        self.ear.stream_start()
        self.maxFFT = 0
        self.fftStartIdx = int(FREQ_BASE / FREQ_DIFF)
        self.fftEndIdx = int(FREQ_T2 / FREQ_DIFF) + 1
        self.fft_dict = {}
        self.last_max = 0
        self.ring_buf = ByteRingBuffer(BYTE_BUF_SIZE)
        self.callback = callback

    def update(self):
        if self.ear.data is None or self.ear.fft is None: return

        self.maxFFT = np.max(np.abs(self.ear.fft))

        fftx = self.ear.fftx[self.fftStartIdx:self.fftEndIdx]
        fft = self.ear.fft[self.fftStartIdx:self.fftEndIdx]
        self.fft_dict = dict(zip(fftx,fft/self.maxFFT))

        max_freq_tuple = max(self.fft_dict.items(), key=operator.itemgetter(1))
        if max_freq_tuple[1] > RECOGNIZE_THRESH and max_freq_tuple[0] != self.last_max:
            self.last_max = max_freq_tuple[0]
            ret = self.ring_buf.add(freq_to_byte[self.last_max])
            if ret != None: self.callback(ret)

