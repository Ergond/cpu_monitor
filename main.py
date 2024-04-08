import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import psutil
import sqlite3
import threading
import time

# Инициализация базы данных
conn = sqlite3.connect('cpu_usage.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS cpu_usage (
    timestamp TEXT,
    cpu_percent REAL
)
''')
conn.commit()

def log_cpu_usage(cpu_percent):
    """Запись данных использования CPU в базу данных."""
    timestamp = time.time()
    c.execute("INSERT INTO cpu_usage (timestamp, cpu_percent) VALUES (?, ?)", (timestamp, cpu_percent))
    conn.commit()

def cpu_monitor(interval, window):
    """Функция мониторинга CPU и отправки данных в главный поток."""
    while True:
        cpu_percent = psutil.cpu_percent(interval=None)
        log_cpu_usage(cpu_percent)
        window.write_event_value('-CPU-', cpu_percent)
        time.sleep(interval)

def draw_figure(canvas, figure):
    """Добавление графика matplotlib в элемент Canvas PySimpleGUI."""
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

# Определение макета GUI
layout = [
    [sg.Text('Real-time CPU Usage Graph')],
    [sg.Canvas(key='-CANVAS-')],
    [sg.Text('Update Interval:'), sg.Combo(['1 second', '10 seconds', '1 minute'], default_value='1 second', key='-INTERVAL-')],
    [sg.Button('Start', key='-START-'), sg.Button('Stop', key='-STOP-')]
]

window = sg.Window('CPU Usage Monitor', layout, finalize=True)
canvas_elem = window['-CANVAS-']
canvas = canvas_elem.TKCanvas

# Настройка графика matplotlib
fig, ax = plt.subplots()
ax.set_xlabel('Time')
ax.set_ylabel('CPU Usage (%)')
ax.set_ylim(0, 100)

monitor_thread = None
cpu_usage_data = []

# Обработка событий окна
while True:
    event, values = window.read(timeout=100)

    if event == sg.WINDOW_CLOSED:
        break
    elif event == '-CPU-':
        cpu_usage_data.append(values[event])
        ax.clear()
        ax.plot(cpu_usage_data, label='CPU Usage')
        ax.legend()
        draw_figure(canvas, fig)
    elif event == '-START-':
        if monitor_thread is None or not monitor_thread.is_alive():
            intervals = {'1 second': 1, '10 seconds': 10, '1 minute': 60}.get(values['-INTERVAL-'], 1)
            monitor_thread = threading.Thread(target=cpu_monitor, args=(intervals, window), daemon=True)
            monitor_thread.start()
    elif event == '-STOP-' and monitor_thread:
        monitor_thread.join(timeout=0.1)

window.close()
conn.close()
