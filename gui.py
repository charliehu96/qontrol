#!/usr/bin/env python3

diimport sys, time
from PyQt5 import QtCore, QtWidgets, QtGui
import qontrol
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

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

        # Channel label
        self.title_label = QtWidgets.QLabel(f"Ch {channel:02d}")
        bold = QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold)
        self.title_label.setFont(bold)
        self.layout.addWidget(self.title_label, alignment=QtCore.Qt.AlignCenter)

        # Display
        self.current_label = QtWidgets.QLabel("0.00 mA")
        self.current_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.current_label)

        # Input
        self.input_field = QtWidgets.QLineEdit()
        self.input_field.setPlaceholderText("Enter mA")
        self.layout.addWidget(self.input_field)

        # Buttons
        btns = QtWidgets.QHBoxLayout()
        self.set_button = QtWidgets.QPushButton("Set")
        self.get_button = QtWidgets.QPushButton("Get Reading")
        btns.addWidget(self.set_button)
        btns.addWidget(self.get_button)
        self.layout.addLayout(btns)

        # Connect
        self.set_button.clicked.connect(self.apply_current)
        self.get_button.clicked.connect(self.get_reading)

        # Styles
        self.base_style = """
            QFrame { background: #F7F7F7; border:1px solid #CCC; border-radius:8px; }
            QLabel { font:10pt 'Segoe UI'; color:#333; }
            QLineEdit { background:#fff; border:1px solid #CCC; border-radius:4px; padding:4px; }
            QPushButton { background:#0078D7; color:#fff; border:none; border-radius:4px; padding:6px; font:10pt 'Segoe UI'; }
            QPushButton:hover { background:#005FB8; }
        """
        self.success_style = self.base_style + "QFrame { background:#E0F2E9; border:1px solid #A5D6A7; }"
        self.error_style   = self.base_style + "QFrame { background:#FFE5E5; border:1px solid #FFAAAA; }"
        self.setStyleSheet(self.base_style)

    def update_current_display(self):
        val = self.driver.i[self.channel]
        self.current_label.setText(f"{val:.2f} mA")

    def apply_current(self):
        try:
            val = float(self.input_field.text())
            self.driver.i[self.channel] = val
            self.update_current_display()
            self.setStyleSheet(self.success_style)
        except ValueError:
            self.setStyleSheet(self.error_style)
        QtCore.QTimer.singleShot(1000, lambda: self.setStyleSheet(self.base_style))

    def get_reading(self):
        val = self.driver.i[self.channel]
        self.current_label.setText(f"{val:.2f} mA")
        self.setStyleSheet(self.success_style)
        QtCore.QTimer.singleShot(800, lambda: self.setStyleSheet(self.base_style))


# -------------- Functions Window ---------------
class FunctionsWindow(QtWidgets.QDialog):
    def __init__(self, driver, parent=None):
        super().__init__(parent)
        self.driver = driver
        self.main_win = parent
        self.active = None
        self.setWindowTitle("Functions")
        self.resize(600,400)
        self.layout = QtWidgets.QVBoxLayout(self)

        # Channel selector
        self.layout.addWidget(QtWidgets.QLabel("Select Channel:"))
        self.combo = QtWidgets.QComboBox()
        for ch in range(1,61):
            self.combo.addItem(f"Ch {ch:02d}")
        self.combo.setStyleSheet("QComboBox:hover{background:#e6e6e6}")
        self.layout.addWidget(self.combo)

        # Toggle
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("Toggle mA:"))
        self.t_in = QtWidgets.QLineEdit(); self.t_in.setFixedWidth(80)
        row.addWidget(self.t_in)
        self.t_btn = QtWidgets.QPushButton("Toggle"); self.t_btn.setCheckable(True)
        self.t_btn.toggled.connect(self.toggle_current)
        row.addWidget(self.t_btn)
        self.layout.addLayout(row)

        self.t_timer = QtCore.QTimer(self); self.t_timer.setInterval(1)
        self.t_timer.timeout.connect(self._do_toggle)
        self.t_state=False; self.t_val=0.0

        # Ramp
        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(QtWidgets.QLabel("Ramp Max mA:"))
        self.r_in = QtWidgets.QLineEdit(); self.r_in.setFixedWidth(80)
        row2.addWidget(self.r_in)
        row2.addWidget(QtWidgets.QLabel("Duration(ms):"))
        self.d_in = QtWidgets.QLineEdit(); self.d_in.setFixedWidth(80)
        row2.addWidget(self.d_in)
        self.r_btn = QtWidgets.QPushButton("Ramp"); self.r_btn.clicked.connect(self.start_ramp)
        row2.addWidget(self.r_btn)
        self.layout.addLayout(row2)

        self.r_timer = QtCore.QTimer(self); self.r_timer.timeout.connect(self._do_ramp)
        self.r_steps=10

        # Plot
        self.start_t = time.time(); self.x=[]; self.y=[]
        self.fig = Figure(); self.canvas=FigureCanvas(self.fig)
        self.ax=self.fig.add_subplot(111)
        self.ax.set_xlabel("Time (s)"); self.ax.set_ylabel("Current (mA)")
        self.layout.addWidget(self.canvas)

        # update timer for both reading & plot
        self.au_timer = QtCore.QTimer(self); self.au_timer.setInterval(200)
        self.au_timer.timeout.connect(self._auto_update)

    def get_chan(self):
        return int(self.combo.currentText().split()[1])

    def _auto_update(self):
        # refresh display
        if not self.active: return
        for c in self.main_win.channel_cards:
            if c.channel==self.active:
                old=c.current_label.text(); c.update_current_display();
                if c.current_label.text()!=old:
                    c.setStyleSheet(c.success_style)
                    QtCore.QTimer.singleShot(800, lambda w=c: w.setStyleSheet(w.base_style))
                break
        # plot
        t=time.time()-self.start_t; v=self.driver.i[self.active]
        self.x.append(t); self.y.append(v)
        self.ax.clear(); self.ax.plot(self.x,self.y)
        self.ax.set_xlabel("Time (s)"); self.ax.set_ylabel("Current (mA)")
        self.canvas.draw()

    def toggle_current(self, chk):
        ch=self.get_chan(); self.active=ch
        if chk:
            self.t_btn.setText("Toggle(On)")
            try: self.t_val=float(self.t_in.text())
            except: self.t_val=0.0
            self.t_state=False; self.t_timer.start(); self.au_timer.start()
        else:
            self.t_btn.setText("Toggle"); self.t_timer.stop(); self.driver.i[ch]=0; self.au_timer.stop()

    def _do_toggle(self):
        ch=self.active
        self.driver.i[ch] = (0 if self.t_state else self.t_val)
        self.t_state=not self.t_state

    def start_ramp(self):
        ch=self.get_chan(); self.active=ch
        try: mx=float(self.r_in.text())
        except: mx=0.0
        try: dur=float(self.d_in.text())
        except: dur=1000.0
        step=mx/self.r_steps; interval=dur/self.r_steps
        self.cur=0; self.cnt=0
        self.r_timer.setInterval(int(interval))
        self.driver.i[ch]=0; self.r_timer.start(); self.au_timer.start(); self.step=step

    def _do_ramp(self):
        self.cnt+=1; self.cur+=self.step; ch=self.active
        if self.cnt<=self.r_steps:
            self.driver.i[ch]=self.cur
        else:
            self.r_timer.stop(); self.au_timer.stop()


