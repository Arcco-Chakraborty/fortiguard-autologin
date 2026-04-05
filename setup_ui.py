import tkinter as tk
from tkinter import messagebox
from credentials import save_credentials, load_credentials


def show_setup_window(on_save=None) -> None:
    root = tk.Tk()
    root.title("FortiGuard Auto-Login Setup")
    root.geometry("350x210")
    root.resizable(False, False)
    root.eval("tk::PlaceWindow . center")

    tk.Label(root, text="College WiFi Credentials", font=("Arial", 12, "bold")).pack(
        pady=(20, 10)
    )

    frame = tk.Frame(root)
    frame.pack(padx=20)

    tk.Label(frame, text="Username:").grid(row=0, column=0, sticky="e", pady=6)
    username_var = tk.StringVar()
    tk.Entry(frame, textvariable=username_var, width=25).grid(row=0, column=1, padx=6)

    tk.Label(frame, text="Password:").grid(row=1, column=0, sticky="e", pady=6)
    password_var = tk.StringVar()
    tk.Entry(frame, textvariable=password_var, show="*", width=25).grid(
        row=1, column=1, padx=6
    )

    existing = load_credentials()
    if existing:
        username_var.set(existing[0])

    def _save():
        username = username_var.get().strip()
        password = password_var.get()
        if not username or not password:
            messagebox.showerror("Error", "Both fields are required.", parent=root)
            return
        save_credentials(username, password)
        root.destroy()
        if on_save:
            on_save()

    tk.Button(root, text="Save & Start", command=_save, width=15).pack(pady=15)
    root.mainloop()
