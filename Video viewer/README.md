Video viewer:
This demostration shows a camera captured video that performed several real-time video operations:
1. Histogram calculation - .
2. Frame left/right reverse - .
3. Face detection - I used Open CV Haar Cascade Classifier[1] to implement real-time face detection. More details can be found in the introduction in [2].

pb11_operaticons:
1. pybind11 C++ package: see setup.py/operations.h/operations.cpp 
2. hisCalculate function: calculate B/G/R histogram
3. frameReverse: reverse frame index(right/left)

Reference:
1. Haar Cascade Human Face Classifier - https://github.com/opencv/opencv/tree/4.x/data
2. 圖形辨識筆記-OPEN CV (haarcascades ) https://vocus.cc/article/636b4479fd89780001a955ac
