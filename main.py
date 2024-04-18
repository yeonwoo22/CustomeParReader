import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import os
import datetime

from parreader import ParReader, ParState
from parmanager import ParManager, ParMergeType

class FileLoaderApp:
    def __init__(self, root):
        
        self.files = {}
        self.parmanager = ParManager()
        
        self.root = root
        self.root.title("File Loader GUI")
        self.root.geometry("600x400")  # 초기 창 크기 설정

        self.canvas = tk.Canvas(root, bg='white')
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 파일 열기 버튼
        open_button = tk.Button(root, text="Open Files", command=self.open_file)
        open_button.pack(padx=10, pady=10)
        
        save_button = tk.Button(root, text="Save", command=self.save)
        save_button.pack(padx=10, pady=10)
        
        self.check = [tk.IntVar()]
        
        checkbox1 = tk.Checkbutton(root, text="Detail", variable=self.check[0])
        checkbox1.pack(padx=10, pady=10)
        
        self.mode = tk.IntVar()
        
        default_rad = tk.Radiobutton(root, text="Default", variable=self.mode, value=0)
        PBS_rad = tk.Radiobutton(root, text="PBS", variable=self.mode, value=1)
        Tafel_rad = tk.Radiobutton(root, text="Tafel", variable=self.mode, value=2)

        default_rad.pack()
        PBS_rad.pack()
        Tafel_rad.pack()
    
    def save(self):

        savepath = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        os.makedirs(savepath, exist_ok=True)
        self.parmanager.save(savepath, self.check, self.mode)

    def open_file(self):
        filepaths = filedialog.askopenfilenames(title="Select files")
        for filepath in filepaths:
            par = ParReader(filepath)
            self.parmanager.add(par)
        self.parmanager.sort()
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        for par in self.parmanager.files.values():
            self.add_file_group(par)
            
        self.mode.set(self.parmanager.type)
        
    def add_file_group(self, par : ParReader):
        if par.status == ParState.NOPAR: return
        
        filename = par.filename
        
        frame = tk.Frame(self.scrollable_frame, borderwidth=2, relief="groove", bg='white')
        frame.pack(fill="x", padx=5, pady=5)
        
        delete_button = tk.Button(frame, text="Delete", command=lambda: self.delete_file_group(par, frame))
        delete_button.pack(side="left", padx=5)

        filename_label = tk.Label(frame, text=f"Filename: {filename}", bg='white')
        filename_label.pack(side="left", padx=5)

        values = [f"Segment#{_}" for _ in range(par.max_segment)] if par.status == ParState.OK else ["Empty Data"]
        options_combobox = ttk.Combobox(frame, values=values, state="readonly")
        options_combobox.set("Segment#2")  # default value
        options_combobox.bind('<<ComboboxSelected>>', lambda event : self.changed(event, par))
        options_combobox.pack(side="left", padx=5)
    
    def changed(self, event, par):
        selected_value = event.widget.get()
        par.select_segment = int(selected_value.split("#")[-1])

    def delete_file_group(self, par, frame):
        frame.destroy()
        self.parmanager.remove(par.filepath)

root = tk.Tk()
app = FileLoaderApp(root)
root.mainloop()
