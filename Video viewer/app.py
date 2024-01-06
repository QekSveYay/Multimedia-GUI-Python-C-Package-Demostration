import PySimpleGUI as sg
import cv2
import numpy as np
import matplotlib.pyplot as plt
from embededMatplotlib import draw_figure, update_figure
# local user-defined package
import pb11_operations.operations as ops

frame = [
    [sg.Canvas(key = '-B_CANVAS-'),
     sg.Canvas(key = '-G_CANVAS-'),
     sg.Canvas(key = '-R_CANVAS-')]
]
layout = [
    [sg.Text('Image Info: ', key = '-IMAGE TEXT-', expand_x = True, justification = 'c')],
    [sg.Image(key = '-IMAGE-')],
    [sg.Text('People in picture: 0', key = '-PEOPLE TEXT-', expand_x = True, justification = 'c')],
    [sg.Frame('Histogram Frame', frame, title_color='blue')]
]

window = sg.Window('Face Detector', layout, finalize=False)

# get camera video
video = cv2.VideoCapture(0)
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# create matplotlib figure and place canvas on top of image
fig_b = plt.Figure(figsize=(4,3))
fig_b.suptitle('B histogram')
ax_b = fig_b.add_subplot(111)
fig_b_agg = draw_figure(window['-B_CANVAS-'].TKCanvas, fig_b)
fig_g = plt.Figure(figsize=(4,3))
fig_g.suptitle('G histogram')
ax_g = fig_g.add_subplot(111)
fig_g_agg = draw_figure(window['-G_CANVAS-'].TKCanvas, fig_g)
fig_r = plt.Figure(figsize=(4,3))
fig_r.suptitle('R histogram')
ax_r = fig_r.add_subplot(111)
fig_r_agg = draw_figure(window['-R_CANVAS-'].TKCanvas, fig_r)

while True:
    event, values = window.read(timeout=0)
    if event == sg.WIN_CLOSED:
        break
    _, frame = video.read()

    # calculate B/G/R histogram
    b_frame, g_frame, r_frame = cv2.split(frame)

    b_frame = b_frame.astype(int)
    (H, W) = b_frame.shape[:2]
    b_list = list(b_frame.flatten())
    b_hist = ops.histCalculate(b_list, H, W)
    g_frame = g_frame.astype(int)
    (H, W) = g_frame.shape[:2]
    g_list = list(g_frame.flatten())
    g_hist = ops.histCalculate(g_list, H, W)
    r_frame = r_frame.astype(int)
    (H, W) = r_frame.shape[:2]
    r_list = list(r_frame.flatten())
    r_hist = ops.histCalculate(r_list, H, W)

    # update histogram figures
    ax_b.cla()
    ax_g.cla()
    ax_r.cla()
    update_figure(b_hist, fig_b)
    update_figure(g_hist, fig_g)
    update_figure(r_hist, fig_r)
    fig_b_agg.draw()
    fig_g_agg.draw()
    fig_r_agg.draw()

    # The following steps are procedures that transfer opencv frame format to 1-D C++ vector format,
    # corresponding C++ codes can be found in pb11_operations directory.
    # transfer opencv frame(BGR) into 1-D integer list
    int_frame = list(frame.flatten().astype(int))
    # call C++ frame operation module to perform left/right reverse
    reversed_flatten_frame = ops.frameReverse(int_frame, H, W)
    # covert result frame into uint8 type
    result_frame = np.array(reversed_flatten_frame, dtype='uint8')
    # transfer back to opencv frame format
    reversed_frame = result_frame.reshape(H, W, 3)

    # human face detection processing
    gray = cv2.cvtColor(reversed_frame,cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor = 1.3,
        minNeighbors = 7,
        minSize = (50,50)
    )

    # draw the rectangles
    for (x, y, w, h) in faces:
        cv2.rectangle(reversed_frame,(x,y),(x+w,y+h),(0,255,0),2)

    # update the image
    imgbytes = cv2.imencode('.png', reversed_frame)[1].tobytes()
    window['-IMAGE-'].update(data = imgbytes)

    # update the text
    window['-IMAGE TEXT-'].update(f'Image Info: {H} x {W}')
    window['-PEOPLE TEXT-'].update(f'People in picture:{len(faces)}')

window.close()
