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
import threading
import time
import sounddevice as sd
import wave
import numpy as np
from enum import Enum

import pb11_operations.operations as ops

try:
    import PySimpleGUI as sg
    HAS_GUI = True
except ImportError:
    HAS_GUI = False


class PlaybackState(Enum):
    """Enumeration for playback states."""
    IDLE = 0
    PLAYING = 1
    PAUSED = 2
    STOPPED = 3


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
        
        # Playback control flags
        self.state = PlaybackState.IDLE
        self._state_lock = threading.Lock()
        self.current_frame = 0
        self.total_frames = 0
        self.current_volume = 0
        
        try:
            self.wf = wave.open(filepath, 'rb')
        except Exception:
            logging.exception("Failed to open wave file")
            raise

        self.FS = self.wf.getframerate()
        self.CH_SIZE = self.wf.getnchannels()
        self.SAMPWIDTH = self.wf.getsampwidth()
        self.total_frames = self.wf.getnframes()
        self.duration_seconds = self.total_frames / self.FS

        # sounddevice doesn't need explicit stream initialization
        # We'll play audio data directly using sd.play()

    def _set_state(self, state):
        """Thread-safe state setter."""
        with self._state_lock:
            self.state = state

    def _get_state(self):
        """Thread-safe state getter."""
        with self._state_lock:
            return self.state

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def play(self):
        """Play the entire file with basic processing.

        This method reads the entire file, processes it, and plays it using sounddevice.
        """
        self._set_state(PlaybackState.PLAYING)
        try:
            # Read entire file
            self.wf.rewind()
            raw_data = self.wf.readframes(self.total_frames)
            
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
        finally:
            self._set_state(PlaybackState.IDLE)

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
                self.current_volume = vol
                self.current_frame = i + len(chunk)
                logging.debug("volume: %s", vol)
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

    def pause(self):
        """Pause playback."""
        if self._get_state() == PlaybackState.PLAYING:
            self._set_state(PlaybackState.PAUSED)
            sd.stop()  # Stop current playback

    def resume(self):
        """Resume playback - not supported with sounddevice blocking play."""
        logging.warning("Resume not supported with current sounddevice implementation")

    def stop(self):
        """Stop playback."""
        self._set_state(PlaybackState.STOPPED)
        sd.stop()  # Stop any current playback

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


def format_time(seconds):
    """Format seconds to MM:SS string."""
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins:02d}:{secs:02d}"


