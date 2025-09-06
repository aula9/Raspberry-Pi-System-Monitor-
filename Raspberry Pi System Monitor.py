# -*- coding: utf-8 -*-
"""
Raspberry Pi System Monitor - Compact Version
Optimized for small displays like the Raspberry Pi touchscreen
"""

import sys, psutil, os, collections, csv, datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QProgressBar, QPushButton, QFileDialog, 
                             QGroupBox, QGridLayout, QScrollArea)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPalette, QColor
import pyqtgraph as pg

# libEGL warning
os.environ['QT_XCB_GL_INTEGRATION'] = 'none'

class SystemMonitor(QWidget):
    def __init__(self):
        super().__init__()
        # Window setup for small displays
        self.setWindowTitle("Pi Monitor")
        self.setGeometry(50, 50, 480, 600)  # Smaller window size
        
        # Apply dark theme for better visibility
        self.apply_dark_theme()
        
        # Create scroll area for small screens
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        
        # Setup main layout for scroll content
        main_layout = QVBoxLayout(self.scroll_content)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Application title (smaller)
        title = QLabel("Pi System Monitor")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2E86AB; padding: 5px;")
        main_layout.addWidget(title)
        
        # Create metric groups using grid layout
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # CPU performance group
        cpu_group = QGroupBox("CPU")
        cpu_group.setFont(QFont("Arial", 10, QFont.Bold))
        cpu_layout = QVBoxLayout()
        
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setFont(QFont("Arial", 9))
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setTextVisible(True)
        self.cpu_bar.setFormat("%v%")
        self.cpu_bar.setMaximumHeight(20)
        
        cpu_layout.addWidget(self.cpu_label)
        cpu_layout.addWidget(self.cpu_bar)
        cpu_group.setLayout(cpu_layout)
        
        # RAM performance group
        ram_group = QGroupBox("RAM")
        ram_group.setFont(QFont("Arial", 10, QFont.Bold))
        ram_layout = QVBoxLayout()
        
        self.ram_label = QLabel("RAM: 0%")
        self.ram_label.setFont(QFont("Arial", 9))
        self.ram_bar = QProgressBar()
        self.ram_bar.setTextVisible(True)
        self.ram_bar.setFormat("%v%")
        self.ram_bar.setMaximumHeight(20)
        
        ram_layout.addWidget(self.ram_label)
        ram_layout.addWidget(self.ram_bar)
        ram_group.setLayout(ram_layout)
        
        # Temperature monitoring group
        temp_group = QGroupBox("Temp")
        temp_group.setFont(QFont("Arial", 10, QFont.Bold))
        temp_layout = QVBoxLayout()
        
        self.temp_label = QLabel("Temp: 0°C")
        self.temp_label.setFont(QFont("Arial", 9))
        self.temp_bar = QProgressBar()
        self.temp_bar.setTextVisible(True)
        self.temp_bar.setFormat("%v°C")
        self.temp_bar.setMaximum(100)
        self.temp_bar.setMaximumHeight(20)
        
        temp_layout.addWidget(self.temp_label)
        temp_layout.addWidget(self.temp_bar)
        temp_group.setLayout(temp_layout)
        
        # Add groups to grid layout
        grid_layout.addWidget(cpu_group, 0, 0)
        grid_layout.addWidget(ram_group, 0, 1)
        grid_layout.addWidget(temp_group, 1, 0)
        
        main_layout.addLayout(grid_layout)
        
        # Live graphs for historical data
        graph_layout = QVBoxLayout()
        
        self.cpu_plot = pg.PlotWidget(title="CPU %")
        self.cpu_plot.setBackground('#2B2B2B')
        self.cpu_plot.setYRange(0, 100)
        self.cpu_plot.setLabel('left', '%')
        self.cpu_plot.setMinimumHeight(120)
        
        self.ram_plot = pg.PlotWidget(title="RAM %")
        self.ram_plot.setBackground('#2B2B2B')
        self.ram_plot.setYRange(0, 100)
        self.ram_plot.setLabel('left', '%')
        self.ram_plot.setMinimumHeight(120)
        
        self.temp_plot = pg.PlotWidget(title="Temp °C")
        self.temp_plot.setBackground('#2B2B2B')
        self.temp_plot.setYRange(0, 100)
        self.temp_plot.setLabel('left', '°C')
        self.temp_plot.setMinimumHeight(120)
        
        # Add graphs to layout
        graph_layout.addWidget(self.cpu_plot)
        graph_layout.addWidget(self.ram_plot)
        graph_layout.addWidget(self.temp_plot)
        
        main_layout.addLayout(graph_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.setFont(QFont("Arial", 9))
        self.save_button.clicked.connect(self.save_data)
        self.save_button.setStyleSheet("QPushButton { background-color: #2E86AB; color: white; border: none; padding: 5px; border-radius: 3px; }"
                                      "QPushButton:hover { background-color: #1B6B93; }")
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setFont(QFont("Arial", 9))
        self.pause_button.setCheckable(True)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setStyleSheet("QPushButton { background-color: #A23B72; color: white; border: none; padding: 5px; border-radius: 3px; }"
                                       "QPushButton:checked { background-color: #7A2A58; }")
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # Set the scroll area's widget
        self.scroll.setWidget(self.scroll_content)
        
        # Set the main layout for the window
        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll)
        
        
        # Data storage for metrics
        self.timestamps = collections.deque(maxlen=3600)
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
        self.timer.start(1000)
        
        # Pause state
        self.paused = False

    def apply_dark_theme(self):
        """Apply a dark theme palette for better visibility"""
        #qt5ct palette support
        app = QApplication.instance()
        if app is not None:
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
            app.setPalette(dark_palette)
        
        # Additional styling for compact view
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 3px;
                margin-top: 0.5ex;
                padding-top: 5px;
                background-color: #333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 5px;
                padding: 0 3px 0 3px;
                color: #2E86AB;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                font: bold 10px;
                height: 15px;
            }
            QScrollArea {
                border: none;
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
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                font: bold 10px;
                color: white;
                height: 15px;
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
        self.cpu_label.setText(f"CPU: {cpu}%")
        self.cpu_bar.setValue(int(cpu))
        self.style_bar(self.cpu_bar, cpu, 50, 80)

        self.ram_label.setText(f"RAM: {ram}%")
        self.ram_bar.setValue(int(ram))
        self.style_bar(self.ram_bar, ram, 50, 80)

        if temp is not None:
            self.temp_label.setText(f"Temp: {temp}°C")
            self.temp_bar.setValue(int(temp))
            self.style_bar(self.temp_bar, temp, 50, 70)
        else:
            self.temp_label.setText("Temp: N/A")
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
            "Save Data", 
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
    
    os.environ['QT_QPA_PLATFORMTHEME'] = ''
    
    app = QApplication(sys.argv)
    window = SystemMonitor()
    window.show()
    sys.exit(app.exec_())
