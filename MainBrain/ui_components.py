import customtkinter as ctk
from tkinter import filedialog
from pdf_utils import open_pdf

# ---------- Note Popups ----------
def create_note_popup(master, notes_manager, font, parent_id=None, note_to_edit=None):
    popup = ctk.CTkToplevel(master)
    popup.title("Add/Edit Note")
    popup.geometry("650x350")  # Wider than before for long notes
    popup.attributes("-topmost", True)  # Always on top

    ctk.CTkLabel(popup, text="Note text:", font=font).pack(pady=10)

    # Frame to hold textbox + scrollbar
    text_frame = ctk.CTkFrame(popup)
    text_frame.pack(pady=5, padx=10, fill="both", expand=True)

    # Multi-line text box (keep same size)
    text_box = ctk.CTkTextbox(text_frame, width=500, height=150, font=font)
    text_box.pack(side="left", fill="both", expand=True)

    # Vertical scrollbar
    scrollbar = ctk.CTkScrollbar(text_frame, orientation="vertical", command=text_box.yview)
    scrollbar.pack(side="right", fill="y")
    text_box.configure(yscrollcommand=scrollbar.set)

    if note_to_edit:
        text_box.insert("0.0", note_to_edit["text"])

    pdf_path_var = {"path": None}

    def attach_pdf():
        filepath = filedialog.askopenfilename(title="Select PDF file",
                                              filetypes=[("PDF files", "*.pdf")])
        if filepath:
            pdf_path_var["path"] = filepath
            # Optional: show PDF filename at top of text box
            text_box.insert("0.0", f"[Attached PDF: {filepath.split('/')[-1]}]\n")

    attach_btn = ctk.CTkButton(popup, text="Attach PDF", command=attach_pdf, font=font)
    attach_btn.pack(pady=(5,5))

    def confirm():
        text = text_box.get("0.0", "end").strip()
        if text:
            if note_to_edit:
                note_to_edit["text"] = text
                if pdf_path_var["path"]:
                    note_to_edit["pdf_path"] = pdf_path_var["path"]
            else:
                notes_manager.add_note(text, parent_id=parent_id, pdf_path=pdf_path_var["path"])
            popup.destroy()
            if hasattr(master, "render_notes"):
                master.render_notes()

    btn_text = "Update Note" if note_to_edit else "Add Note"
    ctk.CTkButton(popup, text=btn_text, command=confirm, font=font).pack(pady=(5,10))

    text_box.focus()



# ---------- Collapse ----------
def toggle_collapse(note, notes_manager, render_fn):
    note["collapsed"] = not note.get("collapsed", True)
    notes_manager.save_notes()
    render_fn()


HIGHLIGHT_COLOR = "#D0E0FF"      # ghost highlight color
INSERT_LINE_COLOR = "#000000"    # black insertion line
INSERT_LINE_THICKNESS = 4        # thicker line for boundary emphasis


# ---------- Drag and Drop Helpers ----------
def make_draggable(widget, note_id, app, is_section=False):
    widget.bind("<Button-1>", lambda e: start_drag(e, widget, note_id, app, is_section))
    widget.bind("<B1-Motion>", lambda e: drag_motion(e, widget, app))
    widget.bind("<ButtonRelease-1>", lambda e: end_drag(e, widget, note_id, app, is_section))


def start_drag(event, widget, note_id, app, is_section):
    app.drag_data = {
        "widget": widget,
        "note_id": note_id,
        "is_section": is_section,
        "mouse_offset_y": event.y_root - widget.winfo_rooty(),
    }

    if is_section:
        app.drag_data["child_ids"] = [
            n["id"] for n in app.notes_manager.notes if n.get("parent_section_id") == note_id
        ]

    ghost = ctk.CTkFrame(widget.master, width=widget.winfo_width(), height=widget.winfo_height(), corner_radius=5)
    ghost.configure(fg_color=HIGHLIGHT_COLOR)
    ghost.place(x=widget.winfo_x(), y=widget.winfo_y())
    app.drag_data["ghost"] = ghost

    insert_line = ctk.CTkFrame(widget.master, width=widget.winfo_width(), height=2, fg_color=INSERT_LINE_COLOR)
    insert_line.place_forget()
    app.drag_data["insert_line"] = insert_line


def drag_motion(event, widget, app):
    ghost = app.drag_data.get("ghost")
    insert_line = app.drag_data.get("insert_line")
    if not ghost or not insert_line:
        return

    new_y = event.y_root - widget.master.winfo_rooty() - app.drag_data["mouse_offset_y"]
    scroll_height = widget.master.winfo_height()
    widget_height = widget.winfo_height()
    new_y = max(0, min(new_y, scroll_height - widget_height))
    ghost.place(y=new_y)

    children = [c for c in widget.master.winfo_children() if c not in (ghost, insert_line)]
    line_y = 0
    thickness = 2

    if new_y < children[0].winfo_y():  # top boundary
        line_y = children[0].winfo_y() - INSERT_LINE_THICKNESS // 2
        thickness = INSERT_LINE_THICKNESS
    elif new_y + widget_height > children[-1].winfo_y() + children[-1].winfo_height():  # bottom boundary
        line_y = children[-1].winfo_y() + children[-1].winfo_height() - INSERT_LINE_THICKNESS // 2
        thickness = INSERT_LINE_THICKNESS
    else:
        for i, child in enumerate(children):
            child_center = child.winfo_y() + child.winfo_height() / 2
            if new_y < child_center:
                line_y = child.winfo_y()
                break
            line_y = child.winfo_y() + child.winfo_height()

    insert_line.configure(height=thickness)
    insert_line.place(x=10, y=line_y)


def end_drag(event, widget, note_id, app, is_section):
    ghost = app.drag_data.get("ghost")
    insert_line = app.drag_data.get("insert_line")
    if ghost:
        ghost.destroy()
    if insert_line:
        insert_line.destroy()

    notes = app.notes_manager.notes
    dragged_index = next((i for i, n in enumerate(notes) if n["id"] == note_id), None)
    if dragged_index is None:
        app.drag_data = {}
        return

    widget_y = event.y_root - app.scroll_frame.winfo_rooty()
    positions = [(i, child.winfo_y() + child.winfo_height() / 2)
                 for i, child in enumerate(app.scroll_frame.winfo_children())]
    new_index = dragged_index
    for i, pos in positions:
        if widget_y < pos:
            new_index = i
            break
        new_index = i + 1

    if is_section:
        section = notes.pop(dragged_index)
        children = [notes.pop(next(i for i, n in enumerate(notes) if n["id"] == cid))
                    for cid in app.drag_data.get("child_ids", [])]
        insert_list = [section] + children
        notes[new_index:new_index] = insert_list
    else:
        note = notes.pop(dragged_index)
        notes.insert(new_index, note)

    app.notes_manager.save_notes()
    app.render_notes()
    app.drag_data = {}

def delete_note_safe(note, app):
    """
    Safely delete a note (section or child) using the main app instance.
    """
    if note.get("is_section"):
        # Remove children first
        child_ids = [n["id"] for n in app.notes_manager.notes if n.get("parent_section_id") == note["id"]]
        for cid in child_ids:
            app.notes_manager.delete_note(cid)
    app.notes_manager.delete_note(note["id"])
    app.render_notes()