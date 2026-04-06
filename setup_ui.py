import customtkinter as ctk
from credentials import save_credentials, load_credentials


def show_setup_window(on_save=None) -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("FortiGuard Auto-Login")
    root.geometry("420x340")
    root.resizable(False, False)

    # Center on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 420) // 2
    y = (root.winfo_screenheight() - 340) // 2
    root.geometry(f"+{x}+{y}")

    # Header
    ctk.CTkLabel(
        root, text="BITS WiFi Auto-Login",
        font=ctk.CTkFont(size=22, weight="bold"),
    ).pack(pady=(30, 5))

    ctk.CTkLabel(
        root, text="Enter your FortiGuard credentials",
        font=ctk.CTkFont(size=13),
        text_color="gray",
    ).pack(pady=(0, 20))

    # Form
    frame = ctk.CTkFrame(root, fg_color="transparent")
    frame.pack(padx=40, fill="x")

    username_entry = ctk.CTkEntry(
        frame, placeholder_text="Username (e.g. F20250719)", height=38,
    )
    username_entry.pack(fill="x", pady=(0, 12))

    password_entry = ctk.CTkEntry(
        frame, placeholder_text="Password", show="*", height=38,
    )
    password_entry.pack(fill="x", pady=(0, 8))

    # Pre-fill username if credentials exist
    existing = load_credentials()
    if existing:
        username_entry.insert(0, existing[0])

    # Error label (hidden by default)
    error_label = ctk.CTkLabel(
        frame, text="", text_color="#ff4444",
        font=ctk.CTkFont(size=12),
    )
    error_label.pack(pady=(0, 4))

    def _save():
        username = username_entry.get().strip()
        password = password_entry.get()
        if not username or not password:
            error_label.configure(text="Both fields are required")
            return
        save_credentials(username, password)
        root.destroy()
        if on_save:
            on_save()

    ctk.CTkButton(
        frame, text="Save & Start", command=_save,
        height=42, font=ctk.CTkFont(size=14, weight="bold"),
        corner_radius=8,
    ).pack(fill="x", pady=(8, 0))

    # Footer
    ctk.CTkLabel(
        root, text="Credentials are stored securely in your OS credential manager",
        font=ctk.CTkFont(size=11),
        text_color="gray",
    ).pack(side="bottom", pady=15)

    root.mainloop()
