import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
from PIL import Image, ImageTk
import subprocess
import json
import os
import sys
import threading

def run_lemma(input_file_path, output_area):
    python_executable = sys.executable
    process = subprocess.Popen(
    [python_executable, "-u", "lemma.py", "--input_file_name", input_file_path, "--use_cache"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

    def read_output(pipe, is_error=False):
        for line in iter(pipe.readline, ''):
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

    process.wait()  # Wait for the process to finish

def execute():
    input_file_path = "data/example_input.json"
    
    if not os.path.exists(input_file_path):
        output_area.insert(tk.END, f"Error: The example file '{input_file_path}' does not exist.\n")
        output_area.yview(tk.END)
        return
    
    # If the file exists, just confirm and run the lemma
    output_area.insert(tk.END, f"Example file '{input_file_path}' found. Running lemma...\n")
    output_area.yview(tk.END)
    
    threading.Thread(target=run_lemma, args=(input_file_path, output_area), daemon=True).start()

def load_example():
    try:
        # Load the example JSON file
        with open('data/example_input.json', 'r') as f:
            example_json = json.load(f)

        if isinstance(example_json, list) and len(example_json) > 0:
            example_data = example_json[0]

            output_area.delete("1.0", tk.END)
            image_url = example_data.get("image_url", "")
            if image_url:
                try:
                    image_path = os.path.join(os.getcwd(), image_url)
                    img = Image.open(image_path)
                    img.thumbnail((350, 350))
                    img_tk = ImageTk.PhotoImage(img)

                    image_label.config(image=img_tk)
                    image_label.image = img_tk
                except Exception as e:
                    output_area.insert(tk.END, f"Error loading image: {str(e)}\n")
            else:
                output_area.insert(tk.END, "No image URL found in JSON\n")

            original_post = example_data.get("original_post", "No original_post found.")
            original_post_label.config(text=f"Original Post: {original_post}")
            output_area.yview(tk.END)

        else:
            output_area.insert(tk.END, "Error: The JSON is empty or malformed.\n")
            output_area.yview(tk.END)

    except FileNotFoundError:
        output_area.insert(tk.END, "Error: The file 'data/example_input.json' was not found.")
        output_area.yview(tk.END)
    except json.JSONDecodeError:
        output_area.insert(tk.END, "Error: The file contains invalid JSON.")
        output_area.yview(tk.END)

app = tk.Tk()
app.title("LEMMA DEMO")

# window size
app.geometry("860x860")

app.config(padx=20, pady=20)

# Create a frame to hold the text area and the image side by side
frame = ttk.Frame(app)
frame.pack(pady=20, fill=tk.BOTH, expand=True)

# Create another frame to contain the text box and the image
input_frame = ttk.Frame(frame)
input_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

# Label
label = ttk.Label(input_frame, text="Select an example to view the image and post:", font=("Arial", 12))
label.grid(row=0, column=0, pady=10, columnspan=2)

# Example menu button
example_menu = ttk.Menubutton(input_frame, text="Select Example", style="TButton")
example_menu.menu = tk.Menu(example_menu, tearoff=0)
example_menu["menu"] = example_menu.menu
example_menu.menu.add_command(label="Example 1", command=load_example)
example_menu.grid(row=1, column=0, pady=10, columnspan=2)

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

frame.grid_rowconfigure(0, weight=1)
frame.grid_columnconfigure(0, weight=1)

app.mainloop()
