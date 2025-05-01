import sys
from PyQt5 import QtCore, QtWidgets, QtGui
import qontrol
from functions_window import FunctionsWindow  # Import the functions window

# ------------------ Channel Card Widget ------------------
class ChannelCard(QtWidgets.QFrame):
    def __init__(self, channel, driver, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel = channel
        self.driver = driver

        self.setObjectName("channelCard")
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(6)
        self.layout.setContentsMargins(8, 8, 8, 8)

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

        # Styles
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
            }
        """
        self.error_card_style = self.base_card_style + """
            QFrame {
                background-color: #FFE5E5;
                border: 1px solid #FFAAAA;
            }
        """
        self.setStyleSheet(self.base_card_style)

    def update_current_display(self):
        current = self.driver.i[self.channel]
        self.current_label.setText(f"{current:.2f} mA")

    def apply_current(self):
        try:
            val = float(self.input_field.text())
            self.driver.i[self.channel] = val
            self.update_current_display()
            self.setStyleSheet(self.success_card_style)
        except ValueError:
            self.setStyleSheet(self.error_card_style)
        QtCore.QTimer.singleShot(1000, lambda: self.setStyleSheet(self.base_card_style))

    def get_reading(self):
        val = self.driver.i[self.channel]
        self.current_label.setText(f"{val:.2f} mA")
        self.setStyleSheet(self.success_card_style)
        QtCore.QTimer.singleShot(800, lambda: self.setStyleSheet(self.base_card_style))


# ------------------ Main Application Window ------------------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qontrol GUI")
        self.setStyleSheet("background-color: white;")

        # instantiate the real Qontrol driver
        self.driver = qontrol.QXOutput(serial_port_name="YOUR_SERIAL_PORT")

        # prepare layouts BEFORE fullscreen
        self.channel_cards = []
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # grid of channel cards
        self.grid_widget = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.grid_widget, 1)

        for ch in range(1, 61):
            self.channel_cards.append(ChannelCard(ch, self.driver))
        self.responsive_layout()

        # bottom controls (global set, get all, functions, exit)
        self.bottom_widget = QtWidgets.QWidget()
        self.bottom_widget.setMinimumHeight(50)
        bottom_layout = QtWidgets.QGridLayout(self.bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        for col in range(4):
            bottom_layout.setColumnStretch(col, 1)

        btn_style = (
            "background-color: #0078D7; color: white; border: none;"
            " border-radius: 4px; padding: 6px; font: 10pt 'Segoe UI'; font-weight: 600;"
        )
        # Column 0: Global mA
        col0 = QtWidgets.QWidget()
        l0 = QtWidgets.QHBoxLayout(col0)
        l0.setContentsMargins(0, 0, 0, 0)
        l0.setSpacing(5)
        lbl0 = QtWidgets.QLabel("Global mA:")
        lbl0.setStyleSheet("font: 10pt 'Segoe UI'; color: #333;")
        l0.addWidget(lbl0)
        self.all_current_input = QtWidgets.QLineEdit()
        self.all_current_input.setPlaceholderText("Enter global mA")
        self.all_current_input.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        l0.addWidget(self.all_current_input)
        btn0 = QtWidgets.QPushButton("Set All Currents")
        btn0.setStyleSheet(btn_style)
        btn0.clicked.connect(self.set_all_currents)
        l0.addWidget(btn0)
        bottom_layout.addWidget(col0, 0, 0)
        # Column 1: Get All
        col1 = QtWidgets.QWidget()
        l1 = QtWidgets.QHBoxLayout(col1)
        l1.setContentsMargins(0, 0, 0, 0)
        btn1 = QtWidgets.QPushButton("Get All Readings")
        btn1.setStyleSheet(btn_style)
        btn1.clicked.connect(self.get_all_readings)
        l1.addWidget(btn1)
        bottom_layout.addWidget(col1, 0, 1)
        # Column 2: Functions
        col2 = QtWidgets.QWidget()
        l2 = QtWidgets.QHBoxLayout(col2)
        l2.setContentsMargins(0, 0, 0, 0)
        btn2 = QtWidgets.QPushButton("Functions")
        btn2.setStyleSheet(btn_style)
        btn2.clicked.connect(self.open_functions_window)
        l2.addWidget(btn2)
        bottom_layout.addWidget(col2, 0, 2)
        # Column 3: Exit
        col3 = QtWidgets.QWidget()
        l3 = QtWidgets.QHBoxLayout(col3)
        l3.setContentsMargins(0, 0, 0, 0)
        btn3 = QtWidgets.QPushButton("Exit")
        btn3.setStyleSheet(btn_style)
        btn3.clicked.connect(QtWidgets.qApp.quit)
        l3.addWidget(btn3)
        bottom_layout.addWidget(col3, 0, 3)

        self.main_layout.addWidget(self.bottom_widget, 0)

        # refresh timer
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_all_channel_displays)
        self.timer.start(1000)

        # go fullscreen
        self.showFullScreen()

    def update_all_channel_displays(self):
        for card in self.channel_cards:
            card.update_current_display()

    def set_all_currents(self):
        try:
            val = float(self.all_current_input.text())
            self.driver.i[:] = val
            for card in self.channel_cards:
                card.update_current_display()
                card.setStyleSheet(card.success_card_style)
                QtCore.QTimer.singleShot(800, lambda c=card: c.setStyleSheet(c.base_card_style))
        except ValueError:
            pass

    def get_all_readings(self):
        for card in self.channel_cards:
            card.get_reading()

    def responsive_layout(self):
        if not hasattr(self, 'grid_layout'):
            return
        w = self.width()
        cols = 10 if w > 1800 else 8 if w > 1200 else 6
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        for idx, card in enumerate(self.channel_cards):
            self.grid_layout.addWidget(card, idx // cols, idx % cols)

    def resizeEvent(self, event):
        if hasattr(self, 'grid_layout'):
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