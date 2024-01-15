# Multimedia GUI Python with C/C++ package demonstration

This project includes video/image/audio Python GUI development tools.
Each of them is composed by three parts:
1. Graphic User Interface viewer: GUI is implemented in PySimpleGUI.
2. Specific Python package in C++ codes: User-defined operations are written in C/C++ codes and packed as Python package in Pybind11.
3. Multimedia data format converter: Transfer Python image/video/audio format(opencv/pyaudio) into 1-D Python list format, then map it to C++ vector array. After processing by specific C++ codes, the multimedia data is transfered inversely. This implementation keeps things as simple as possible. You can find more memory security method in [1].

# Reference

[1] Pybind11 Documentation - https://pybind11.readthedocs.io/en/stable/index.html

## TODO

* Demonstrate more GUI functions for multimedia usage in PySimpleGUI.
* Update more multimedia data transmission between Python and C/C++.
