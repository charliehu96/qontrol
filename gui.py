#!/usr/bin/env python3

import sys
import time
import logging
from PyQt5 import QtCore, QtWidgets, QtGui
import qontrol
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# ------------------ Logging Configuration ------------------
logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s:%(name)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('QontrolGUI')

# ------------------ Channel Card Widget ------------------
class ChannelCard(QtWidgets.QFrame):
    def __init__(self, channel, driver, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel = channel
        self.driver = driver
        logger.debug(f"Initialized ChannelCard for channel {channel}")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # Channel label
        self.title_label = QtWidgets.QLabel(f"Ch {channel:02d}")
        font = QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold)
        self.title_label.setFont(font)
        layout.addWidget(self.title_label, alignment=QtCore.Qt.AlignCenter)

        # Voltage display
        self.voltage_label = QtWidgets.QLabel("0.00 V")
        self.voltage_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.voltage_label)

        # Input for new voltage
        self.input_field = QtWidgets.QLineEdit()
        self.input_field.setPlaceholderText("Enter V")
        layout.addWidget(self.input_field)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.set_button = QtWidgets.QPushButton("Set")
        self.get_button = QtWidgets.QPushButton("Get Reading")
        btn_layout.addWidget(self.set_button)
        btn_layout.addWidget(self.get_button)
        layout.addLayout(btn_layout)

        # Connect signals
        self.set_button.clicked.connect(self.apply_voltage)
        self.get_button.clicked.connect(self.get_reading)

        # Styles
        self.base_style = """
            QFrame { background: #F7F7F7; border: 1px solid #CCC; border-radius: 8px; }
            QLabel { font: 10pt 'Segoe UI'; color: #333; }
            QLineEdit { background: #fff; border: 1px solid #ccc; border-radius: 4px; padding: 4px; }
            QPushButton { background: #0078D7; color: #fff; border: none; border-radius: 4px; padding: 6px; font: 10pt 'Segoe UI'; font-weight: 600; }
            QPushButton:hover { background: #005FB8; }
        """
        self.success_style = self.base_style + "QFrame { background: #E0F2E9; border: 1px solid #A5D6A7; }"
        self.error_style   = self.base_style + "QFrame { background: #FFE5E5; border: 1px solid #FFAAAA; }"
        self.setStyleSheet(self.base_style)

    def apply_voltage(self):
        """Send the new voltage to the hardware and confirm."""
        try:
            v = float(self.input_field.text())
            logger.debug(f"Applying voltage: setting channel {self.channel} to {v} V")
            # Use array syntax for voltage
            self.driver.v[self.channel] = v
            # Read back to confirm
            confirmed = self.driver.v[self.channel]
            logger.debug(f"Confirmed channel {self.channel} voltage: {confirmed} V")
            self.voltage_label.setText(f"{confirmed:.2f} V")
            self.setStyleSheet(self.success_style)
        except Exception as e:
            logger.error(f"Error applying voltage to channel {self.channel}: {e}")
            self.setStyleSheet(self.error_style)
        finally:
            QtCore.QTimer.singleShot(1000, lambda: self.setStyleSheet(self.base_style))

    def get_reading(self):
        """Fetch the voltage reading from the hardware."""
        try:
            v = self.driver.v[self.channel]
            logger.debug(f"Reading channel {self.channel}: {v} V")
            self.voltage_label.setText(f"{v:.2f} V")
            self.setStyleSheet(self.success_style)
        except Exception as e:
            logger.error(f"Error reading channel {self.channel}: {e}")
            self.setStyleSheet(self.error_style)
        finally:
            QtCore.QTimer.singleShot(800, lambda: self.setStyleSheet(self.base_style))

