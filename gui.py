import sys
from PyQt5 import QtCore, QtWidgets, QtGui
from functions_window import FunctionsWindow  # Import the functions window

# ------------------ Mock Qontrol Device Driver ------------------
class QontrolDriver:
    def __init__(self):
        # Initialize 60 channels for current (i)
        self.i = {ch: 0.0 for ch in range(1, 61)}

    def set_current(self, ch, value):
        self.i[ch] = value

    def get_current(self, ch):
        return self.i[ch]

    def toggle_current(self, ch, value):
        # Used for toggling: set current to value or to 0.
        self.i[ch] = value

# ------------------ Channel Card Widget ------------------
class ChannelCard(QtWidgets.QFrame):
    def __init__(self, channel, driver, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel = channel
        self.driver = driver

        self.setObjectName("channelCard")
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(6)
        self.layout.setContentsMargins(8,8,8,8)

        # Bold channel label.
        self.title_label = QtWidgets.QLabel(f"Ch {channel:02d}")
        bold_font = QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold)
        self.title_label.setFont(bold_font)
        self.layout.addWidget(self.title_label, alignment=QtCore.Qt.AlignCenter)

        # Current display.
        self.current_label = QtWidgets.QLabel("0.00 mA")
        self.current_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.current_label)

        # Input for new current.
        self.input_field = QtWidgets.QLineEdit()
        self.input_field.setPlaceholderText("Enter mA")
        self.layout.addWidget(self.input_field)

        # Buttons for Set and Get Reading.
        btn_layout = QtWidgets.QHBoxLayout()
        self.set_button = QtWidgets.QPushButton("Set")
        self.get_button = QtWidgets.QPushButton("Get Reading")
        btn_layout.addWidget(self.set_button)
        btn_layout.addWidget(self.get_button)
        self.layout.addLayout(btn_layout)

        # Connect signals.
        self.set_button.clicked.connect(self.apply_current)
        self.get_button.clicked.connect(self.get_reading)

        # Inline CSS for styling.
        self.base_card_style = """
            QFrame {
                background-color: #F7F7F7;
                border: 1px solid #CCC;
                border-radius: 8px;
            }
            QLabel {
                font: 10pt "Segoe UI";
                color: #333;
            }
            QLineEdit {
                background-color: #fff;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
                font: 10pt "Segoe UI";
            }
            QPushButton {
                background-color: #0078D7;
                color: #fff;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font: 10pt "Segoe UI";
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #005FB8;
            }
        """
        self.success_card_style = self.base_card_style + """
            QFrame {
                background-color: #E0F2E9;
                border: 1px solid #A5D6A7;
                border-radius: 8px;
            }
        """
        self.error_card_style = self.base_card_style + """
            QFrame {
                background-color: #FFE5E5;
                border: 1px solid #FFAAAA;
                border-radius: 8px;
            }
        """
        self.setStyleSheet(self.base_card_style)

    def update_current_display(self):
        """Update the current label."""
        current = self.driver.get_current(self.channel)
        self.current_label.setText("{:.2f} mA".format(current))

    def apply_current(self):
        """Read input and update the current."""
        try:
            new_value = float(self.input_field.text())
            self.driver.set_current(self.channel, new_value)
            self.update_current_display()
            self.setStyleSheet(self.success_card_style)
        except ValueError:
            self.setStyleSheet(self.error_card_style)
        QtCore.QTimer.singleShot(1000, lambda: self.setStyleSheet(self.base_card_style))

    def get_reading(self):
        """Update the display with current reading."""
        current = self.driver.get_current(self.channel)
        self.current_label.setText("{:.2f} mA".format(current))
        self.setStyleSheet(self.success_card_style)
        QtCore.QTimer.singleShot(800, lambda: self.setStyleSheet(self.base_card_style))

