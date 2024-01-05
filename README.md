This project includes video/image/audio Python GUI development tools.
Each of them is composed by three parts:
1. Graphic User Interface viewer: I implemented GUI using PySimpleGUI.
2. Specific Python package in C++ codes: User-defined operations are written in C/C++ codes and packed as Python package using Pybind11.
3. Multimedia data format converter: I transfered Python image/video/audio format(opencv/pyaudio) into 1-D Python list format, then mapped it to C++ vector array. After processing by specific C++ codes, the multimedia data is transfered inversely.
