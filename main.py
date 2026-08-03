import customtkinter as ctk
from gui import EV3App


# Appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# Start application
app = EV3App()

app.mainloop()