# ------------------ Functions Window ------------------
class FunctionsWindow(QtWidgets.QDialog):
    def __init__(self, driver, parent=None):
        super().__init__(parent)
        self.driver = driver
        self.main = parent
        self.setWindowTitle("Functions")
        self.resize(600, 400)
        self.setStyleSheet("background: #F7F7F7; font-family: 'Segoe UI'; color: #333;")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Channel selector
        layout.addWidget(QtWidgets.QLabel("Select Channel:"))
        self.combo = QtWidgets.QComboBox()
        self.combo.setStyleSheet("QComboBox:hover { background: #e6e6e6; }")
        for ch in range(1, self.driver.n_chs+1):
            self.combo.addItem(f"Ch {ch:02d}")
        layout.addWidget(self.combo)

        # Toggle controls
        t_layout = QtWidgets.QHBoxLayout()
        t_layout.addWidget(QtWidgets.QLabel("Toggle V:"))
        self.toggle_input = QtWidgets.QLineEdit()
        self.toggle_input.setPlaceholderText("Enter V")
        self.toggle_input.setFixedWidth(80)
        t_layout.addWidget(self.toggle_input)
        self.toggle_button = QtWidgets.QPushButton("Toggle")
        self.toggle_button.setCheckable(True)
        t_layout.addWidget(self.toggle_button)
        layout.addLayout(t_layout)

        # Ramp controls
        r_layout = QtWidgets.QHBoxLayout()
        r_layout.addWidget(QtWidgets.QLabel("Ramp Max V:"))
        self.ramp_max_input = QtWidgets.QLineEdit()
        self.ramp_max_input.setPlaceholderText("Max V")
        self.ramp_max_input.setFixedWidth(80)
        r_layout.addWidget(self.ramp_max_input)
        r_layout.addWidget(QtWidgets.QLabel("Duration (ms):"))
        self.ramp_dur_input = QtWidgets.QLineEdit()
        self.ramp_dur_input.setPlaceholderText("ms")
        self.ramp_dur_input.setFixedWidth(80)
        r_layout.addWidget(self.ramp_dur_input)
        self.ramp_button = QtWidgets.QPushButton("Ramp")
        r_layout.addWidget(self.ramp_button)
        layout.addLayout(r_layout)

        # Real-time plot setup
        self.start_time = time.time()
        self.time_data = []
        self.voltage_data = []
        fig = Figure()
        self.canvas = FigureCanvas(fig)
        self.ax = fig.add_subplot(111)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Voltage (V)")
        layout.addWidget(self.canvas)

        # Timers
        self.toggle_timer = QtCore.QTimer(self)
        self.toggle_timer.setInterval(1)
        self.ramp_timer = QtCore.QTimer(self)
        self.auto_timer = QtCore.QTimer(self)
        self.auto_timer.setInterval(200)

        # Connect signals
        self.toggle_button.toggled.connect(self.toggle_voltage)
        self.toggle_timer.timeout.connect(self.perform_toggle)
        self.ramp_button.clicked.connect(self.start_ramp)
        self.ramp_timer.timeout.connect(self.perform_ramp)
        self.auto_timer.timeout.connect(self._auto_update)

        # Internal state
        self.active_channel = None
        self.toggle_state = False

    def get_selected_channel(self):
        return int(self.combo.currentText().split()[1])

    def toggle_voltage(self, checked):
        ch = self.get_selected_channel()
        self.active_channel = ch
        if checked:
            try:
                self.toggle_value = float(self.toggle_input.text())
            except ValueError:
                self.toggle_value = 0.0
            self.toggle_state = False
            logger.debug(f"Starting toggle on channel {ch} with {self.toggle_value} V")
            self.toggle_timer.start()
            self.auto_timer.start()
            self.toggle_button.setText("Toggle (On)")
        else:
            logger.debug(f"Stopping toggle on channel {ch}")
            self.toggle_timer.stop()
            self.auto_timer.stop()
            self.driver.v[ch] = 0
            self.toggle_button.setText("Toggle")

    def perform_toggle(self):
        ch = self.active_channel
        v = self.toggle_value if not self.toggle_state else 0
        logger.debug(f"Toggling channel {ch} to {v} V")
        self.driver.v[ch] = v
        self.toggle_state = not self.toggle_state

    def start_ramp(self):
        ch = self.get_selected_channel()
        self.active_channel = ch
        try:
            max_v = float(self.ramp_max_input.text())
        except ValueError:
            max_v = 0.0
        try:
            duration = float(self.ramp_dur_input.text())
        except ValueError:
            duration = 1000.0
        steps = 10
        self.step_value = max_v / steps
        interval = duration / steps
        self.current_step = 0
        logger.debug(f"Starting ramp on channel {ch}: max {max_v} V over {duration} ms")
        self.ramp_timer.setInterval(int(interval))
        self.ramp_timer.start()
        self.auto_timer.start()

    def perform_ramp(self):
        ch = self.active_channel
        self.current_step += 1
        value = self.current_step * self.step_value
        if self.current_step <= 10:
            logger.debug(f"Ramping channel {ch} to {value} V (step {self.current_step})")
            self.driver.v[ch] = value
        else:
            logger.debug(f"Ramp complete on channel {ch}")
            self.ramp_timer.stop()
            self.auto_timer.stop()

    def _auto_update(self):
        if self.active_channel is None:
            return
        # Update main window display
        for card in self.main.cards:
            if card.channel == self.active_channel:
                old = card.voltage_label.text()
                new_val = self.driver.v[self.active_channel]
                new = f"{new_val:.2f} V"
                card.voltage_label.setText(new)
                if old != new:
                    logger.debug(f"Channel {self.active_channel} updated to {new}")
                    card.setStyleSheet(card.success_style)
                    QtCore.QTimer.singleShot(800, lambda w=card: w.setStyleSheet(w.base_style))
                break
        # Plot update
        t = time.time() - self.start_time
        self.time_data.append(t)
        self.voltage_data.append(self.driver.v[self.active_channel])
        self.ax.clear()
        self.ax.plot(self.time_data, self.voltage_data)
        self.canvas.draw()

