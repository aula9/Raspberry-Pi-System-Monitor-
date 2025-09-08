# -*- coding: utf-8 -*-
import sys, psutil, os, collections, csv, datetime
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QPushButton, QFileDialog
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont
import pyqtgraph as pg

class SystemMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Monitor with Live Graphs and Save")
        self.setGeometry(200, 200, 600, 550)

        layout = QVBoxLayout()

        # ===== CPU =====
        self.cpu_label = QLabel("CPU Usage:")
        self.cpu_label.setFont(QFont("Arial", 12))
        self.cpu_bar = QProgressBar()
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.cpu_bar)

        self.cpu_plot = pg.PlotWidget(title="CPU Usage (%)")
        self.cpu_plot.setYRange(0, 100)
        layout.addWidget(self.cpu_plot)

        # ===== RAM =====
        self.ram_label = QLabel("RAM Usage:")
        self.ram_label.setFont(QFont("Arial", 12))
        self.ram_bar = QProgressBar()
        layout.addWidget(self.ram_label)
        layout.addWidget(self.ram_bar)

        self.ram_plot = pg.PlotWidget(title="RAM Usage (%)")
        self.ram_plot.setYRange(0, 100)
        layout.addWidget(self.ram_plot)

        # ===== Temperature =====
        self.temp_label = QLabel("CPU Temperature:")
        self.temp_label.setFont(QFont("Arial", 12))
        self.temp_bar = QProgressBar()
        self.temp_bar.setMaximum(100)
        layout.addWidget(self.temp_label)
        layout.addWidget(self.temp_bar)

        self.temp_plot = pg.PlotWidget(title="CPU Temp (°C)")
        self.temp_plot.setYRange(0, 100)
        layout.addWidget(self.temp_plot)

        # ===== Save Button =====
        self.save_button = QPushButton("Save Data to CSV")
        self.save_button.clicked.connect(self.save_data)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

        # Data buffers
        self.timestamps = collections.deque(maxlen=3600)
        self.cpu_data = collections.deque(maxlen=3600)
        self.ram_data = collections.deque(maxlen=3600)
        self.temp_data = collections.deque(maxlen=3600)

        self.cpu_curve = self.cpu_plot.plot(pen=pg.mkPen('g', width=2))
        self.ram_curve = self.ram_plot.plot(pen=pg.mkPen('b', width=2))
        self.temp_curve = self.temp_plot.plot(pen=pg.mkPen('r', width=2))

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

    def get_cpu_temp(self):
        try:
            res = os.popen("vcgencmd measure_temp").readline()
            temp_str = res.replace("temp=","").replace("'C\n","")
            return float(temp_str)
        except:
            return None

    def style_bar(self, bar, value, safe, warn):
        if value <= safe:
            color = "green"
        elif value <= warn:
            color = "orange"
        else:
            color = "red"
        bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                font: bold 14px 'Arial';
                color: white;
                height: 28px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                width: 1px;
            }}
        """)

    def update_stats(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        temp = self.get_cpu_temp()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update bars
        self.cpu_bar.setValue(cpu)
        self.style_bar(self.cpu_bar, cpu, 50, 80)

        self.ram_bar.setValue(ram)
        self.style_bar(self.ram_bar, ram, 50, 80)

        if temp is not None:
            self.temp_bar.setValue(int(temp))
            self.style_bar(self.temp_bar, temp, 50, 70)
        else:
            self.temp_bar.setValue(0)
            self.temp_bar.setStyleSheet("QProgressBar::chunk { background-color: gray; }")

        # Append to data buffers
        self.timestamps.append(timestamp)
        self.cpu_data.append(cpu)
        self.ram_data.append(ram)
        self.temp_data.append(temp if temp is not None else 0)

        # Update graphs
        self.cpu_curve.setData(list(self.cpu_data))
        self.ram_curve.setData(list(self.ram_data))
        self.temp_curve.setData(list(self.temp_data))

    def save_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "CSV Files (*.csv)")
        if file_path:
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "CPU Usage (%)", "RAM Usage (%)", "CPU Temp (°C)"])
                for ts, cpu, ram, temp in zip(self.timestamps, self.cpu_data, self.ram_data, self.temp_data):
                    writer.writerow([ts, cpu, ram, temp])
            print(f"Data saved to {file_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemMonitor()
    window.show()
    sys.exit(app.exec_())
