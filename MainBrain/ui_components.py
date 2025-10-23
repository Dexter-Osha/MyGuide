import customtkinter as ctk
from tkinter import filedialog
from pdf_utils import open_pdf

# ---------- Note Popups ----------
def create_note_popup(master, notes_manager, font, parent_id=None, note_to_edit=None):
    popup = ctk.CTkToplevel(master)
    popup.title("Add/Edit Note")
    popup.geometry("400x250")

    entry_var = ctk.StringVar()
    if note_to_edit:
        entry_var.set(note_to_edit["text"])

    ctk.CTkLabel(popup, text="Note text:", font=font).pack(pady=10)
    entry = ctk.CTkEntry(popup, textvariable=entry_var, width=300, font=font)
    entry.pack(pady=5)

    pdf_path_var = {"path": None}

    def attach_pdf():
        filepath = filedialog.askopenfilename(title="Select PDF file",
                                              filetypes=[("PDF files", "*.pdf")])
        if filepath:
            pdf_path_var["path"] = filepath
            entry_var.set(filepath.split("/")[-1])  # insert filename into text

    attach_btn = ctk.CTkButton(popup, text="Attach PDF", command=attach_pdf, font=font)
    attach_btn.pack(pady=(5,10))

    def confirm():
        text = entry_var.get().strip()
        if text:
            if note_to_edit:
                note_to_edit["text"] = text
                if pdf_path_var["path"]:
                    note_to_edit["pdf_path"] = pdf_path_var["path"]
            else:
                notes_manager.add_note(text, parent_id=parent_id, pdf_path=pdf_path_var["path"])
            popup.destroy()

    btn_text = "Update Note" if note_to_edit else "Add Note"
    ctk.CTkButton(popup, text=btn_text, command=confirm, font=font).pack(pady=10)
    entry.focus()


# ---------- Collapse ----------
def toggle_collapse(note, notes_manager, render_fn):
    note["collapsed"] = not note.get("collapsed", True)
    notes_manager.save_notes()
    render_fn()


# ---------- Drag and Drop Helpers ----------
def make_draggable(widget, note_id, app, is_section=False):
    widget.bind("<Button-1>", lambda e: start_drag(e, widget, note_id, app, is_section))
    widget.bind("<B1-Motion>", lambda e: drag_motion(e, widget))
    widget.bind("<ButtonRelease-1>", lambda e: end_drag(e, widget, note_id, app, is_section))


def start_drag(event, widget, note_id, app, is_section):
    app.drag_data["widget"] = widget
    app.drag_data["y"] = event.y_root
    app.drag_data["note_id"] = note_id
    app.drag_data["is_section"] = is_section
    # If section, store child ids
    if is_section:
        app.drag_data["child_ids"] = [
            n["id"] for n in app.notes_manager.notes if n.get("parent_section_id") == note_id
        ]


def drag_motion(event, widget):
    dy = event.y_root - widget.winfo_rooty()
    widget.place(y=widget.winfo_y() + dy)


def end_drag(event, widget, note_id, app, is_section):
    widget.place_forget()  # remove temporary positioning
    notes = app.notes_manager.notes

    # Find dragged note index
    dragged_index = next((i for i, n in enumerate(notes) if n["id"] == note_id), None)
    if dragged_index is None:
        return

    # Determine new index based on drop position
    widget_y = event.y_root - app.scroll_frame.winfo_rooty()
    positions = []
    for i, child in enumerate(app.scroll_frame.winfo_children()):
        positions.append((i, child.winfo_y() + child.winfo_height()/2))

    new_index = dragged_index
    for i, pos in positions:
        if widget_y < pos:
            new_index = i
            break
        new_index = i + 1

    if is_section:
        # Move section and its children together
        section = notes.pop(dragged_index)
        children = [notes.pop(next(i for i, n in enumerate(notes) if n["id"] == cid)) for cid in app.drag_data.get("child_ids", [])]
        insert_list = [section] + children
        notes[new_index:new_index] = insert_list
    else:
        # Regular note
        note = notes.pop(dragged_index)
        notes.insert(new_index, note)

    app.notes_manager.save_notes()
    app.render_notes()
    app.drag_data = {"widget": None, "y": 0, "note_id": None, "is_section": False}