# ------------------ Main Application Window ------------------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qontrol GUI")
        self.setStyleSheet("background: white;")

        # Initialize driver with response_timeout
        serial_port = "YOUR_SERIAL_PORT"
        self.driver = qontrol.QXOutput(serial_port_name=serial_port, response_timeout=0.1)
        logger.info(f"Qontrol '{self.driver.device_id}' initialized with firmware {self.driver.firmware} and {self.driver.n_chs} channels")

        # Central widget and layout
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Channel grid
        grid_widget = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(grid_widget)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(grid_widget, 1)

        self.cards = []
        for ch in range(1, self.driver.n_chs + 1):
            card = ChannelCard(ch, self.driver)
            self.cards.append(card)
        self.responsive_layout()

        # Bottom controls
        main_layout.addWidget(self._build_bottom_controls(), 0)

        # Show fullscreen
        self.showFullScreen()

    def _build_bottom_controls(self):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        for i in range(4): layout.setColumnStretch(i, 1)

        btn_style = (
            "background:#0078D7;color:white;border:none; border-radius:4px; padding:6px;"
            "font:10pt 'Segoe UI'; font-weight:600;"
        )
        # Column 0: Global set
        w0 = QtWidgets.QWidget(); l0 = QtWidgets.QHBoxLayout(w0)
        l0.setContentsMargins(0, 0, 0, 0); l0.setSpacing(5)
        l0.addWidget(QtWidgets.QLabel("Global V:"))
        self.global_input = QtWidgets.QLineEdit()
        self.global_input.setPlaceholderText("Enter global V")
        self.global_input.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        l0.addWidget(self.global_input)
        btn0 = QtWidgets.QPushButton("Set All Voltages"); btn0.setStyleSheet(btn_style)
        btn0.clicked.connect(self.set_all)
        l0.addWidget(btn0)
        layout.addWidget(w0, 0, 0)

        # Column 1: Get all readings
        w1 = QtWidgets.QWidget(); l1 = QtWidgets.QHBoxLayout(w1)
        l1.setContentsMargins(0, 0, 0, 0)
        btn1 = QtWidgets.QPushButton("Get All Readings"); btn1.setStyleSheet(btn_style)
        btn1.clicked.connect(self.get_all)
        l1.addWidget(btn1); layout.addWidget(w1, 0, 1)

        # Column 2: Functions
        w2 = QtWidgets.QWidget(); l2 = QtWidgets.QHBoxLayout(w2)
        l2.setContentsMargins(0, 0, 0, 0)
        btn2 = QtWidgets.QPushButton("Functions"); btn2.setStyleSheet(btn_style)
        btn2.clicked.connect(self.open_functions)
        l2.addWidget(btn2); layout.addWidget(w2, 0, 2)

        # Column 3: Exit
        w3 = QtWidgets.QWidget(); l3 = QtWidgets.QHBoxLayout(w3)
        l3.setContentsMargins(0, 0, 0, 0)
        btn3 = QtWidgets.QPushButton("Exit"); btn3.setStyleSheet(btn_style)
        btn3.clicked.connect(QtWidgets.qApp.quit)
        l3.addWidget(btn3); layout.addWidget(w3, 0, 3)

        return container

    def set_all(self):
        try:
            v = float(self.global_input.text())
            logger.debug(f"Bulk setting all channels to {v} V")
            self.driver.v[:] = v
            for card in self.cards:
                card.voltage_label.setText(f"{v:.2f} V")
                card.setStyleSheet(card.success_style)
                QtCore.QTimer.singleShot(800, lambda w=card: w.setStyleSheet(w.base_style))
        except Exception as e:
            logger.error(f"Error bulk setting voltages: {e}")

    def get_all(self):
        logger.debug("Manual bulk read of all channels")
        for card in self.cards:
            card.get_reading()

    def open_functions(self):
        self.func_win = FunctionsWindow(self.driver, self)
        self.func_win.show()

    def responsive_layout(self):
        width = self.width()
        cols = 10 if width > 1800 else 8 if width > 1200 else 6
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget(): item.widget().setParent(None)
        for idx, card in enumerate(self.cards):
            self.grid_layout.addWidget(card, idx // cols, idx % cols)

    def resizeEvent(self, event):
        self.responsive_layout()
        super().resizeEvent(event)

# ------------------ Entry Point ------------------
def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setFont(QtGui.QFont("Segoe UI", 10))
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
