import tkinter as tk
from io import BytesIO
from tkinter import messagebox, filedialog, ttk, simpledialog
from tkinter.font import Font

import requests
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import csv
from database.database import DatabaseManager

def load_users():
    users = db_manager.fetch_all_users()
    return [user['username'] for user in users]

def authenticate(username, pin):
    return db_manager.authenticate_user(username, pin)

def display_blend_info(blend_id):
    blend_info = db_manager.fetch_blend_info(blend_id)
    if blend_info:
        text_description.config(state=tk.NORMAL)
        text_description.delete('1.0', tk.END)

        info_lines = [
            ("Product", blend_info['product']),
            ("Tablets Amount", blend_info['tablets_amount'] * 1000),
            ("Kilos to Produce", blend_info['kilos_to_produce']),
            ("Tablet Size", blend_info['tablet_size']),
            ("Tablet weight", blend_info['tablet_weight'])
        ]

        for key, value in info_lines:
            text_description.insert(tk.END, f"{key}: ", ('bold',))
            text_description.insert(tk.END, f"{value}\n", ('normal',))

        # Disable editing
        text_description.config(state=tk.DISABLED)


def parse_lot_number(lot_number):
    lot_str = str(lot_number)
    if lot_str.startswith("10"):
        # only remove first two if it's still in the 10,000s,
        # although it'll be a while before we reach 11000 I suppose
        lot_str = lot_str[2:]
    else:
        lot_str = lot_str[1:]
    return int(lot_str)


user_initials = ""

def login():
    global user_initials
    username = user_var.get()
    pin = entry_pin.get()
    if authenticate(username, pin):
        user_initials = get_initials(username)
        login_frame.pack_forget()
        blend_selection_frame.pack()
        app.geometry("")
    else:
        messagebox.showerror("Login failed", "Invalid username or PIN")

def get_initials(full_name):
    words = full_name.split()
    initials = [word[0].upper() for word in words]
    return ''.join(initials)

def show_blend_selection():
    login_frame.pack_forget()
    blend_selection_frame.pack()


def update_lot_selection_dropdown(blend_id):
    # Fetch lot numbers from the database
    lot_numbers = db_manager.fetch_lot_numbers_for_blend(blend_id)

    if lot_numbers:
        # Update the dropdown values with the fetched lot numbers
        lot_selection['values'] = lot_numbers
        lot_selection.set(lot_numbers[0])  # Optionally set the first lot number as the default selection
    else:
        lot_selection.set('No lots available')



# Function to load and display the selected blend's past lot image and details
def load_blend_data():
    blend_id = blend_var.get()  # Get the selected blend_id from blend_var
    display_blend_info(blend_id)

    image_path, lot_number = db_manager.fetch_image_info_for_blend(blend_id)
    update_lot_selection_dropdown(blend_id)
    if image_path and lot_number:
        overlay_text = f"PAST (Lot {lot_number})"
        load_image_from_url(image_path, last_lot_image_label, overlay_text, "green")
    else:
        messagebox.showinfo("Info", "No past lot image found for this blend.")

def load_image_from_url(url, label, overlay_text, overlay_color):
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        # Proceed with resizing, drawing overlay text, and displaying the image as before
        img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        # Assuming you have a function to draw overlay text on the image
        draw_text_overlay(img, overlay_text, overlay_color)
        photo = ImageTk.PhotoImage(img)
        label.config(image=photo)
        label.image = photo  # Keep a reference
    except Exception as e:
        print(f"Error loading image from URL: {e}")
        label.config(image="")
        messagebox.showerror("Error", f"Failed to load image from URL. {e}")

def draw_text_overlay(img, overlay_text, overlay_color):
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

def upload_image_to_server(blend_id):
    next_lot_number = db_manager.find_next_lot(blend_id)
    if next_lot_number == 0:
        next_lot_number = ask_for_lot_number()
    if next_lot_number is None:  # User cancelled the operation
        return
    file_path = filedialog.askopenfilename()
    if file_path:
        files = {'image': open(file_path, 'rb')}
        data = {'blend_id': blend_id, 'lot_number': str(next_lot_number)}
        response = requests.post('http://51.81.166.148:25050/upload', files=files, data=data)
        if response.status_code == 200:
            image_url = response.json().get('image_path')
            overlay_text = f"CURRENT ({next_lot_number})"
            load_image_from_url(image_url, current_lot_image_label, overlay_text, "red")
            db_manager.insert_lot_image(blend_id, next_lot_number, image_url)
            messagebox.showinfo("Success", "Image uploaded successfully")
            tk.Button(blend_selection_frame, text="Mark as Verified", command=lambda: db_manager.mark_confirmed(user_initials, blend_id, next_lot_number)).pack()
        else:
            messagebox.showerror("Error", "Failed to upload image")


def load_selected_lot_image():
    blend_id = blend_var.get()  # Get the selected blend_id from blend_var
    selected_lot = lot_selection.get()  # Get the selected lot number
    image_path = f"http://51.81.166.148:25050/images/{blend_id}/{selected_lot}"
    load_image_from_url(image_path, last_lot_image_label, f"PAST ({selected_lot})", "green")


def update_blend_dropdown():
    blend_codes = db_manager.fetch_valid_blends()
    blend_dropdown['values'] = blend_codes
    if blend_codes:
        blend_dropdown.set(blend_codes[0])  # Optionally set the first blend code as the default selection
    else:
        blend_dropdown.set('No blends available')

def ask_for_lot_number():
    next_lot_number = simpledialog.askinteger("Input", "Last lot number unknown. Please enter a lot number:", parent=app)
    if next_lot_number is None:
        messagebox.showerror("Error", "No lot number entered. Cancelled.")
        return None
    return next_lot_number


if __name__ == "__main__":
    db_manager = DatabaseManager()
    # Initialize the main application window
    app = tk.Tk()
    app.title("MegaFood Quality Control - Pressing")

    # Set the application to nearly full-screen
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()
    app.geometry(f"{screen_width - 100}x{screen_height - 100}+50+50")

    # Define a custom font for headers
    headerFont = Font(family="Helvetica", size=12, weight="bold")

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
    blend_dropdown.bind('<<ComboboxSelected>>', lambda event, blend_id=blend_var.get(): load_blend_data())
    update_blend_dropdown()
    blend_dropdown.pack()

    lot_selection = ttk.Combobox(blend_selection_frame, width=50, state="readonly")
    lot_selection.pack()
    lot_selection.bind('<<ComboboxSelected>>', lambda event, blend_id=blend_var.get(): load_selected_lot_image())


    # Upload current lot image button
    tk.Button(blend_selection_frame, text="Upload Current Lot Image", command=lambda: upload_image_to_server(blend_var.get())).pack()

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
