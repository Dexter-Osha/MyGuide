import json
import os

class NotesManager:
    def __init__(self, data_file):
        self.data_file = data_file
        self.notes = []
        self.load_notes()

    def load_notes(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.notes = data.get("notes", [])
            except:
                self.notes = []
        else:
            self.notes = []

    def save_notes(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, "w") as f:
            json.dump({"notes": self.notes}, f, indent=2)

    def add_note(self, text, is_section=False, parent_id=None, pdf_path=None):
        note = {
            "text": text,
            "id": self.get_next_id(),
            "is_section": is_section,
            "parent_section_id": parent_id,
        }
        if is_section:
            note["collapsed"] = True
        if pdf_path:
            note["pdf_path"] = pdf_path
        self.notes.append(note)
        self.save_notes()
        return note

    def delete_note(self, note_id):
        note = next((n for n in self.notes if n["id"] == note_id), None)
        if not note:
            return
        if note.get("is_section"):
            # Remove children
            self.notes = [n for n in self.notes if n.get("parent_section_id") != note_id]
        self.notes = [n for n in self.notes if n["id"] != note_id]
        self.save_notes()

    def get_next_id(self):
        if not self.notes:
            return 1
        return max(n["id"] for n in self.notes) + 1
