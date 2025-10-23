import customtkinter as ctk
from config import DATA_FILE, PLACEHOLDER_COLOR, get_default_font
from ui_components import create_note_popup, toggle_collapse, make_draggable,delete_note_safe
from notes_manager import NotesManager
from ui_components import create_note_popup, toggle_collapse
from pdf_utils import open_pdf
from PIL import Image, ImageTk  # For search icon

class WorkNotesApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Interactive Work Notes")
        self.geometry("1000x650")

        # Create font AFTER root exists
        self.default_font = get_default_font()

        self.notes_manager = NotesManager(DATA_FILE)
        self.drag_data = {"widget": None, "y": 0, "note_id": None}

        saved_theme = self.notes_manager.load_theme()
        ctk.set_appearance_mode(saved_theme)

        self.setup_ui()
        self.render_notes()

    def setup_ui(self):
        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # ---------- Search Bar with Icon in Frame ----------
        self.search_var = ctk.StringVar()

        search_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        search_frame.pack(pady=10, padx=10, fill="x")

        # ---------- Load Magnifying Glass Images ----------
        from PIL import Image
        from customtkinter import CTkImage

        search_icon_light = Image.open("icons/magnifying_glass.png").resize((20, 20), Image.Resampling.LANCZOS)
        search_icon_light_ctk = CTkImage(light_image=search_icon_light, dark_image=search_icon_light, size=(20, 20))

        search_icon_dark = Image.open("icons/magnifying_glassDARKMODE.png").resize((20, 20), Image.Resampling.LANCZOS)
        search_icon_dark_ctk = CTkImage(light_image=search_icon_dark, dark_image=search_icon_dark, size=(20, 20))

        icon_label = ctk.CTkLabel(search_frame, image=search_icon_light_ctk, text="")
        icon_label.pack(side="left", padx=(0, 5))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Search notes... e.g., Project A",
            placeholder_text_color=PLACEHOLDER_COLOR,
            font=self.default_font
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self.render_notes())

        # ---------- Add Section / Add Note Buttons ----------
        self.add_section_btn = ctk.CTkButton(
            self.sidebar,
            text="Add Section",
            font=self.default_font,
            command=lambda: create_note_popup(self, self.notes_manager, self.default_font)
        )
        self.add_section_btn.pack(pady=(5, 5), padx=10, fill="x")

        self.add_note_btn = ctk.CTkButton(
            self.sidebar,
            text="Add Note",
            font=self.default_font,
            command=lambda: create_note_popup(self, self.notes_manager, self.default_font)
        )
        self.add_note_btn.pack(pady=(0, 15), padx=10, fill="x")

        # ---------- Scrollable Frame for Main Content ----------
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.scroll_frame.pack(fill="both", expand=True)

        # ---------- Theme Toggle (Light/Dark) ----------
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=10, padx=10)

        # Load saved theme from notes_manager
        saved_theme = self.notes_manager.load_theme()
        ctk.set_appearance_mode(saved_theme)
        initial_text = "Dark Mode" if saved_theme == "Dark" else "Light Mode"

        theme_var = ctk.StringVar(value=saved_theme)

        def toggle_theme():
            if theme_var.get() == "Dark":
                ctk.set_appearance_mode("Dark")
                icon_label.configure(image=search_icon_dark_ctk)
                theme_switch.configure(text="Dark Mode")
                self.notes_manager.save_theme("Dark")
            else:
                ctk.set_appearance_mode("Light")
                icon_label.configure(image=search_icon_light_ctk)
                theme_switch.configure(text="Light Mode")
                self.notes_manager.save_theme("Light")

        theme_switch = ctk.CTkSwitch(
            bottom_frame,
            text=initial_text,
            variable=theme_var,
            onvalue="Dark",
            offvalue="Light",
            command=toggle_theme,
            font=self.default_font
        )
        theme_switch.pack(fill="x")

        # Keep references to prevent garbage collection
        self.search_icon_light_ctk = search_icon_light_ctk
        self.search_icon_dark_ctk = search_icon_dark_ctk

    def render_notes(self):
        # Clear the scroll area first
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Sort notes: sections first, then children under them
        for note in self.notes_manager.notes:
            if not note.get("parent_section_id"):
                self.render_section(note)

    def render_section(self, sec):
        frame = ctk.CTkFrame(self.scroll_frame, corner_radius=5)
        frame.pack(fill="x", pady=(5, 2), padx=10)

        # Section header
        arrow_text = "▼" if not sec.get("collapsed", False) else "▶"
        collapse_btn = ctk.CTkButton(
            frame,
            text=arrow_text,
            width=30,
            command=lambda s=sec: self.toggle_section_dropdown(s),
            font=self.default_font
        )
        collapse_btn.pack(side="left", padx=(5, 2))

        sec_label = ctk.CTkLabel(frame, text=sec["text"], font=self.default_font)
        sec_label.pack(side="left", padx=5, pady=5)

        # Make draggable
        make_draggable(frame, sec["id"], self, is_section=True)

        # If expanded, render buttons and children
        if not sec.get("collapsed", False):
            btn_frame = ctk.CTkFrame(frame)
            btn_frame.pack(side="right", padx=5)

            add_btn = ctk.CTkButton(
                btn_frame,
                text="+ Note",
                font=self.default_font,
                width=70,
                command=lambda s=sec: create_note_popup(self, self.notes_manager, self.default_font, parent_id=s["id"])
            )
            edit_btn = ctk.CTkButton(
                btn_frame,
                text="Edit",
                font=self.default_font,
                width=50,
                command=lambda s=sec: create_note_popup(self, self.notes_manager, self.default_font, note_to_edit=s)
            )
            del_btn = ctk.CTkButton(
                btn_frame,
                text="Del",
                font=self.default_font,
                width=50,
                command=lambda n=sec: delete_note_safe(n, self)
            )

            for btn in [add_btn, edit_btn, del_btn]:
                btn.pack(side="left", padx=2)

            # Render children notes
            children = [n for n in self.notes_manager.notes if n.get("parent_section_id") == sec["id"]]
            for note in children:
                self.render_note(note, indent=30, app=self)

    def render_note(self, note, indent=0, app=None):
        frame = ctk.CTkFrame(self.scroll_frame, corner_radius=5)
        frame.pack(fill="x", pady=(2, 2), padx=(indent + 10, 10))

        text_label = ctk.CTkLabel(
            frame,
            text=note["text"],
            font=self.default_font,
            wraplength=500,
            justify="left",
        )
        text_label.pack(side="left", padx=5, pady=5)

        # PDF hyperlink
        if note.get("pdf_path"):
            pdf_btn = ctk.CTkButton(
                frame,
                text="Open PDF",
                font=self.default_font,
                command=lambda path=note["pdf_path"]: open_pdf(path),
            )
            pdf_btn.pack(side="right", padx=5)

        # Control buttons
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(side="right", padx=5)

        edit_btn = ctk.CTkButton(
            btn_frame,
            text="Edit",
            font=self.default_font,
            width=50,
            command=lambda n=note: create_note_popup(app, app.notes_manager, app.default_font, note_to_edit=n),
        )

        del_btn = ctk.CTkButton(
            btn_frame,
            text="Del",
            font=self.default_font,
            width=50,
            command=lambda n=note: delete_note_safe(n, app)
        )

        for btn in [edit_btn, del_btn]:
            btn.pack(side="left", padx=2)

        # Make draggable
        make_draggable(frame, note["id"], app, is_section=False)

    def toggle_section_dropdown(self, sec):
        # Toggle collapsed state
        sec["collapsed"] = not sec.get("collapsed", True)
        self.notes_manager.save_notes()
        self.render_notes()

        if not sec.get("collapsed"):
            # Add contextual buttons inside section frame
            frame_widgets = self.scroll_frame.winfo_children()
            for frame in frame_widgets:
                label = frame.winfo_children()[0]  # first child = label
                if label.cget("text") == sec["text"]:
                    # Add buttons only for this section
                    add_btn = ctk.CTkButton(
                        frame,
                        text="+ Note",
                        font=self.default_font,
                        command=lambda s=sec: create_note_popup(self, self.notes_manager, self.default_font,
                                                                parent_id=s["id"])
                    )
                    edit_btn = ctk.CTkButton(
                        frame,
                        text="Edit",
                        font=self.default_font,
                        command=lambda s=sec: create_note_popup(self, self.notes_manager, self.default_font,
                                                                note_to_edit=s)
                    )
                    del_btn = ctk.CTkButton(
                        frame,
                        text="Delete",
                        font=self.default_font,
                        command=lambda s=sec: self.delete_section(s)
                    )
                    # Pack buttons to the right
                    for btn in [del_btn, edit_btn, add_btn]:
                        btn.pack(side="right", padx=3)

    def delete_section(self, sec):
        self.notes_manager.delete_note(sec["id"])
        self.render_notes()
if __name__ == "__main__":
    app = WorkNotesApp()
    app.mainloop()
