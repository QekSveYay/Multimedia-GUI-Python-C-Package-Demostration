# Copyright (C) 2024 by CHANG, Wei-Chen

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import pyaudio
import wave
import numpy as np

import pb11_operations.operations as ops

class AudioFile:
    CHUNK_SIZE = 1024

    def __init__(self, file):
        """ Init audio stream """
        self.wf = wave.open(file, 'rb')
        self.FS = self.wf.getframerate()
        self.CH_SIZE = self.wf.getnchannels()
        self.SAMPWIDTH = self.wf.getsampwidth()
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format = self.p.get_format_from_width(self.SAMPWIDTH),
            channels = self.CH_SIZE,
            rate = self.FS,
            output = True
        )

    def play(self):
        """ Play entire file """
        data = self.wf.readframes(self.CHUNK_SIZE)

        while data != b'':
            np_indata = np.frombuffer(data, dtype='int16')
            list_indata = list(np_indata)
            # de-interleave, select channel 1
            channel0 = list(np_indata[0::self.CH_SIZE])
            # channel0 = self.af.process(channel0, 1024)
            vol = ops.volMeter(channel0, self.CHUNK_SIZE)
            print('volume: ', vol)
            # switch stereo input
            list_outdata = ops.switchCH(list_indata, self.CH_SIZE, self.CHUNK_SIZE)
            # transfer list data to numpy data
            outdata = np.array(list_outdata, dtype='int16').tobytes()

            # send data to stream playback
            self.stream.write(outdata)
            # receive next data chunk
            data = self.wf.readframes(self.CHUNK_SIZE)

    def close(self):
        """ Graceful shutdown """
        self.stream.close()
        self.p.terminate()

# Usage example for pyaudio
a = AudioFile("test.wav")
a.play()
a.close()