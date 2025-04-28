import tkinter as tk
from tkinter import ttk
import threading
import time

# === Mock driver with 60 channels ===
class MockQXOutput:
    def __init__(self, port, channels=60):
        self.v = [0.0] * channels
        self.i = [0.0] * channels

    def __getitem__(self, idx):
        return {"v": self.v[idx], "i": self.i[idx]}

    def __setitem__(self, idx, value):
        if 'v' in value:
            self.v[idx] = value['v']
        if 'i' in value:
            self.i[idx] = value['i']

driver = MockQXOutput("mock_port", channels=60)

class QontrolGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Qontrol 60-Channel Current Control")
        self.master.configure(bg="#f5f5f5")
        self.master.attributes('-fullscreen', True)
        self.master.bind("<Escape>", lambda e: self.exit_fullscreen())

        # Get screen size to decide number of columns
        screen_width = self.master.winfo_screenwidth()
        if screen_width >= 1920:
            self.num_cols = 10
        elif screen_width >= 1280:
            self.num_cols = 8
        else:
            self.num_cols = 6

        self.channel_labels = []
        self.current_labels = []
        self.current_entries = []

        style = ttk.Style()
        style.configure("TButton", font=("Segoe UI", 10), padding=5)
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("Bold.TLabel", font=("Segoe UI", 12, "bold"))

        title = tk.Label(master, text="Qontrol 60-Channel Dashboard", bg="#f5f5f5",
                         font=("Segoe UI", 20, "bold"), fg="#333")
        title.pack(pady=10)

        self.grid_frame = tk.Frame(master, bg="#f5f5f5")
        self.grid_frame.pack(fill="both", expand=True, padx=20)

        for ch in range(60):
            row = ch // self.num_cols
            col = ch % self.num_cols

            frame = tk.Frame(self.grid_frame, relief="raised", bg="white", bd=1)
            frame.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            self.grid_frame.grid_columnconfigure(col, weight=1)
            self.grid_frame.grid_rowconfigure(row, weight=1)

            label = ttk.Label(frame, text=f"Ch {ch+1:02d}", style="Bold.TLabel")
            label.pack(pady=(5, 0))

            current_label = tk.Label(frame, text=f"{driver.i[ch]:.2f} mA", fg="#007acc",
                                     font=("Segoe UI", 11), bg="white")
            current_label.pack(pady=3)
            self.current_labels.append(current_label)

            entry = tk.Entry(frame, width=6, justify='center', font=("Segoe UI", 10))
            entry.insert(0, f"{driver.i[ch]:.2f}")
            entry.pack(pady=(0, 5))
            self.current_entries.append(entry)

            set_button = ttk.Button(frame, text="Set",
                                    command=lambda c=ch: self.set_individual_current(c))
            set_button.pack(pady=(0, 5))

        control_frame = tk.Frame(master, bg="#f5f5f5")
        control_frame.pack(pady=10)

        ttk.Button(control_frame, text="Set All Currents", command=self.set_all_currents).pack(side="left", padx=20)
        ttk.Button(control_frame, text="Exit", command=self.exit_app).pack(side="left", padx=10)

        self.refresh_interval_ms = 1000
        self.master.after(self.refresh_interval_ms, self.update_display)

    def set_individual_current(self, ch):
        try:
            value = float(self.current_entries[ch].get())
            driver.i[ch] = value
            print(f"✅ Set Channel {ch+1} to {value:.2f} mA")
            self.current_labels[ch].config(fg="green")
            self.master.after(500, lambda: self.current_labels[ch].config(fg="#007acc"))
        except ValueError:
            print(f"⚠️ Invalid input for Channel {ch+1}")
            self.current_labels[ch].config(fg="red")
            self.master.after(500, lambda: self.current_labels[ch].config(fg="#007acc"))

    def set_all_currents(self):
        for ch in range(60):
            try:
                value = float(self.current_entries[ch].get())
                driver.i[ch] = value
            except ValueError:
                print(f"⚠️ Invalid current input for channel {ch+1}")

    def update_display(self):
        for ch in range(60):
            self.current_labels[ch].config(text=f"{driver.i[ch]:.2f} mA")
        self.master.after(self.refresh_interval_ms, self.update_display)

    def exit_app(self):
        self.master.destroy()

    def exit_fullscreen(self):
        self.master.attributes('-fullscreen', False)

# === Launch App ===
if __name__ == "__main__":
    root = tk.Tk()
    app = QontrolGUI(root)
    root.mainloop()