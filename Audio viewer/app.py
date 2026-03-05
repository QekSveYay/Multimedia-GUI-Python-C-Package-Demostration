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
import sounddevice as sd
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

        # sounddevice doesn't need explicit stream initialization

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def play(self):
        """Play the entire file with basic processing.

        This method reads the entire file, processes it, and plays it using sounddevice.
        """
        try:
            # Read entire file
            self.wf.rewind()
            raw_data = self.wf.readframes(self.wf.getnframes())
            
            # Convert to numpy array
            if self.SAMPWIDTH == 2:  # 16-bit
                dtype = np.int16
            elif self.SAMPWIDTH == 4:  # 32-bit
                dtype = np.int32
            else:
                dtype = np.int16  # default
            
            audio_data = np.frombuffer(raw_data, dtype=dtype)
            
            # Reshape to (frames, channels)
            audio_data = audio_data.reshape(-1, self.CH_SIZE)
            
            # Process audio data
            processed_data = self._process_audio_data(audio_data)
            
            # Convert back to proper format for sounddevice
            if processed_data.dtype != np.float32:
                # Normalize to float32 in range [-1, 1]
                if processed_data.dtype == np.int16:
                    processed_data = processed_data.astype(np.float32) / 32768.0
                elif processed_data.dtype == np.int32:
                    processed_data = processed_data.astype(np.float32) / 2147483648.0
            
            # Play the audio
            sd.play(processed_data, samplerate=self.FS, blocking=True)
            
        except Exception:
            logging.exception("Unexpected error during playback")
            raise

    def _process_audio_data(self, audio_data):
        """Process audio data with volume metering and channel switching."""
        processed_data = audio_data.copy()
        
        # Process in chunks for volume metering
        chunk_size = self.CHUNK_SIZE
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            
            # De-interleave: select first channel (channel 0) for volume
            if self.CH_SIZE > 1:
                channel0 = chunk[:, 0]
            else:
                channel0 = chunk[:, 0]
            
            # Compute volume
            try:
                vol = ops.volMeter(channel0.tolist(), len(channel0))
                logging.info("volume: %s", vol)
            except Exception:
                logging.exception("volMeter failed")
            
            # Try to process channel switching
            try:
                if self.CH_SIZE == 2:  # Stereo
                    # Switch channels
                    chunk_list = chunk.tolist()
                    switched = []
                    for sample in chunk_list:
                        switched.append([sample[1], sample[0]])  # swap L/R
                    processed_data[i:i+len(chunk)] = np.array(switched)
            except Exception:
                logging.exception("switchCH failed; using original")
        
        return processed_data

    def close(self):
        """Graceful shutdown of audio resources."""
        try:
            sd.stop()  # Stop any playing audio
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