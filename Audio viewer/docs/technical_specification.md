# Technical Specification

## Project Overview
This repository contains a Python-based audio viewer/player with optional GUI and a C++ extension for audio processing.
The key components include:

- `app.py`: Command-line audio playback with metering and channel switching.
- `app_gui.py`: PySimpleGUI-based GUI wrapper around audio playback, displaying waveform and playback controls.
- `pb11_operations/`: pybind11 C++ extension providing `volMeter` and `switchCH` functions.

The project targets macOS (ARM M1) and uses `sounddevice` for cross-platform audio output.

## Current Status
- **Build/packaging**: `pb11_operations/setup.py` corrected with necessary compile flags (e.g. `-std=c++17`).
- **CLI mode**: `app.py` supports playing WAV files with chunk-based processing, exception handling, logging, and volume metering via the C++ extension.
- **GUI mode** (`app_gui.py`): fully functional
  - File browser, playback controls (Play/Pause/Stop/Exit).
  - Waveform display with downsampled data.
  - Moving red marker indicating current playback position.
  - Progress bar, time display, and volume indicator.
  - Threaded, non-blocking playback using `sounddevice` and elapsed-time tracking.
  - Robust state management and cleanup.
- **Dependencies**: `PySimpleGUI`, `numpy`, `sounddevice`, `wave`, `pb11_operations` extension.
- **Environment**: Conda/miniforge environments; sounddevice installed in active env (`sd_m1_env`).

## Architecture
1. **AudioFile** (in Python)
   - Manages file reading, state, volume meter and channel switch via C++.
   - Supports play/pause/stop with thread-safe state locking.
   - Plays audio using `sounddevice` in non-blocking mode.
2. **AudioPlayerGUI**
   - Builds GUI layout with `sg.Graph` for waveform.
   - Loads and normalizes waveform data on file selection.
   - Keeps `waveform`, `marker`, and `graph` references.
   - Updates UI periodically (100ms timeout) while playback is active.
   - Handles user events and drives playback thread.
3. **pybind11 Extension**
   - `volMeter`: computes volume level for a chunk of samples.
   - `switchCH`: swaps stereo channels when necessary.

## Key Design Decisions
- **Sounddevice over PyAudio**: resolved Mac M1 compatibility issues.
- **Non-blocking playback + timer**: ensures UI remains responsive and marker moves correctly.
- **Downsampling waveform**: limits graph points to ~1000 for performance.
- **Thread-safe state**: using locks to manage playback states.
- **Graceful error handling**: catch file, wave, and audio device errors.

## Remaining Work & Future Enhancements
- Add seeking capability in GUI (click/drag marker).
- Support additional audio formats (e.g., MP3, FLAC) via `pydub` or `soundfile`.
- Export/import playback annotations or markers.
- Add logging configuration and CLI options for GUI mode.
- Package as a PyPI distributable with entry points.

## Development Notes
- Python 3.10/3.11 recommended.
- Use `python -m pip install -e .` in `pb11_operations` to compile extension.
- Run CLI: `python app.py <file.wav>`.
- Run GUI: `python app_gui.py` (optionally `--verbose` or `--no-gui`).

---
*Document generated 2026-03-13.*
