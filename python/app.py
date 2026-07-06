'''
 * ============================================================================
 * @repo        espidf-atm
 *
 * @author      Marco Antônio Ranghetti
 * @github      github.com/mRangh
 * @email       marcoantonioranghetti@gmail.com
 * @academic    d2026008956@unifei.edu.br
 *
 * @version     1.0.0
 * @date        2026-07-05
 * @license     Apache License 2.0
 * ============================================================================
'''

import tkinter as tk
import data_base as db
from uart_client import UartClient

BG_COLOR = "#1e1e1e"
FG_COLOR = "#ffffff"
ENTRY_BG = "#2d2d2d"
BTN_COLOR = "#00e676"
BTN_HOVER = "#33ff99"
BTN_FG = "#000000"
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_TEXT = ("Segoe UI", 12)
FONT_MONEY = ("Segoe UI", 20, "bold")

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, width=220, height=45, radius=20, **kwargs):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, bd=0, **kwargs)
        self.command = command
        self.bg_color = BTN_COLOR
        self.fg_color = BTN_FG
        self.hover_bg = parent["bg"]
        self.hover_fg = BTN_COLOR

        self.rect = self.round_rectangle(2, 2, width-2, height-2, radius=radius,
                                         fill=self.bg_color, outline=self.bg_color, width=2)
        self.text_item = self.create_text(width/2, height/2, text=text,
                                          fill=self.fg_color, font=("Segoe UI", 11, "bold"))

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)

    def round_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1,
                  x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius,
                  x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2,
                  x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

    def on_enter(self, event):
        self.itemconfig(self.rect, fill=self.hover_bg, outline=self.hover_fg)
        self.itemconfig(self.text_item, fill=self.hover_fg)
        self.config(cursor="hand2")

    def on_leave(self, event):
        self.itemconfig(self.rect, fill=self.bg_color, outline=self.bg_color)
        self.itemconfig(self.text_item, fill=self.fg_color)
        self.config(cursor="arrow")

    def on_click(self, event):
        self.itemconfig(self.rect, fill=self.bg_color)
        self.itemconfig(self.text_item, fill=self.fg_color)

    def on_release(self, event):
        self.itemconfig(self.rect, fill=self.hover_bg)
        self.itemconfig(self.text_item, fill=self.hover_fg)
        if self.command:
            self.command()

class ATMApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ATM Sys - GUI")
        self.geometry("450x480")
        self.configure(bg=BG_COLOR)
        self.resizable(False, False)

        db.init_db()
        self.current_action = None
        self.current_user = None
        self.pending_amount = 0

        self.container = tk.Frame(self, bg=BG_COLOR)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (HomeScreen, CredentialsScreen, AmountScreen, BalanceScreen, StatusScreen):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomeScreen")

        self.uart = UartClient(port='/dev/ttyUSB0')
        self.is_connected = self.uart.connect()

        self.check_serial()

    def check_serial(self):
        msg = None

        if self.is_connected:
            try:
                msg = self.uart.read_line()
            except Exception as e:
                print("[PYTHON_ERR]: Run time desconnection!")
                self.is_connected = False
                self.uart.close()

        if msg:
            print(f"[UART]: {msg}")

            try:
                if msg.startswith("DONE"):
                    action = msg.split()[1]

                    if len(msg.split()) >= 3:
                        if action == 'DEPOSIT':
                            amount = int(msg.split()[2])
                        elif action == 'WITHDRAW':
                            amount = -int(msg.split()[2])

                        db.atl_balance(self.current_user, amount)
                        self.frames["StatusScreen"].show_status(
                            "Operation successfully completed",
                            f"{abs(amount)}€ {action.capitalize()} carried out\nReturning to main menu...",
                            delay=4000
                        )
            except Exception:
                ...

        self.after(100, self.check_serial)


    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

class HomeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller

        tk.Label(self, text="Electronic Safe", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=(35, 10))
        tk.Label(self, text="Select option:", font=FONT_TEXT, bg=BG_COLOR, fg="#aaaaaa").pack(pady=(0, 15))

        RoundedButton(self, "Deposit", command=lambda: self.set_action("Deposit")).pack(pady=6)
        RoundedButton(self, "Withdraw", command=lambda: self.set_action("Withdraw")).pack(pady=6)
        RoundedButton(self, "Check Balance", command=lambda: self.set_action("Check Balance")).pack(pady=6)

        tk.Frame(self, height=1, bg="#333333").pack(fill="x", padx=60, pady=(20, 15))

        tk.Label(self, text="New to the platform?", font=("Segoe UI", 10), bg=BG_COLOR, fg="#aaaaaa").pack(pady=(0, 2))

        self.lbl_new_user = tk.Label(self, text="New User", font=("Segoe UI", 10, "underline"), 
                                     bg=BG_COLOR, fg=BTN_COLOR, cursor="hand2")
        self.lbl_new_user.pack()

        self.lbl_new_user.bind("<Button-1>", lambda e: self.set_action("New User"))
        self.lbl_new_user.bind("<Enter>", lambda e: self.lbl_new_user.config(fg=BTN_HOVER))
        self.lbl_new_user.bind("<Leave>", lambda e: self.lbl_new_user.config(fg=BTN_COLOR))

    def set_action(self, action):
        self.controller.current_action = action
        self.controller.frames["CredentialsScreen"].clear_entries()
        self.controller.show_frame("CredentialsScreen")

class CredentialsScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller

        self.lbl_title = tk.Label(self, text="Login", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR)
        self.lbl_title.pack(pady=(40, 15))

        entry_kwargs = {"bg": ENTRY_BG, "fg": FG_COLOR, "insertbackground": FG_COLOR, 
                        "relief": "flat", "font": FONT_TEXT, "bd": 5}

        tk.Label(self, text="Name:", font=FONT_TEXT, bg=BG_COLOR, fg="#aaaaaa").pack(pady=(5, 0))
        self.entry_name = tk.Entry(self, width=25, **entry_kwargs)
        self.entry_name.pack(pady=5)

        tk.Label(self, text="Password:", font=FONT_TEXT, bg=BG_COLOR, fg="#aaaaaa").pack(pady=(5, 0))
        self.entry_pass = tk.Entry(self, show="*", width=25, **entry_kwargs)
        self.entry_pass.pack(pady=5)

        btn_frame = tk.Frame(self, bg=BG_COLOR)
        btn_frame.pack(pady=20)

        RoundedButton(btn_frame, "Back", command=lambda: controller.show_frame("HomeScreen"), width=120).pack(side="left", padx=10)
        RoundedButton(btn_frame, "Next", command=self.process_credentials, width=120).pack(side="right", padx=10)

        self.lbl_error = tk.Label(self, text="", font=("Segoe UI", 11), bg=BG_COLOR, fg="#ff5252")
        self.lbl_error.pack(pady=5)

    def clear_entries(self):
        self.entry_name.delete(0, tk.END)
        self.entry_pass.delete(0, tk.END)
        self.lbl_error.config(text="")
        if self.controller.current_action == "New User":
            self.lbl_title.config(text="Register new user")
        else:
            self.lbl_title.config(text=f"Login: {self.controller.current_action}")

    def process_credentials(self):
        u_name = self.entry_name.get()
        password = self.entry_pass.get()

        if not u_name or not password:
            self.lbl_error.config(text="Fill in all fields!", fg="#ff5252")
            return

        action = self.controller.current_action

        if action == "New User":
            success = db.new_user(u_name, password)
            if success:
                self.controller.frames["StatusScreen"].show_status(
                    "Success", "New user registered!\n\nReturning to main menu..."
                )
                self.controller.show_frame("StatusScreen")
            else:
                self.lbl_error.config(text="Registration failed or user already exists.", fg="#ff5252")

        elif action in ["Deposit", "Withdraw", "Check Balance"]:
            is_valid = db.verify_pass(u_name, password)
            if is_valid:
                self.controller.current_user = u_name

                if action == "Check Balance":
                    user_money, bank_money = db.check_balance(u_name)
                    self.controller.frames["BalanceScreen"].update_balance_labels(u_name, user_money, bank_money)
                    self.controller.show_frame("BalanceScreen")
                else:
                    self.controller.frames["AmountScreen"].clear_entries()
                    self.controller.show_frame("AmountScreen")
            else:
                self.lbl_error.config(text="Incorrect name or password!", fg="#ff5252")

class AmountScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller

        self.lbl_title = tk.Label(self, text="Amount:", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR)
        self.lbl_title.pack(pady=(50, 20))

        tk.Label(self, text="Enter value:", font=FONT_TEXT, bg=BG_COLOR, fg="#aaaaaa").pack(pady=5)

        self.entry_amount = tk.Entry(self, width=15, bg=ENTRY_BG, fg=FG_COLOR,
                                     insertbackground=FG_COLOR, relief="flat", font=FONT_TITLE, bd=5, justify="center")
        self.entry_amount.pack(pady=10)

        btn_frame = tk.Frame(self, bg=BG_COLOR)
        btn_frame.pack(pady=20)

        RoundedButton(btn_frame, "Back", command=lambda: controller.show_frame("CredentialsScreen"), width=120).pack(side="left", padx=10)
        RoundedButton(btn_frame, "Confirm", command=self.execute_action, width=120).pack(side="right", padx=10)

        self.lbl_error = tk.Label(self, text="", font=("Segoe UI", 11), bg=BG_COLOR, fg="#ff5252")
        self.lbl_error.pack(pady=5)

    def clear_entries(self):
        self.entry_amount.delete(0, tk.END)
        self.lbl_error.config(text="")
        self.lbl_title.config(text=f"Value to {self.controller.current_action}")

    def execute_action(self):
        amount_str = self.entry_amount.get()
        if not amount_str.isdigit():
            self.lbl_error.config(text="Please, enter a valid numeric value.")
            return

        amount = int(amount_str)
        action = self.controller.current_action.upper()

        if action == "WITHDRAW":
            user_money, bank_money = db.check_balance(self.controller.current_user)

            if user_money < amount:
                self.lbl_error.config(text="Insufficient account balance!")
                return

            if bank_money < amount:
                self.lbl_error.config(text="The machine does not have enough money!")
                return

        self.controller.pending_amount = amount

        if self.controller.is_connected:
            self.controller.uart.send_command(f"{action} {amount}")
            self.controller.frames["StatusScreen"].show_status(
                "Processing",
                "Communicating with the machine.\nPlease wait...",
                delay=None
            )
            self.controller.show_frame("StatusScreen")

        else:
            print("[PYTHON]: Run time reconnection attempt...")
            self.controller.is_connected = self.controller.uart.connect()

            if self.controller.is_connected:
                self.controller.uart.send_command(f"{action} {amount}")
                self.controller.frames["StatusScreen"].show_status(
                    "Processing",
                    "Communicating with the machine.\nPlease wait...",
                    delay=None
                )
                self.controller.show_frame("StatusScreen")
            else:
                self.controller.frames["StatusScreen"].show_status(
                    "Processment failed",
                    "Board disconnected.\nReturning to main menu...",
                    delay=4000
                )
                self.controller.show_frame("StatusScreen")

class BalanceScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller

        tk.Label(self, text="Balance inquiry", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=(40, 20))

        self.lbl_user = tk.Label(self, text="User: -", font=FONT_TEXT, bg=BG_COLOR, fg="#aaaaaa")
        self.lbl_user.pack(pady=5)

        tk.Label(self, text="Account balance:", font=FONT_TEXT, bg=BG_COLOR, fg="#aaaaaa").pack(pady=(20, 2))
        self.lbl_user_money = tk.Label(self, text="0€", font=FONT_MONEY, bg=BG_COLOR, fg=BTN_COLOR)
        self.lbl_user_money.pack()

        tk.Label(self, text="Overall bank balance:", font=FONT_TEXT, bg=BG_COLOR, fg="#aaaaaa").pack(pady=(20, 2))
        self.lbl_bank_money = tk.Label(self, text="0€", font=FONT_MONEY, bg=BG_COLOR, fg=BTN_COLOR)
        self.lbl_bank_money.pack()

        RoundedButton(self, "Main menu", command=lambda: controller.show_frame("HomeScreen"), width=180).pack(pady=40)

    def update_balance_labels(self, username, user_money, bank_money):
        self.lbl_user.config(text=f"Utilizador: {username}")
        self.lbl_user_money.config(text=f"{user_money}€")
        self.lbl_bank_money.config(text=f"{bank_money}€")

class StatusScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller
        self.timer_id = None
        self.lbl_title = tk.Label(self, text="Status", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR)
        self.lbl_title.pack(pady=(70, 20))

        self.lbl_message = tk.Label(self, text="", font=FONT_TEXT, bg=BG_COLOR, fg="#aaaaaa", justify="center")
        self.lbl_message.pack(pady=20)

        RoundedButton(self, "Main menu", command=self.go_home, width=180).pack(pady=40)

    def show_status(self, title, message, delay=4000):
        self.lbl_title.config(text=title)
        self.lbl_message.config(text=message)

        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None

        if delay is not None:
            self.timer_id = self.after(delay, self.go_home)

    def go_home(self):
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        self.controller.show_frame("HomeScreen")

if __name__ == "__main__":
    app = ATMApp()
    app.mainloop()