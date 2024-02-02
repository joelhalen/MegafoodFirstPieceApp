import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkinter.font import Font
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import csv

# Initialize the main application window
app = tk.Tk()
app.title("Quality Control Application")

# Set the application to nearly full-screen
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()
app.geometry(f"{screen_width-100}x{screen_height-100}+50+50")

# Define a custom font for headers
headerFont = Font(family="Helvetica", size=12, weight="bold")

# Load user data
def load_users():
    users = []
    with open('users.txt', 'r') as file:
        for line in file:
            username, _ = line.strip().split(':')
            users.append(username)
    return users

# Function to authenticate the user
def authenticate(username, pin):
    with open('users.txt', 'r') as file:
        for line in file:
            stored_username, stored_pin = line.strip().split(':')
            if username == stored_username and pin == stored_pin:
                return True
    return False


def parse_lot_number(lot_number):
    """Parse the lot number, removing leading '1's and '0's as specified."""
    # Convert to string, remove leading '1' and '0's if they exist, then convert back to integer
    lot_str = str(lot_number)
    if lot_str.startswith("10"):
        lot_str = lot_str[2:]
    return int(lot_str)


def login():
    username = user_var.get()
    pin = entry_pin.get()
    if authenticate(username, pin):
        login_frame.pack_forget()  # Hide the login frame
        blend_selection_frame.pack()  # Show the blend selection frame
        app.geometry("")  # Adjust the window size if necessary
    else:
        messagebox.showerror("Login failed", "Invalid username or PIN")


# Function to display the blend selection screen
def show_blend_selection():
    login_frame.pack_forget()
    blend_selection_frame.pack()

# Function to load and display the selected blend's past lot image and details
def load_blend_data():
    blend_id = blend_var.get()
    display_blend_info(blend_id)

    # Default image path
    default_image_path = f"img/past-lots/{blend_id}/past-lot.jpg"
    load_image(default_image_path, last_lot_image_label, "PAST", "green")


    # Update the lot selection dropdown with available lots
    update_lot_selection_dropdown(blend_id)


def update_lot_selection_dropdown(blend_id):
    directory = f"img/past-lots/{blend_id}/"
    try:
        # List all .png files in the directory
        files = [f for f in os.listdir(directory) if f.endswith('.png')]
        files.sort(reverse=True)  # Sort to have the most recent lots first
        lot_selection['values'] = files
        if files:
            lot_selection.set('past-lot.png')  # Default selection
        else:
            lot_selection.set('No other lots available')
    except FileNotFoundError:
        lot_selection.set('No other lots available')


