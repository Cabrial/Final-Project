import smtplib
import ssl
import tkinter as tk
from email.message import EmailMessage
from tkinter import ttk, messagebox
import sqlite3

conn = sqlite3.connect('shelter.db')

cur = conn.cursor()

conn.commit()

# Sample user data (username and password)
user_data = {
    "Pedro": "phc",
    "Vinicius": "vini",
}

bed_data = {f"Bed {i}": {"Guest Name": "", "Checkbox": None} for i in range(1, 25)}

def fetch_guest_data():
    cur.execute("SELECT * FROM guests")
    data = cur.fetchall()
    return data

def populate_guests_tab(guests_tab):
    guest_data = fetch_guest_data()

    guest_listbox = tk.Listbox(guests_tab)
    guest_listbox.pack(fill="both", expand=True)

    for guest in guest_data:
        guest_listbox.insert("end", f"Name: {guest[1]} {guest[2]}, Birth Date: {guest[3]}")

    # Create a button to open the guest request form
    request_button = tk.Button(guests_tab, text="Add a New Guest", command=request_user_creation)
    request_button.pack()

def login():
    username = username_entry.get()
    password = password_entry.get()

    if username in user_data and user_data[username] == password:
        messagebox.showinfo("Login Successful", "Welcome, " + username + "!")
        window.destroy()
        create_main_screen()
    else:
        messagebox.showerror("Login Failed", "Invalid username or password. Please try again.")

def create_beds_grid(bed_frame):
    row = 0
    col = 0

    for bed, data in bed_data.items():
        bed_label = tk.Label(bed_frame, text=bed)
        bed_label.grid(row=row, column=col, padx=10, pady=5)

        guest_name_entry = tk.Entry(bed_frame)
        guest_name_entry.insert(0, data["Guest Name"])
        guest_name_entry.grid(row=row + 1, column=col, padx=10, pady=5)
        data["Guest Name Entry"] = guest_name_entry

        checkbox = tk.Checkbutton(bed_frame)
        checkbox.grid(row=row + 1, column=col + 1, padx=10, pady=5)
        data["Checkbox"] = checkbox

        # Adjust the row and column for the next bed
        col += 2
        if col >= 12:  # Change the number of columns as needed
            col = 0
            row += 2

def create_main_screen():
    main_screen = tk.Tk()
    main_screen.title("Shelter Beds")
    main_screen.geometry("1200x400")

    notebook = ttk.Notebook(main_screen)
    current_guests_tab = ttk.Frame(notebook)
    guests_tab = ttk.Frame(notebook)

    notebook.add(current_guests_tab, text="Current Guests")
    notebook.add(guests_tab, text="Guests")

    notebook.pack(expand=1, fill="both")

    current_guests_label = tk.Label(current_guests_tab, text="Current Guests")
    current_guests_label.pack()

    bed_frame = tk.Frame(current_guests_tab)
    bed_frame.pack()

    create_beds_grid(bed_frame)

    populate_guests_tab(guests_tab)

    main_screen.mainloop()

def request_user_creation():
    def submit_request():
        # Retrieve the input values
        first_name = first_name_entry.get()
        last_name = last_name_entry.get()
        dob = dob_entry.get()

        # You can process the captured data as needed (e.g., store in the database)
        print("First Name:", first_name)
        print("Last Name:", last_name)
        print("DOB:", dob)

        conn = sqlite3.connect('shelter.db')

        cur = conn.cursor()

        cur.execute("INSERT INTO guests (first_name, last_name, birth_date) VALUES (?, ?, ?)", (first_name, last_name, dob))

        conn.commit()

        # Close the request window
        request_window.destroy()

    # Create a new window for the request
    request_window = tk.Tk()
    request_window.title("Request User Creation")
    request_window.geometry("300x200")

    # Label and Entry widgets for First Name
    first_name_label = tk.Label(request_window, text="First Name:")
    first_name_label.pack()
    first_name_entry = tk.Entry(request_window)
    first_name_entry.pack()

    # Label and Entry widgets for Last Name
    last_name_label = tk.Label(request_window, text="Last Name:")
    last_name_label.pack()
    last_name_entry = tk.Entry(request_window)
    last_name_entry.pack()

    # Label and Entry widgets for Date of Birth (DOB)
    dob_label = tk.Label(request_window, text="Date of Birth (YYYY-MM-DD):")
    dob_label.pack()
    dob_entry = tk.Entry(request_window)
    dob_entry.pack()

    # Button to submit the request
    submit_button = tk.Button(request_window, text="Submit", command=submit_request)
    submit_button.pack()

    request_window.mainloop()

# Create a new window for login
window = tk.Tk()
window.title("Login Interface")
window.geometry("300x200")

username_label = tk.Label(window, text="Username:")
username_label.pack()
username_entry = tk.Entry(window)
username_entry.pack()

password_label = tk.Label(window, text="Password:")
password_label.pack()
password_entry = tk.Entry(window, show="*")
password_entry.pack()

login_button = tk.Button(window, text="Login", command=login)
login_button.pack()

request_button = tk.Button(window, text="Request Account", command=request_user_creation)
request_button.pack()

window.mainloop()
