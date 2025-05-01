import time
from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class FunctionsWindow(QtWidgets.QDialog):
    """
    Advanced functions (Toggle and Ramp) with auto-updating reading
    and a real-time plot of current vs. time.
    """
    def __init__(self, driver, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Functions")
        self.driver = driver
        self.main_window = parent
        self.resize(600, 400)
        self.setStyleSheet("background-color: #F7F7F7; font-family: 'Segoe UI'; color: #333;")
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10,10,10,10)

        # Channel selection
        self.layout.addWidget(QtWidgets.QLabel("Select Channel:"))
        self.channel_combo = QtWidgets.QComboBox()
        self.channel_combo.setStyleSheet("QComboBox:hover { background-color: #e6e6e6; }")
        for ch in range(1, 61):
            self.channel_combo.addItem(f"Ch {ch:02d}")
        self.layout.addWidget(self.channel_combo)

        # Auto-update timer
        self.auto_update_timer = QtCore.QTimer(self)
        self.auto_update_timer.setInterval(200)  # 200 ms
        self.auto_update_timer.timeout.connect(self.auto_update_reading)
        self.active_channel = None

        # Toggle controls
        toggle_layout = QtWidgets.QHBoxLayout()
        toggle_layout.addWidget(QtWidgets.QLabel("Toggle mA:"))
        self.toggle_input = QtWidgets.QLineEdit()
        self.toggle_input.setPlaceholderText("Enter mA")
        self.toggle_input.setFixedWidth(80)
        toggle_layout.addWidget(self.toggle_input)
        self.toggle_button = QtWidgets.QPushButton("Toggle")
        self.toggle_button.setCheckable(True)
        self.toggle_button.toggled.connect(self.toggle_current)
        toggle_layout.addWidget(self.toggle_button)
        self.layout.addLayout(toggle_layout)

        self.toggle_timer = QtCore.QTimer(self)
        self.toggle_timer.setInterval(1)   # 1 ms toggle
        self.toggle_timer.timeout.connect(self.perform_toggle)
        self.toggle_state = False
        self.toggle_value = 0.0

        # Ramp controls
        ramp_layout = QtWidgets.QHBoxLayout()
        ramp_layout.addWidget(QtWidgets.QLabel("Ramp Max mA:"))
        self.ramp_max_input = QtWidgets.QLineEdit()
        self.ramp_max_input.setPlaceholderText("Max mA")
        self.ramp_max_input.setFixedWidth(80)
        ramp_layout.addWidget(self.ramp_max_input)
        ramp_layout.addWidget(QtWidgets.QLabel("Duration (ms):"))
        self.ramp_duration_input = QtWidgets.QLineEdit()
        self.ramp_duration_input.setPlaceholderText("ms")
        self.ramp_duration_input.setFixedWidth(80)
        ramp_layout.addWidget(self.ramp_duration_input)
        self.ramp_button = QtWidgets.QPushButton("Ramp")
        self.ramp_button.clicked.connect(self.start_ramp)
        ramp_layout.addWidget(self.ramp_button)
        self.layout.addLayout(ramp_layout)

        self.ramp_timer = QtCore.QTimer(self)
        self.ramp_timer.timeout.connect(self.perform_ramp)
        self.ramp_steps = 10

        # --- Real-time plotting setup ---
        self.start_time    = time.time()
        self.time_data     = []
        self.current_data  = []
        self.figure        = Figure()
        self.canvas        = FigureCanvas(self.figure)
        self.ax            = self.figure.add_subplot(111)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Current (mA)")
        self.layout.addWidget(self.canvas)

        # also hook plot into the same auto-update timer
        self.auto_update_timer.timeout.connect(self._update_plot)

    def get_selected_channel(self):
        text = self.channel_combo.currentText()
        return int(text.split()[1])

    def auto_update_reading(self):
        if self.active_channel is None:
            return
        for card in self.main_window.channel_cards:
            if card.channel == self.active_channel:
                old = card.current_label.text()
                card.update_current_display()
                new = card.current_label.text()
                if old != new:
                    card.setStyleSheet(card.success_card_style)
                    QtCore.QTimer.singleShot(800, lambda c=card: c.setStyleSheet(c.base_card_style))
                break

    def _update_plot(self):
        if self.active_channel is None:
            return
        t   = time.time() - self.start_time
        val = self.driver.i[self.active_channel]
        self.time_data.append(t)
        self.current_data.append(val)

        self.ax.clear()
        self.ax.plot(self.time_data, self.current_data)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Current (mA)")
        self.canvas.draw()

    def toggle_current(self, checked):
        ch = self.get_selected_channel()
        if checked:
            self.toggle_button.setText("Toggle (On)")
            self.active_channel = ch
            try:
                self.toggle_value = float(self.toggle_input.text())
            except ValueError:
                self.toggle_value = 0.0
            self.toggle_state = False
            self.toggle_timer.start()
            self.auto_update_timer.start()
        else:
            self.toggle_button.setText("Toggle")
            self.toggle_timer.stop()
            self.driver.i[ch] = 0.0
            self.auto_update_timer.stop()

    def perform_toggle(self):
        ch = self.active_channel
        if ch is None:
            return
        if self.toggle_state:
            self.driver.i[ch] = 0.0
            self.toggle_state = False
        else:
            self.driver.i[ch] = self.toggle_value
            self.toggle_state = True

    def start_ramp(self):
        ch = self.get_selected_channel()
        self.active_channel = ch
        try:
            self.ramp_max = float(self.ramp_max_input.text())
        except ValueError:
            self.ramp_max = 0.0
        try:
            self.ramp_duration = float(self.ramp_duration_input.text())
        except ValueError:
            self.ramp_duration = 1000.0
        self.ramp_step = self.ramp_max / self.ramp_steps
        interval = self.ramp_duration / self.ramp_steps
        self.ramp_timer.setInterval(int(interval))
        self.current_ramp = 0.0
        self.ramp_count = 0
        self.driver.i[ch] = self.current_ramp
        self.ramp_timer.start()
        self.auto_update_timer.start()

    def perform_ramp(self):
        self.ramp_count += 1
        self.current_ramp += self.ramp_step
        ch = self.active_channel
        if self.ramp_count <= self.ramp_steps:
            self.driver.i[ch] = self.current_ramp
        else:
            self.ramp_timer.stop()
            self.auto_update_timer.stop()