# ------------------ Main Application Window ------------------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qontrol GUI")
        self.showFullScreen()  # Launch fullscreen
        self.setStyleSheet("background-color: white;")
        self.driver = QontrolDriver()
        self.channel_cards = []

        # Central widget and vertical layout.
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Container for the grid of channels (no scrolling).
        self.grid_widget = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.grid_widget, 1)

        # Create 60 channel cards.
        for ch in range(1, 61):
            card = ChannelCard(ch, self.driver)
            self.channel_cards.append(card)
        self.responsive_layout()

        # --- Bottom Control Area: 4 Equal Columns ---
        self.bottom_widget = QtWidgets.QWidget()
        self.bottom_widget.setMinimumHeight(50)
        bottom_layout = QtWidgets.QGridLayout(self.bottom_widget)
        bottom_layout.setContentsMargins(0,0,0,0)
        bottom_layout.setSpacing(10)
        for col in range(4):
            bottom_layout.setColumnStretch(col, 1)

        # Inline style for buttons.
        btn_style = ("background-color: #0078D7; color: white; border: none; border-radius: 4px; "
                     "padding: 6px; font: 10pt 'Segoe UI'; font-weight: 600;")

        # Column 0: Global mA input and "Set All Currents" button.
        col0_widget = QtWidgets.QWidget()
        col0_layout = QtWidgets.QHBoxLayout(col0_widget)
        col0_layout.setContentsMargins(0,0,0,0)
        col0_layout.setSpacing(5)
        self.global_label = QtWidgets.QLabel("Global mA:")
        self.global_label.setStyleSheet("font: 10pt 'Segoe UI'; color: #333;")
        col0_layout.addWidget(self.global_label)
        self.all_current_input = QtWidgets.QLineEdit()
        self.all_current_input.setPlaceholderText("Enter global mA")
        # Let the input expand to fill extra space:
        self.all_current_input.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.all_current_input.setStyleSheet("background-color: #fff; color: #333; border: 1px solid #ccc; border-radius: 4px; padding: 4px;")
        col0_layout.addWidget(self.all_current_input)
        self.set_all_button = QtWidgets.QPushButton("Set All Currents")
        self.set_all_button.setStyleSheet(btn_style)
        self.set_all_button.clicked.connect(self.set_all_currents)
        col0_layout.addWidget(self.set_all_button)
        bottom_layout.addWidget(col0_widget, 0, 0)

        # Column 1: "Get All Readings"
        col1_widget = QtWidgets.QWidget()
        col1_layout = QtWidgets.QHBoxLayout(col1_widget)
        col1_layout.setContentsMargins(0,0,0,0)
        self.get_all_button = QtWidgets.QPushButton("Get All Readings")
        self.get_all_button.setStyleSheet(btn_style)
        self.get_all_button.clicked.connect(self.get_all_readings)
        col1_layout.addWidget(self.get_all_button)
        bottom_layout.addWidget(col1_widget, 0, 1)

        # Column 2: "Functions"
        col2_widget = QtWidgets.QWidget()
        col2_layout = QtWidgets.QHBoxLayout(col2_widget)
        col2_layout.setContentsMargins(0,0,0,0)
        self.functions_button = QtWidgets.QPushButton("Functions")
        self.functions_button.setStyleSheet(btn_style)
        self.functions_button.clicked.connect(self.open_functions_window)
        col2_layout.addWidget(self.functions_button)
        bottom_layout.addWidget(col2_widget, 0, 2)

        # Column 3: "Exit"
        col3_widget = QtWidgets.QWidget()
        col3_layout = QtWidgets.QHBoxLayout(col3_widget)
        col3_layout.setContentsMargins(0,0,0,0)
        self.exit_button = QtWidgets.QPushButton("Exit")
        self.exit_button.setStyleSheet(btn_style)
        self.exit_button.clicked.connect(QtWidgets.qApp.quit)
        col3_layout.addWidget(self.exit_button)
        bottom_layout.addWidget(col3_widget, 0, 3)

        self.main_layout.addWidget(self.bottom_widget, 0)

        # Timer to update readings every second.
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_all_channel_displays)
        self.timer.start(1000)

    def update_all_channel_displays(self):
        for card in self.channel_cards:
            card.update_current_display()

    def set_all_currents(self):
        """Set all channels to the global mA value."""
        text = self.all_current_input.text()
        try:
            value = float(text)
            for card in self.channel_cards:
                self.driver.set_current(card.channel, value)
                card.update_current_display()
                card.setStyleSheet(card.success_card_style)
                QtCore.QTimer.singleShot(800, lambda c=card: c.setStyleSheet(c.base_card_style))
        except ValueError:
            pass

    def get_all_readings(self):
        for card in self.channel_cards:
            card.get_reading()

    def responsive_layout(self):
        if not hasattr(self, "grid_layout"):
            return
        width = self.width()
        if width > 1800:
            columns = 10
        elif width > 1200:
            columns = 8
        else:
            columns = 6

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        for index, card in enumerate(self.channel_cards):
            row = index // columns
            col = index % columns
            self.grid_layout.addWidget(card, row, col)

    def resizeEvent(self, event):
        if hasattr(self, "grid_layout"):
            self.responsive_layout()
        super().resizeEvent(event)

    def open_functions_window(self):
        self.func_window = FunctionsWindow(self.driver, self)
        self.func_window.show()

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setFont(QtGui.QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()


## Ramp and toggle to see the waveform, plotting the reading as it's reaching desired current.