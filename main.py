import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import psutil
import sqlite3
import time

# Создаем или открываем базу данных SQLite и создаем таблицу, если она еще не существует
conn = sqlite3.connect('cpu_usage.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS cpu_usage (
    timestamp REAL,
    cpu_percent REAL
)
''')
conn.commit()

# Определение интерфейса пользователя PySimpleGUI
layout = [
    [sg.Text('Real-time CPU Usage Graph')],
    [sg.Canvas(key='-CANVAS-')],
    [sg.Text('Update Interval:'), sg.Combo(['1', '10', '60'], default_value='1', key='-INTERVAL-')],
    [sg.Button('Start', key='-START-'), sg.Button('Stop', key='-STOP-')]
]

window = sg.Window('CPU Usage Monitor', layout, finalize=True)
canvas_elem = window['-CANVAS-']

# Создаем фигуру и оси matplotlib один раз
fig, ax = plt.subplots()
fig_agg = None

# Инициализируем список для хранения данных загрузки CPU
cpu_usage_data = []

def log_cpu_usage(cpu_percent):
    """Функция для записи загрузки CPU в базу данных."""
    timestamp = time.time()
    c.execute("INSERT INTO cpu_usage (timestamp, cpu_percent) VALUES (?, ?)", (timestamp, cpu_percent))
    conn.commit()

def draw_chart(fig, ax, cpu_usage_data):
    """Функция для перерисовки графика с новыми данными."""
    ax.clear()
    ax.plot(cpu_usage_data, '-o', markersize=2)
    ax.set_ylim(0, 100)
    ax.set_xlabel('Measurements')
    ax.set_ylabel('CPU Usage %')
    global fig_agg
    if fig_agg:
        fig_agg.draw_idle()  # Используем draw_idle для обновления существующего графика
    else:
        # Первоначальное создание графика
        fig_agg = FigureCanvasTkAgg(fig, canvas_elem.TKCanvas)
        fig_agg.draw()
        fig_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

monitoring = False
last_update_time = time.time()
update_interval = 1  # Интервал обновления в секундах

while True:
    event, values = window.read(timeout=10)
    if event == sg.WIN_CLOSED:
        break
    elif event == '-START-':
        monitoring = True
        cpu_usage_data.clear()
    elif event == '-STOP-':
        monitoring = False

    # Обновляем интервал обновления на основе выбора пользователя
    update_interval = int(values['-INTERVAL-'])

    # Проверяем, пора ли обновить график
    if monitoring and (time.time() - last_update_time) >= update_interval:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_usage_data.append(cpu_percent)
        log_cpu_usage(cpu_percent)
        draw_chart(fig, ax, cpu_usage_data)
        last_update_time = time.time()

window.close()
conn.close()
