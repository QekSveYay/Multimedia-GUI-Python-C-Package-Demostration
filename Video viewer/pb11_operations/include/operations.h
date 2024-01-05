#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
using std::vector;

namespace py = pybind11;

int add(int i, int j);

int minus(int i, int j);

vector<int> histCalculate(vector<int>& frame, int H, int W);

vector<int> frameReverse(vector<int>& frame, int H, int W);

PYBIND11_MODULE(operations, m) {
    m.doc() = "The operations for int";
    // define all classes
    // define all standalone functions
    m.def("add", &add, "Add operation");
    m.def("minus", &minus, "Minus operation");
    m.def("histCalculate", &histCalculate, "Histogram calculate operation");
    m.def("frameReverse", &frameReverse, "Frame reverse");
}