# ------------------ Main Application Window ------------------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qontrol GUI")
        self.setStyleSheet("background:white;")
        self.driver = qontrol.QXOutput(serial_port_name="YOUR_SERIAL_PORT")
        self.channel_cards=[]
        w=QtWidgets.QWidget(); self.setCentralWidget(w)
        v=QtWidgets.QVBoxLayout(w); v.setSpacing(10); v.setContentsMargins(10,10,10,10)

        # grid
        gw=QtWidgets.QWidget(); self.gl=QtWidgets.QGridLayout(gw)
        self.gl.setSpacing(10); self.gl.setContentsMargins(0,0,0,0)
        v.addWidget(gw,1)
        for ch in range(1,61):
            self.channel_cards.append(ChannelCard(ch,self.driver))
        self._layout_grid()

        # bottom bar
        bb=QtWidgets.QWidget(); bb.setFixedHeight(50)
        bl=QtWidgets.QGridLayout(bb); bl.setContentsMargins(0,0,0,0); bl.setSpacing(10)
        for i in range(4): bl.setColumnStretch(i,1)
        btns=[("Global mA:",True),("Get All Readings",False),("Functions",False),("Exit",False)]
        # Global
        c0=QtWidgets.QWidget(); l0=QtWidgets.QHBoxLayout(c0); l0.setSpacing(5)
        lbl=QtWidgets.QLabel("Global mA:"); l0.addWidget(lbl)
        self.ginput=QtWidgets.QLineEdit(); self.ginput.setPlaceholderText("Enter global mA"); l0.addWidget(self.ginput)
        b0=QtWidgets.QPushButton("Set All Currents"); b0.clicked.connect(self._set_all); l0.addWidget(b0); bl.addWidget(c0,0,0)
        # Get All
        b1=QtWidgets.QPushButton("Get All Readings"); b1.clicked.connect(self._get_all); bl.addWidget(b1,0,1)
        # Func
        b2=QtWidgets.QPushButton("Functions"); b2.clicked.connect(self._open_funcs); bl.addWidget(b2,0,2)
        # Exit
        b3=QtWidgets.QPushButton("Exit"); b3.clicked.connect(QtWidgets.qApp.quit); bl.addWidget(b3,0,3)
        v.addWidget(bb,0)

        self.showFullScreen()

    def _layout_grid(self):
        w=self.width(); cols=10 if w>1800 else 8 if w>1200 else 6
        while self.gl.count():
            i=self.gl.takeAt(0)
            if i.widget(): i.widget().setParent(None)
        for idx,card in enumerate(self.channel_cards):
            self.gl.addWidget(card,idx//cols,idx%cols)

    def resizeEvent(self,e):
        self._layout_grid(); super().resizeEvent(e)

    def _set_all(self):
        try: v=float(self.ginput.text())
        except: return
        self.driver.i[:]=v
        for c in self.channel_cards:
            c.update_current_display(); c.setStyleSheet(c.success_style)
            QtCore.QTimer.singleShot(800,lambda w=c: w.setStyleSheet(w.base_style))

    def _get_all(self):
        for c in self.channel_cards: c.get_reading()

    def _open_funcs(self):
        self.fw=FunctionsWindow(self.driver,self); self.fw.show()


def main():
    app=QtWidgets.QApplication(sys.argv)
    app.setFont(QtGui.QFont("Segoe UI",10))
    mw=MainWindow(); mw.show(); sys.exit(app.exec_())

if __name__=='__main__':
    main()