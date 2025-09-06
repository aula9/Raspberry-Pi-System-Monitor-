# -*- coding: utf-8 -*-
"""
Raspberry Pi System Monitor
A real-time monitoring tool for tracking system performance on Raspberry Pi
Features:
- Live CPU, RAM, and temperature monitoring
- Visual graphs with historical data
- Data export to CSV
- Dark theme UI optimized for Raspberry Pi displays
"""

import sys, psutil, os, collections, csv, datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QProgressBar, QPushButton, QFileDialog, 
                             QGroupBox, QGridLayout, QFrame)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPalette, QColor
import pyqtgraph as pg

class SystemMonitor(QWidget):
    def __init__(self):
        super().__init__()
        # Window setup
        self.setWindowTitle("Raspberry Pi System Monitor")
        self.setGeometry(100, 100, 800, 700)
        
        # Apply dark theme for better visibility
        self.apply_dark_theme()
        
        # Setup main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Application title
        title = QLabel("Raspberry Pi System Monitor")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2E86AB; padding: 10px;")
        main_layout.addWidget(title)
        
        # Create metric groups using grid layout
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        
        # CPU performance group
        cpu_group = QGroupBox("CPU Performance")
        cpu_group.setFont(QFont("Arial", 12, QFont.Bold))
        cpu_layout = QVBoxLayout()
        
        self.cpu_label = QLabel("CPU Usage: 0%")
        self.cpu_label.setFont(QFont("Arial", 10))
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setTextVisible(True)
        self.cpu_bar.setFormat("%v%")
        
        cpu_layout.addWidget(self.cpu_label)
        cpu_layout.addWidget(self.cpu_bar)
        cpu_group.setLayout(cpu_layout)
        
        # RAM performance group
        ram_group = QGroupBox("Memory Performance")
        ram_group.setFont(QFont("Arial", 12, QFont.Bold))
        ram_layout = QVBoxLayout()
        
        self.ram_label = QLabel("Memory Usage: 0%")
        self.ram_label.setFont(QFont("Arial", 10))
        self.ram_bar = QProgressBar()
        self.ram_bar.setTextVisible(True)
        self.ram_bar.setFormat("%v%")
        
        ram_layout.addWidget(self.ram_label)
        ram_layout.addWidget(self.ram_bar)
        ram_group.setLayout(ram_layout)
        
        # Temperature monitoring group
        temp_group = QGroupBox("CPU Temperature")
        temp_group.setFont(QFont("Arial", 12, QFont.Bold))
        temp_layout = QVBoxLayout()
        
        self.temp_label = QLabel("Temperature: 0°C")
        self.temp_label.setFont(QFont("Arial", 10))
        self.temp_bar = QProgressBar()
        self.temp_bar.setTextVisible(True)
        self.temp_bar.setFormat("%v°C")
        self.temp_bar.setMaximum(100)
        
        temp_layout.addWidget(self.temp_label)
        temp_layout.addWidget(self.temp_bar)
        temp_group.setLayout(temp_layout)
        
        # Add groups to grid layout
        grid_layout.addWidget(cpu_group, 0, 0)
        grid_layout.addWidget(ram_group, 0, 1)
        grid_layout.addWidget(temp_group, 1, 0)
        
        main_layout.addLayout(grid_layout)
        
        # Live graphs for historical data
        graph_layout = QHBoxLayout()
        
        self.cpu_plot = pg.PlotWidget(title="CPU Usage (%)")
        self.cpu_plot.setBackground('#2B2B2B')
        self.cpu_plot.setYRange(0, 100)
        self.cpu_plot.setLabel('left', 'Percentage (%)')
        self.cpu_plot.setLabel('bottom', 'Time')
        self.cpu_plot.setMinimumHeight(200)
        
        self.ram_plot = pg.PlotWidget(title="Memory Usage (%)")
        self.ram_plot.setBackground('#2B2B2B')
        self.ram_plot.setYRange(0, 100)
        self.ram_plot.setLabel('left', 'Percentage (%)')
        self.ram_plot.setLabel('bottom', 'Time')
        self.ram_plot.setMinimumHeight(200)
        
        graph_layout.addWidget(self.cpu_plot)
        graph_layout.addWidget(self.ram_plot)
        
        main_layout.addLayout(graph_layout)
        
        # Temperature graph
        self.temp_plot = pg.PlotWidget(title="CPU Temperature (°C)")
        self.temp_plot.setBackground('#2B2B2B')
        self.temp_plot.setYRange(0, 100)
        self.temp_plot.setLabel('left', 'Temperature (°C)')
        self.temp_plot.setLabel('bottom', 'Time')
        self.temp_plot.setMinimumHeight(200)
        main_layout.addWidget(self.temp_plot)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Data")
        self.save_button.setFont(QFont("Arial", 10))
        self.save_button.clicked.connect(self.save_data)
        self.save_button.setStyleSheet("QPushButton { background-color: #2E86AB; color: white; border: none; padding: 8px; border-radius: 4px; }"
                                      "QPushButton:hover { background-color: #1B6B93; }")
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setFont(QFont("Arial", 10))
        self.pause_button.setCheckable(True)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setStyleSheet("QPushButton { background-color: #A23B72; color: white; border: none; padding: 8px; border-radius: 4px; }"
                                       "QPushButton:checked { background-color: #7A2A58; }")
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)

        # Data storage for metrics
        self.timestamps = collections.deque(maxlen=3600)  # Store up to 1 hour of data
        self.cpu_data = collections.deque(maxlen=3600)
        self.ram_data = collections.deque(maxlen=3600)
        self.temp_data = collections.deque(maxlen=3600)

        # Setup plot curves
        self.cpu_curve = self.cpu_plot.plot(pen=pg.mkPen('#18A558', width=2))
        self.ram_curve = self.ram_plot.plot(pen=pg.mkPen('#3498DB', width=2))
        self.temp_curve = self.temp_plot.plot(pen=pg.mkPen('#E74C3C', width=2))

        # Timer for periodic updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)  # Update every second
        
        # Pause state
        self.paused = False

    def apply_dark_theme(self):
        """Apply a dark theme palette for better visibility on Raspberry Pi displays"""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(40, 40, 40))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Highlight, QColor(46, 134, 171))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setPalette(dark_palette)
        
        # Additional styling
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2E86AB;
            }
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                font: bold 12px;
                height: 20px;
            }
        """)

    def get_cpu_temp(self):
        """Read CPU temperature from system command"""
        try:
            res = os.popen("vcgencmd measure_temp").readline()
            temp_str = res.replace("temp=","").replace("'C\n","")
            return float(temp_str)
        except:
            return None

    def style_bar(self, bar, value, safe, warn):
        """Style progress bars based on value thresholds"""
        if value <= safe:
            color = "#18A558"  # Green
        elif value <= warn:
            color = "#F39C12"  # Orange
        else:
            color = "#E74C3C"  # Red
            
        bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                font: bold 12px;
                color: white;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                width: 1px;
            }}
        """)

    def update_stats(self):
        """Update all metrics and visualizations"""
        if self.paused:
            return
            
        # Get current system metrics
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        temp = self.get_cpu_temp()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update labels and progress bars
        self.cpu_label.setText(f"CPU Usage: {cpu}%")
        self.cpu_bar.setValue(int(cpu))
        self.style_bar(self.cpu_bar, cpu, 50, 80)

        self.ram_label.setText(f"Memory Usage: {ram}%")
        self.ram_bar.setValue(int(ram))
        self.style_bar(self.ram_bar, ram, 50, 80)

        if temp is not None:
            self.temp_label.setText(f"Temperature: {temp}°C")
            self.temp_bar.setValue(int(temp))
            self.style_bar(self.temp_bar, temp, 50, 70)
        else:
            self.temp_label.setText("Temperature: N/A")
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

    def toggle_pause(self, checked):
        """Toggle between paused and running states"""
        self.paused = checked
        if checked:
            self.pause_button.setText("Resume")
        else:
            self.pause_button.setText("Pause")

    def save_data(self):
        """Export monitoring data to CSV file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Monitoring Data", 
            f"system_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Timestamp", "CPU Usage (%)", "Memory Usage (%)", "Temperature (°C)"])
                    for ts, cpu, ram, temp in zip(self.timestamps, self.cpu_data, self.ram_data, self.temp_data):
                        writer.writerow([ts, cpu, ram, temp])
                print(f"Data saved to: {file_path}")
            except Exception as e:
                print(f"Error saving file: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemMonitor()
    window.show()
    sys.exit(app.exec_())
