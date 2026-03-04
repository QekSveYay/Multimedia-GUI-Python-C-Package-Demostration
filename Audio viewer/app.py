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

import os
import argparse
import logging
import pyaudio
import wave
import numpy as np

import pb11_operations.operations as ops


class AudioFile:
    DEFAULT_CHUNK = 1024

    def __init__(self, filepath, chunk_size=None):
        """Initialize audio stream and related resources.

        Raises FileNotFoundError or wave.Error on invalid input file.
        Raises OSError on audio device errors.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Audio file not found: {filepath}")

        self.filepath = filepath
        self.CHUNK_SIZE = chunk_size or self.DEFAULT_CHUNK
        try:
            self.wf = wave.open(filepath, 'rb')
        except Exception:
            logging.exception("Failed to open wave file")
            raise

        self.FS = self.wf.getframerate()
        self.CH_SIZE = self.wf.getnchannels()
        self.SAMPWIDTH = self.wf.getsampwidth()

        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(
                format=self.p.get_format_from_width(self.SAMPWIDTH),
                channels=self.CH_SIZE,
                rate=self.FS,
                output=True
            )
        except Exception:
            # Ensure wave file is closed on failure to init audio
            try:
                self.wf.close()
            except Exception:
                pass
            logging.exception("Failed to initialize PyAudio stream")
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def play(self):
        """Play the entire file in chunks with basic processing.

        This method logs volume and attempts to use the pybind11 operations.
        Any processing errors fall back to playing the original audio data.
        """
        try:
            while True:
                data = self.wf.readframes(self.CHUNK_SIZE)
                if not data:
                    break

                # Interpret raw bytes as int16 samples
                try:
                    np_indata = np.frombuffer(data, dtype=np.int16)
                except Exception:
                    logging.exception("Failed to interpret audio frame as int16")
                    self.stream.write(data)
                    continue

                # De-interleave: select first channel (channel 0)
                channel0 = np_indata[0::self.CH_SIZE]

                # Compute volume (use safe conversion and error handling)
                try:
                    vol = ops.volMeter(channel0.tolist(), len(channel0))
                    logging.info("volume: %s", vol)
                except Exception:
                    logging.exception("volMeter failed")

                # Try to process switching channels; if it fails, play original
                try:
                    list_indata = np_indata.tolist()
                    list_outdata = ops.switchCH(list_indata, self.CH_SIZE, self.CHUNK_SIZE)
                    outdata = np.array(list_outdata, dtype=np.int16).tobytes()
                except Exception:
                    logging.exception("switchCH failed; playing original frame")
                    outdata = data

                try:
                    self.stream.write(outdata)
                except Exception:
                    logging.exception("Stream write failed")
                    break

        except Exception:
            logging.exception("Unexpected error during playback")
            raise

    def close(self):
        """Graceful shutdown of audio resources."""
        try:
            if hasattr(self, 'stream') and self.stream is not None:
                try:
                    self.stream.stop_stream()
                except Exception:
                    pass
                try:
                    self.stream.close()
                except Exception:
                    pass
        finally:
            try:
                if hasattr(self, 'p') and self.p is not None:
                    self.p.terminate()
            except Exception:
                pass

        try:
            if hasattr(self, 'wf') and self.wf is not None:
                self.wf.close()
        except Exception:
            pass


def _build_arg_parser():
    p = argparse.ArgumentParser(description='Simple audio viewer / player')
    p.add_argument('file', nargs='?', default='test.wav', help='Path to WAV file')
    p.add_argument('--chunk', type=int, default=AudioFile.DEFAULT_CHUNK, help='Chunk size in frames')
    p.add_argument('--verbose', action='store_true', help='Enable debug logging')
    return p


if __name__ == '__main__':
    args = _build_arg_parser().parse_args()
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')

    try:
        with AudioFile(args.file, chunk_size=args.chunk) as af:
            af.play()
    except FileNotFoundError:
        logging.error('File not found: %s', args.file)
    except wave.Error:
        logging.error('Invalid WAV file: %s', args.file)
    except Exception:
        logging.exception('Failed to play audio')