# Function to display blend information from CSV
def display_blend_info(blend_id):
    with open('blend_data.csv', mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            if row['Code'] == blend_id:
                # Clear previous information
                text_description.config(state=tk.NORMAL)
                text_description.delete('1.0', tk.END)

                # Define the format for keys and values
                bold_font = Font(family="Helvetica", size=10, weight="bold")
                normal_font = Font(family="Helvetica", size=10, weight="normal")

                # Constructing the information string with formatting
                info_lines = [
                    ("Product", row['PRODUCT']),
                    ("Tablets Amount", int(row['Tablets Amount']) * 1000),
                    ("Kilos to Produce", row['Kilos to Produce']),
                    ("Tablet Size", row['Tablet Size']),
                    ("Tablet weight", row['Tablet weight'])
                ]

                for key, value in info_lines:
                    text_description.insert(tk.END, f"{key}: ", ('bold',))
                    text_description.insert(tk.END, f"{value}\n", ('normal',))

                # Disable editing
                text_description.config(state=tk.DISABLED)
                break


# Function to load and display an image

def load_image(path, label, overlay_text, overlay_color):
    try:
        img = Image.open(path)
        img.thumbnail((400, 400), Image.Resampling.LANCZOS)

        draw = ImageDraw.Draw(img)

        # Specify your font file and size
        font_path = "arial.ttf"  # Change to the path of your font file if not using a default font
        font_size = 20
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print("Default font will be used.")
            font = ImageFont.load_default()

        # Fixed position for the text, adjust as needed
        text_x = 10
        text_y = img.height - 30  # Position at the bottom, adjust as needed

        # Drawing text
        draw.text((text_x, text_y), overlay_text, font=font, fill=overlay_color)

        photo = ImageTk.PhotoImage(img)
        label.config(image=photo)
        label.image = photo  # Keep a reference to avoid garbage collection
    except FileNotFoundError:
        label.config(image="")
        messagebox.showerror("Error", "Image file not found.")


# Modify the upload_image function to use the new label for current lot images.
def upload_image():
    file_path = filedialog.askopenfilename()
    if file_path:
        # Use the new label for the current image
        load_image(file_path, current_lot_image_label, "CURRENT", "red")



def load_selected_lot_image(blend_id, selected_lot):
    image_path = f"img/past-lots/{blend_id}/{selected_lot}"
    load_image(image_path, last_lot_image_label, "PAST", "green")



# Display the company logo
logo_image = Image.open("img/megafood.jpg")
logo_photo = ImageTk.PhotoImage(logo_image.resize((600, 200), Image.Resampling.LANCZOS))
logo_label = tk.Label(app, image=logo_photo)
logo_label.pack()

# Setup the login frame
login_frame = tk.Frame(app)
login_frame.pack()
tk.Label(login_frame, text="Press Operator First Piece Past-Lot Comparison Application", font=headerFont).pack()

# User selection dropdown
user_var = tk.StringVar(login_frame)
users = load_users()
user_dropdown = ttk.Combobox(login_frame, textvariable=user_var, values=users, state="readonly")
user_dropdown.pack()

# PIN entry
tk.Label(login_frame, text="PIN:").pack()
entry_pin = tk.Entry(login_frame, show="*")
entry_pin.pack()

# Login button
tk.Button(login_frame, text="Login", command=login).pack()

# Setup the blend selection frame
blend_selection_frame = tk.Frame(app)

# Blend selection dropdown
blend_var = tk.StringVar(blend_selection_frame)
blend_dropdown = ttk.Combobox(blend_selection_frame, textvariable=blend_var, width=50, state="readonly")
blend_dropdown['values'] = ["1240B", "1370B"]
blend_dropdown.bind('<<ComboboxSelected>>', lambda event: load_blend_data())
blend_dropdown.pack()

lot_selection = ttk.Combobox(blend_selection_frame, width=50, state="readonly")
lot_selection.pack()
lot_selection.bind('<<ComboboxSelected>>', lambda event: load_selected_lot_image(blend_id, lot_selection.get()))

# Load blend data button
#tk.Button(blend_selection_frame, text="Load Blend Data", command=load_blend_data).pack()

# Upload current lot image button
tk.Button(blend_selection_frame, text="Upload Current Lot Image", command=upload_image).pack()

# Description label for blend information
# Replace label_description with text_description setup
text_description = tk.Text(blend_selection_frame, height=10, width=50)
text_description.pack()

# Configure tag styles for bold and normal text
bold_font = Font(family="Helvetica", size=10, weight="bold")
normal_font = Font(family="Helvetica", size=10)
text_description.tag_configure('bold', font=bold_font)
text_description.tag_configure('normal', font=normal_font)

# Initially, disable the text widget to prevent user editing
text_description.config(state=tk.DISABLED)

# Image labels for displaying lot images
image_label = tk.Label(blend_selection_frame)
image_label.pack()
last_lot_image_label = tk.Label(blend_selection_frame)
last_lot_image_label.pack()
# At the place where you define your GUI components, add another label for the current lot image.
current_lot_image_label = tk.Label(blend_selection_frame)  # This label will hold the current lot image.
current_lot_image_label.pack(side="right")  # Adjust layout as needed.

last_lot_image_label.pack(side="left")  # Ensure the past lot image label is also correctly positioned.

app.mainloop()
