#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>

using std::vector;

namespace py = pybind11;

int volMeter(vector<int>& input, int input_size);

vector<int> switchCH(vector<int>& input, int channel_size, int input_size);

PYBIND11_MODULE(operations, m){
    m.doc() = "The operations for audio";
    // define all classes
    // define all standalone functions
    m.def("volMeter", &volMeter, "Calculate volume of current input frame");
    m.def("switchCH", &switchCH, "Switch two channel data of current input frame");
}