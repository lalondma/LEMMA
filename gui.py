import tkinter as tk
from tkinter import scrolledtext, ttk
from PIL import Image, ImageTk
import subprocess
import json
import os
import sys
import threading
from configs import demo_root

current_example = None

def run_lemma(input_file_path, output_area):
    python_executable = sys.executable
    process = subprocess.Popen(
        [python_executable, "-u", "lemma.py", "--input_file_name", input_file_path, "--use_offline_image"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    def read_output(pipe, is_error=False):
        for line in iter(pipe.readline, ''):
            if "Lemma Component" in line:
                output_area.after(0, lambda: output_area.insert(tk.END, line, "bold"))
            else:
                if is_error:
                    output_area.after(0, output_area.insert, tk.END, f"ERROR: {line}")
                else:
                    output_area.after(0, output_area.insert, tk.END, f"{line}")
            output_area.after(0, output_area.yview, tk.END)
        pipe.close()

    stdout_thread = threading.Thread(target=read_output, args=(process.stdout, False))
    stderr_thread = threading.Thread(target=read_output, args=(process.stderr, True))

    stdout_thread.start()
    stderr_thread.start()

    stdout_thread.join()
    stderr_thread.join()
    process.wait()

def execute():
    if not current_example:
        output_area.insert(tk.END, "Error: No example file selected.\n")
        output_area.yview(tk.END)
        return

    input_file_path = os.path.join(demo_root, current_example)
    if not os.path.exists(input_file_path):
        output_area.insert(tk.END, f"Error: The example file '{input_file_path}' does not exist.\n")
        output_area.yview(tk.END)
        return
    
    output_area.insert(tk.END, f"Example file '{input_file_path}' found. Running lemma...\n")
    output_area.yview(tk.END)
    threading.Thread(target=run_lemma, args=(input_file_path, output_area), daemon=True).start()

def load_example(file_name):
    global current_example
    current_example = file_name  # Update the selected example
    file_path = os.path.join(demo_root, file_name)
    try:
        with open(file_path, 'r') as f:
            example_json = json.load(f)

        if isinstance(example_json, list) and len(example_json) > 0:
            example_data = example_json[0]
            output_area.delete("1.0", tk.END)
            image_url = example_data.get("image_url", "")
            if image_url:
                try:
                    image_path = os.path.join(demo_root, image_url)
                    img = Image.open(image_path)
                    img.thumbnail((350, 350))
                    img_tk = ImageTk.PhotoImage(img)
                    image_label.config(image=img_tk)
                    image_label.image = img_tk
                except Exception as e:
                    output_area.insert(tk.END, f"Error loading image: {str(e)}\n")
            else:
                output_area.insert(tk.END, "No image URL found in JSON\n")
            
            label_value = example_data.get("label", -1)
            if label_value == 0:
                status_icon = " ✔️"
                text_color = "green"
            elif label_value == 1:
                status_icon = " ❌"
                text_color = "red"
            else:
                status_icon = ""
                text_color = "black"

            original_post = example_data.get("original_post", "No original_post found.")
            original_post_label.config(text=f"Original Post: {original_post}{status_icon}", foreground=text_color)
            output_area.yview(tk.END)
        else:
            output_area.insert(tk.END, "Error: The JSON is empty or malformed.\n")
            output_area.yview(tk.END)
    except FileNotFoundError:
        output_area.insert(tk.END, f"Error: The file '{file_name}' was not found.\n")
        output_area.yview(tk.END)
    except json.JSONDecodeError:
        output_area.insert(tk.END, "Error: The file contains invalid JSON.\n")
        output_area.yview(tk.END)

def populate_example_menu():
    example_menu.menu.delete(0, tk.END)
    if not os.path.exists(demo_root):
        output_area.insert(tk.END, "Error: demo_root directory does not exist.\n")
        return
    
    json_files = [f for f in os.listdir(demo_root) if f.endswith(".json")]
    if not json_files:
        output_area.insert(tk.END, "No JSON files found in demo_root.\n")
        return
    
    for file_name in json_files:
        example_menu.menu.add_command(label=file_name, command=lambda f=file_name: load_example(f))

app = tk.Tk()
app.title("LEMMA DEMO")
app.geometry("860x860")
app.config(padx=20, pady=20)

frame = ttk.Frame(app)
frame.pack(pady=20, fill=tk.BOTH, expand=True)

input_frame = ttk.Frame(frame)
input_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

label = ttk.Label(input_frame, text="Select an example to view the image and post:", font=("Arial", 12))
label.grid(row=0, column=0, pady=10, columnspan=2)

example_menu = ttk.Menubutton(input_frame, text="Select Example", style="TButton")
example_menu.menu = tk.Menu(example_menu, tearoff=0)
example_menu["menu"] = example_menu.menu
example_menu.grid(row=1, column=0, pady=10, columnspan=2)

populate_example_menu()
image_and_post_frame = ttk.Frame(input_frame)
image_and_post_frame.grid(row=2, column=0, padx=10, pady=10, columnspan=2)

image_label = ttk.Label(image_and_post_frame)
image_label.grid(row=0, column=0, columnspan=2)

original_post_label = ttk.Label(image_and_post_frame, text="", wraplength=800, justify="center", font=("Arial", 12))
original_post_label.grid(row=1, column=0, pady=10, columnspan=2)

execute_button = ttk.Button(image_and_post_frame, text="Validate claim", command=execute, style="TButton")
execute_button.grid(row=2, column=0, pady=10, columnspan=2)

output_area = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, width=70, height=10, font=("Arial", 12))
output_area.grid(row=3, column=0, padx=10, pady=15, columnspan=2)
output_area.tag_configure("bold", font=("Arial", 12, "bold"))

frame.grid_rowconfigure(0, weight=1)
frame.grid_columnconfigure(0, weight=1)

app.mainloop()
