from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#matplotlib.use("TkAgg")

def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    #figure_canvas_agg.get_tk_widget().pack(side="top", fill="both", expand=1)
    figure_canvas_agg.get_tk_widget().pack(side="top")
    return figure_canvas_agg

def update_figure(data, figure):
    axes = figure.axes
    x = [i for i in range(len(data))]
    y = [i for i in data]
    axes[0].plot(x, y, 'r-')