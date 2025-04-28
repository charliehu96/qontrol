from PyQt5 import QtCore, QtWidgets

class FunctionsWindow(QtWidgets.QDialog):
    """
    Advanced functions (Toggle and Ramp) with auto-updating reading.
    When Toggle or Ramp is active, the corresponding channel's reading in the main window
    will auto-update every 200 ms and flash green if it changes.
    """
    def __init__(self, driver, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Functions")
        self.driver = driver
        self.main_window = parent  # Reference to MainWindow
        self.resize(400, 240)
        self.setStyleSheet("background-color: #F7F7F7; font-family: 'Segoe UI'; color: #333;")
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10,10,10,10)

        # Channel selection dropdown with hover indicator.
        self.layout.addWidget(QtWidgets.QLabel("Select Channel:"))
        self.channel_combo = QtWidgets.QComboBox()
        # Add hover style for the dropdown:
        self.channel_combo.setStyleSheet("QComboBox:hover { background-color: #e6e6e6; }")
        for ch in range(1, 61):
            self.channel_combo.addItem("Ch {:02d}".format(ch))
        self.layout.addWidget(self.channel_combo)

        # Timer for auto-updating the reading.
        self.auto_update_timer = QtCore.QTimer(self)
        self.auto_update_timer.setInterval(200)  # update every 200 ms
        self.auto_update_timer.timeout.connect(self.auto_update_reading)
        self.active_channel = None

        # --- Function A: Toggle ---
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
        self.toggle_timer.setInterval(1)  # 1 ms for toggling
        self.toggle_timer.timeout.connect(self.perform_toggle)
        self.toggle_state = False
        self.toggle_value = 0.0

        # --- Function B: Ramp ---
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

    def get_selected_channel(self):
        text = self.channel_combo.currentText()  # e.g., "Ch 01"
        return int(text.split()[1])

    # ------------------ Auto-Updating Reading ------------------
    def auto_update_reading(self):
        """Update the reading of the active channel in the main window and flash green if changed."""
        if self.active_channel is None:
            return
        for card in self.main_window.channel_cards:
            if card.channel == self.active_channel:
                old_text = card.current_label.text()
                card.update_current_display()
                new_text = card.current_label.text()
                if old_text != new_text:
                    card.setStyleSheet(card.success_card_style)
                    QtCore.QTimer.singleShot(800, lambda c=card: c.setStyleSheet(c.base_card_style))
                break

    # ------------------ Toggle Function ------------------
    def toggle_current(self, checked):
        ch = self.get_selected_channel()
        if checked:
            self.toggle_button.setText("Toggle (On)")
            self.active_channel = ch
            try:
                self.toggle_value = float(self.toggle_input.text())
            except ValueError:
                self.toggle_value = 0.0
            self.toggle_state = False  # Start from off state.
            self.toggle_timer.start()
            self.auto_update_timer.start()
        else:
            self.toggle_button.setText("Toggle")
            self.toggle_timer.stop()
            self.driver.toggle_current(ch, 0.0)
            self.auto_update_timer.stop()

    def perform_toggle(self):
        ch = self.active_channel
        if ch is None:
            return
        if self.toggle_state:
            self.driver.toggle_current(ch, 0.0)
            self.toggle_state = False
        else:
            self.driver.toggle_current(ch, self.toggle_value)
            self.toggle_state = True

    # ------------------ Ramp Function ------------------
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
        self.driver.set_current(ch, self.current_ramp)
        self.ramp_timer.start()
        self.auto_update_timer.start()

    def perform_ramp(self):
        self.ramp_count += 1
        self.current_ramp += self.ramp_step
        ch = self.active_channel
        if self.ramp_count <= self.ramp_steps:
            self.driver.set_current(ch, self.current_ramp)
        else:
            self.ramp_timer.stop()
            self.auto_update_timer.stop()