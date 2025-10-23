import customtkinter as ctk

DATA_FILE = "data/notes_data.json"
PLACEHOLDER_COLOR = "#A0A0A0"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Factory function to create fonts after root exists
def get_default_font(size=14, weight="normal"):
    return ctk.CTkFont(size=size, weight=weight)
