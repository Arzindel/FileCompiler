import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

EXCLUDED_NAMES = ["prompt.txt"]
EXCLUDED_PREFIXES = ["file_list", "key", "api_key"]

def should_exclude(filename):
    name = filename.lower()
    return (
        name in EXCLUDED_NAMES or
        any(name.startswith(prefix) for prefix in EXCLUDED_PREFIXES)
    )

def detect_language(file_name):
    ext = os.path.splitext(file_name)[1].lower()
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".json": "json",
        ".html": "html",
        ".css": "css",
        ".sh": "bash",
        ".bat": "bat",
        ".cmd": "bat",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".md": "markdown",
        ".txt": ""
    }.get(ext, "")

class FileExporterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fancy File Exporter")
        self.path_var = tk.StringVar()
        self.export_path_var = tk.StringVar()
        self.tree_items = {}      # item_id -> full path
        self.check_states = {}    # full path -> True/False

        self.setup_ui()

    def setup_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Project Folder:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.path_var, width=60).grid(row=0, column=1)
        ttk.Button(frame, text="Browse", command=self.browse_folder).grid(row=0, column=2)
        ttk.Button(frame, text="Fetch Files", command=self.fetch_files).grid(row=0, column=3)

        ttk.Label(frame, text="Export To:").grid(row=1, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.export_path_var, width=60).grid(row=1, column=1)
        ttk.Button(frame, text="Browse", command=self.browse_export_folder).grid(row=1, column=2)

        self.tree = ttk.Treeview(frame, selectmode="none")
        self.tree.grid(row=2, column=0, columnspan=4, sticky="nsew", pady=10)
        self.tree.bind("<Button-1>", self.toggle_checkbox)
        self.tree.bind("<<TreeviewClose>>", lambda e: self.force_all_open())

        self.tree.column("#0", anchor="w")
        self.root.rowconfigure(2, weight=1)
        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(1, weight=1)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=2, column=4, sticky='ns')
        self.tree.configure(yscrollcommand=vsb.set)

        ttk.Button(frame, text="Export", command=self.export_file).grid(row=3, column=0, columnspan=4, pady=10)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)

    def browse_export_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.export_path_var.set(folder)

    def fetch_files(self):
        self.tree.delete(*self.tree.get_children())
        self.tree_items.clear()
        self.check_states.clear()

        folder = self.path_var.get()
        if not os.path.isdir(folder):
            messagebox.showerror("Error", "Invalid project folder path.")
            return

        self.export_path_var.set(folder)

        def add_to_tree(path, parent=""):
            for item in sorted(os.listdir(path)):
                full_path = os.path.join(path, item)
                if os.path.isfile(full_path) and should_exclude(item):
                    continue

                item_id = self.tree.insert(parent, "end", text="[✓] " + item, open=True)
                self.tree_items[item_id] = full_path
                self.check_states[full_path] = True

                if os.path.isdir(full_path):
                    add_to_tree(full_path, item_id)
                    self.tree.item(item_id, open=True)

        add_to_tree(folder)
        self.force_all_open()

    def force_all_open(self):
        for item_id in self.tree.get_children(""):
            self.expand_all(item_id)

    def expand_all(self, item_id):
        self.tree.item(item_id, open=True)
        for child_id in self.tree.get_children(item_id):
            self.expand_all(child_id)

    def toggle_checkbox(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "tree":
            return

        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        full_path = self.tree_items.get(item_id)
        if full_path is None:
            return

        current = self.check_states.get(full_path, False)
        new_state = not current
        self.check_states[full_path] = new_state

        def update_tree_label(item_id, state):
            text = self.tree.item(item_id, "text")
            name = text[4:] if text.startswith("[✓] ") or text.startswith("[ ] ") or text.startswith("[~] ") else text
            symbol = "[✓] " if state else "[ ] "
            self.tree.item(item_id, text=symbol + name)

        def update_children(item_id, state):
            for child_id in self.tree.get_children(item_id):
                path = self.tree_items.get(child_id)
                if path:
                    self.check_states[path] = state
                    update_tree_label(child_id, state)
                update_children(child_id, state)

        def update_parents(item_id):
            parent_id = self.tree.parent(item_id)
            if not parent_id:
                return

            all_children = self.tree.get_children(parent_id)
            checked = 0
            total = 0

            for child in all_children:
                path = self.tree_items.get(child)
                if path is not None:
                    total += 1
                    if self.check_states.get(path, False):
                        checked += 1

            parent_path = self.tree_items.get(parent_id)
            if parent_path:
                if checked == total:
                    self.check_states[parent_path] = True
                    update_tree_label(parent_id, True)
                elif checked == 0:
                    self.check_states[parent_path] = False
                    update_tree_label(parent_id, False)
                else:
                    self.check_states[parent_path] = None
                    text = self.tree.item(parent_id, "text")[4:]
                    self.tree.item(parent_id, text="[~] " + text)

            update_parents(parent_id)

        update_tree_label(item_id, new_state)
        update_children(item_id, new_state)
        update_parents(item_id)

    def get_selected_files(self):
        return [
            path for path, checked in self.check_states.items()
            if checked is True and os.path.isfile(path)
        ]

    def export_file(self):
        selected_files = self.get_selected_files()
        source_root = self.path_var.get()
        export_root = self.export_path_var.get()

        if not selected_files:
            messagebox.showinfo("No Selection", "No files selected.")
            return
        if not os.path.isdir(export_root):
            messagebox.showerror("Error", "Invalid export path.")
            return

        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(export_root, f"file_list_{now}.txt")

        with open(output_file, "w", encoding="utf-8") as out:
            for full_path in selected_files:
                rel_path = os.path.relpath(full_path, source_root)
                language = detect_language(full_path)

                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                except Exception as e:
                    print(f"Error reading {rel_path}: {e}")
                    continue

                if lines and lines[0].startswith("#!"):
                    lines = lines[1:]

                content = "".join(lines)
                out.write("="*40 + "\n")
                out.write(f"File: {rel_path}\n")
                out.write("-"*40 + "\n")
                out.write(f"```{language}\n")
                out.write(content)
                if not content.endswith("\n"):
                    out.write("\n")
                out.write("```\n\n")

        messagebox.showinfo("Export Complete", f"Exported to:\n{output_file}")

def run_app():
    root = tk.Tk()
    root.geometry("900x700")
    FileExporterApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_app()
