import sys
import numpy as np
from scipy.signal import butter, lfilter
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QDoubleSpinBox
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
        self.data_buffer = deque(maxlen=1024 * 16)
        
        self.horizontal_scaling = 0.05

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start()
        # self.timer.start(1000 // 60) # Set up a timer to trigger updates at 60 FPS
        
        self.input_field = QLineEdit(self)
        self.input_field.hide()
        
        self.spin_box = QDoubleSpinBox(self)
        self.spin_box.setRange(0.01, 5.00)  # Set the range for the spin box
        self.spin_box.setSingleStep(0.025)  # Set the step increment for the spin box
        self.spin_box.setValue(self.horizontal_scaling)  # Set the initial value for the spin box
        self.spin_box.valueChanged.connect(self.update_horizontal_scaling)
        self.spin_box.move(10, 10)  # Set the position of the spin box on the Overlay widget
        self.spin_box.hide()
        
    def update_horizontal_scaling(self, value):
        self.horizontal_scaling = value
        
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
        if np.max(np.abs(data)) > 1:
            data_norm = (data / (np.max(np.abs(data))) * 100)
        else:
            data_norm = data
        path = QPainterPath()
        path.moveTo(50, 200)
        for i in range(1, len(data_norm)):
            x = 50 + i * self.horizontal_scaling
            y = 200 - data_norm[i]
            path.lineTo(x, y)
        return path

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.NoPen))

        in_data = self.stream.read(1024 * 2, exception_on_overflow=False)
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
            if self.input_field.isHidden():
                self.input_field.show()
                self.spin_box.show()
            else:
                self.input_field.hide()
                self.spin_box.hide()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = Overlay()
    overlay.show()
    sys.exit(app.exec_())