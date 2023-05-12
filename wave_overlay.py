import sys, time
import numpy as np
from scipy.signal import butter, lfilter
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QDoubleSpinBox, QComboBox
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath
from PyQt5.QtCore import Qt, QPoint, QEvent, QTimer
from collections import deque
from recordOutput import record_stream

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents) # Make the widget transparent for mouse events
        
        screen_geometry = QApplication.desktop().screenGeometry()
        self.setGeometry(0, 0, screen_geometry.width(), screen_geometry.height() - 10) # -10 to account for the task bar
        
        self.stream, self.wave_file, self.sample_rate = record_stream()
        self.data_buffer = deque(maxlen=1024 * 4)
        
        self.variable_values = {
            'Horizontal Scaling': 0.05,
            'Variable 2': 1.0,
            'Variable 3': 2.0
        }
        self.current_variable = 'Horizontal Scaling'

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start()
        # self.timer.start(1000 // 60) # Set up a timer to trigger updates at 60 FPS
        
        self.combo_box = QComboBox(self)
        self.combo_box.addItems(list(self.variable_values.keys()))
        self.combo_box.currentIndexChanged.connect(self.update_combo_box)
        self.combo_box.setStyleSheet("background-color: black; color: green;")
        self.combo_box.move(10, 10)  # Set the position of the combo box on the Overlay widget
        self.combo_box.hide()
        
        self.spin_box = QDoubleSpinBox(self)
        self.spin_box.setRange(0.01, 5.00)  # Set the range for the spin box
        self.spin_box.setSingleStep(0.05)  # Set the step increment for the spin box
        self.spin_box.setValue(self.variable_values[self.current_variable])  # Set the initial value for the spin box
        self.spin_box.valueChanged.connect(self.update_variable_value)
        self.spin_box.setStyleSheet("""
    QDoubleSpinBox {
        background-color: black; 
        color: green;
    }
    QDoubleSpinBox::up-button {
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 16px;
        border-width: 1px;
    }
    QDoubleSpinBox::down-button {
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 16px;
        border-width: 1px;
    }
    QDoubleSpinBox::up-arrow {
        image: url(/path/to/up_arrow.png);
        width: 10px;
        height: 10px;
    }
    QDoubleSpinBox::down-arrow {
        image: url(/path/to/down_arrow.png);
        width: 10px;
        height: 10px;
    }
""")
        self.spin_box.move(150, 10)  # Set the position of the spin box on the Overlay widget
        self.spin_box.hide()
        
    def update_combo_box(self, index):
        selected_variable = self.combo_box.currentText()
        self.current_variable = selected_variable
        self.spin_box.setValue(self.variable_values[self.current_variable])

    def update_variable_value(self, value):
        self.variable_values[self.current_variable] = value
        print(f"New value for {self.current_variable}: {value}")
        
    def path_from_fft_data(self, data):
        fft_freq = np.fft.rfftfreq(len(data), 1/300)
        fft_data = np.fft.rfft(data)
        
        fft_data = fft_data / np.max(np.abs(fft_data)) * 100
        fft_data_norm = np.abs(fft_data / np.max(np.abs(fft_data)) * 100)
        fft_data_norm = fft_data_norm[0:len(fft_data_norm)//4]
        
        path = QPainterPath()
        path.moveTo(50, 200)
        for i in range(1, len(fft_data_norm)):
            # x = int(5 * fft_freq[i]) + 100
            x = 50 + i * 6
            y = 200 - fft_data_norm[i]
            path.lineTo(x, y)
        return path
    
    def path_from_wave_data(self, data):
        data_norm = data / np.int16(10)
        path = QPainterPath()
        path.moveTo(50, 200 - data_norm[0])
        for i in range(0, len(data_norm)):
            x = 50 + i * self.variable_values['Horizontal Scaling']
            y = 200 - data_norm[i]
            path.lineTo(x, y)
        return path

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.NoPen))
        
        in_data = self.stream.read(1024, exception_on_overflow=False)
        
        # self.wave_file.writeframes(in_data)
        data = np.frombuffer(in_data, dtype=np.int16)
        self.data_buffer.extend(data)

        path = self.path_from_wave_data(self.data_buffer)
        painter.setPen(QPen(QColor(0, 255, 0)))
        painter.drawPath(path)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            # Close the application
            print('Closing application...')
            self.wave_file.close()
            self.stream.stop_stream()
            self.stream.close()
            self.close()
        elif event.key() == Qt.Key_W:
            # Toggle the visibility of the input field
            # TODO Set a class attribute to track when the menu is hidden
            if self.combo_box.isHidden():
                self.combo_box.show()
                self.spin_box.show()
            else:
                self.combo_box.hide()
                self.spin_box.hide()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = Overlay()
    overlay.show()
    sys.exit(app.exec_())