class AudioPlayerGUI:
    """Simple PySimpleGUI-based audio player."""

    def __init__(self):
        self.audio_file = None
        self.playback_thread = None
        self.window = None

    def create_window(self):
        """Create the GUI window."""
        sg.theme('DarkBlue2')

        layout = [
            [sg.Text('Audio Player', font=('Arial', 16, 'bold'))],
            [sg.Text('File:', size=(8, 1)), 
             sg.InputText(key='-FILE-', size=(40, 1)), 
             sg.FileBrowse(file_types=(('WAV Files', '*.wav'), ('All Files', '*.*')))],
            [sg.Text('', size=(60, 1), key='-PATH_DISPLAY-')],
            [sg.ProgressBar(100, orientation='h', size=(50, 20), key='-PROGRESS-')],
            [sg.Text('00:00 / 00:00', key='-TIME-', size=(15, 1))],
            [sg.Text('Volume: 0', key='-VOLUME-', size=(20, 1))],
            [sg.Button('Play', size=(8, 1)), 
             sg.Button('Pause', size=(8, 1)), 
             sg.Button('Stop', size=(8, 1)), 
             sg.Button('Exit', size=(8, 1))],
        ]

        self.window = sg.Window('Audio Viewer', layout)

    def update_ui(self):
        """Update UI with current playback info."""
        if self.audio_file is None:
            return

        current_sec = self.audio_file.current_frame / self.audio_file.FS
        progress = (current_sec / self.audio_file.duration_seconds * 100) if self.audio_file.duration_seconds > 0 else 0
        
        self.window['-PROGRESS-'].update(progress)
        self.window['-TIME-'].update(
            f"{format_time(current_sec)} / {format_time(self.audio_file.duration_seconds)}"
        )
        self.window['-VOLUME-'].update(f"Volume: {self.audio_file.current_volume}")

    def run(self):
        """Run the GUI event loop."""
        self.create_window()

        while True:
            event, values = self.window.read(timeout=100)

            # Always update UI while audio is playing
            if self.audio_file is not None and self.playback_thread is not None:
                self.update_ui()

            if event == sg.WINDOW_CLOSED or event == 'Exit':
                break

            if event == 'Play':
                file_path = values['-FILE-']
                if not file_path:
                    sg.PopupError('Please select an audio file')
                    continue

                # If already playing, do nothing
                if self.audio_file is not None and self.playback_thread is not None and self.playback_thread.is_alive():
                    state = self.audio_file._get_state()
                    if state == PlaybackState.PLAYING:
                        sg.PopupInfo('Already playing')
                        continue
                    elif state == PlaybackState.PAUSED:
                        self.audio_file.resume()
                        continue

                # Load new file
                try:
                    if self.audio_file is not None:
                        self.audio_file.close()
                    
                    self.audio_file = AudioFile(file_path)
                    self.window['-PATH_DISPLAY-'].update(f'Loaded: {os.path.basename(file_path)}')
                    
                    # Start playback in a thread
                    self.playback_thread = threading.Thread(target=self.audio_file.play, daemon=True)
                    self.playback_thread.start()
                except FileNotFoundError:
                    sg.PopupError(f'File not found: {file_path}')
                except Exception as e:
                    sg.PopupError(f'Error loading file: {str(e)}')
                    logging.exception('Error loading file')

            elif event == 'Pause':
                if self.audio_file is not None:
                    self.audio_file.pause()
                    sg.PopupInfo('Paused')

            elif event == 'Stop':
                if self.audio_file is not None:
                    self.audio_file.stop()
                    if self.playback_thread is not None:
                        self.playback_thread.join(timeout=1)
                    self.audio_file.close()
                    self.audio_file = None
                    self.window['-PROGRESS-'].update(0)
                    self.window['-TIME-'].update('00:00 / 00:00')
                    self.window['-VOLUME-'].update('Volume: 0')
                    self.window['-PATH_DISPLAY-'].update('')

        self.window.close()
        if self.audio_file is not None:
            self.audio_file.stop()
            self.audio_file.close()


def _build_arg_parser():
    p = argparse.ArgumentParser(description='Audio viewer / player with GUI')
    p.add_argument('file', nargs='?', default=None, help='Path to WAV file (optional, use GUI file browser if not provided)')
    p.add_argument('--chunk', type=int, default=AudioFile.DEFAULT_CHUNK, help='Chunk size in frames')
    p.add_argument('--verbose', action='store_true', help='Enable debug logging')
    p.add_argument('--no-gui', action='store_true', help='Run in CLI mode')
    return p


def run_cli_mode(file_path, chunk_size):
    """Run in CLI (non-GUI) mode."""
    try:
        with AudioFile(file_path, chunk_size=chunk_size) as af:
            af.play()
    except FileNotFoundError:
        logging.error('File not found: %s', file_path)
    except wave.Error:
        logging.error('Invalid WAV file: %s', file_path)
    except Exception:
        logging.exception('Failed to play audio')


if __name__ == '__main__':
    if not HAS_GUI:
        print("PySimpleGUI not installed. Install with: pip install PySimpleGUI")
        exit(1)

    args = _build_arg_parser().parse_args()
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')

    if args.no_gui or not HAS_GUI:
        if args.file is None:
            print("Error: --no-gui mode requires a file argument")
            exit(1)
        run_cli_mode(args.file, args.chunk)
    else:
        gui = AudioPlayerGUI()
        if args.file:
            gui.window = sg.Window('Audio Viewer', [[sg.Text('Loading...')]])
            gui.window.read(timeout=1)
            gui.window.close()
        gui.run()
