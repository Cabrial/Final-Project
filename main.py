import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime


conn = sqlite3.connect('shelter.db')
cur = conn.cursor()
conn.commit()

def fetch_guest_data(search_query=None):
    if search_query:
        cur.execute("""
            SELECT guests.id, guests.first_name, guests.last_name, guests.birth_date,
                   booking.bed_number, booking.check_in_date, booking.check_out_date
            FROM guests
            LEFT JOIN booking ON guests.id = booking.guest_id
            WHERE guests.first_name LIKE ? OR guests.last_name LIKE ?
            ORDER BY guests.id DESC
        """, ('%' + search_query + '%', '%' + search_query + '%'))
    else:
        cur.execute("""
            SELECT guests.id, guests.first_name, guests.last_name, guests.birth_date,
                   booking.bed_number, booking.check_in_date, booking.check_out_date
            FROM guests
            LEFT JOIN booking ON guests.id = booking.guest_id
            ORDER BY guests.id DESC
        """)
    data = cur.fetchall()
    return data


def search_guests(search_query):
    search_results_text.delete(1.0, tk.END)  # Clear previous search results
    guest_data = fetch_guest_data(search_query)
    for guest in guest_data:
        search_results_text.insert(tk.END, f"Name: {guest[1]} {guest[2]}, Birth Date: {guest[3]}\n")

def populate_guests_tab(guests_tab):
    global search_results_text
    guest_data = fetch_guest_data()
    global guest_listbox

    guest_listbox = tk.Listbox(guests_tab)
    guest_listbox.pack(fill="both", expand=True)

    for guest in guest_data:
        guest_listbox.insert("end", f"Name: {guest[1]} {guest[2]}, Birth Date: {guest[3]}")

    assign_bed_button = tk.Button(guests_tab, text="Assign Bed", command=assign_bed)
    assign_bed_button.pack()

    search_entry = tk.Entry(guests_tab)
    search_entry.pack()

    search_button = tk.Button(guests_tab, text="Search", command=lambda: search_guests(search_entry.get()))
    search_button.pack()

    search_results_text = tk.Text(guests_tab, height=10, width=50)
    search_results_text.pack()

    request_button = tk.Button(guests_tab, text="Add a New Guest", command=guest_creation)
    request_button.pack()

    create_beds_grid(guests_tab)

def assign_bed():
    selected_index = guest_listbox.curselection()
    if selected_index:
        selected_guest = fetch_guest_data()[selected_index[0]]
        assign_bed_dialog(selected_guest)
    else:
        messagebox.showinfo("Bed Assignment", "Please select a guest before assigning a bed.")

def assign_bed_dialog(selected_guest):
    assign_bed_window = tk.Tk()
    assign_bed_window.title("Assign Bed")
    assign_bed_window.geometry("300x200")

    bed_label = tk.Label(assign_bed_window, text="Select Bed:")
    bed_label.pack()

    bed_options = list(range(1, 25))
    selected_bed = tk.StringVar()
    bed_dropdown = ttk.Combobox(assign_bed_window, values=bed_options)
    bed_dropdown.pack()

    def assign_and_close():
        global bed_frame
        selected_bed_value = bed_dropdown.get()
        assign_bed_action(assign_bed_window, selected_guest, selected_bed_value)

        update_current_guests_tab(bed_frame)

    assign_button = tk.Button(assign_bed_window, text="Assign", command=assign_and_close)
    assign_button.pack()

    assign_bed_window.mainloop()

def update_current_guests_tab(bed_frame):
    # Clear the existing content
    for widget in bed_frame.winfo_children():
        widget.destroy()

    # Recreate the bed grid with the updated data
    create_beds_grid(bed_frame)


def assign_bed_action(assign_bed_window, selected_guest, selected_bed):
    check_in_date = get_current_date()

    cur.execute("SELECT id FROM guests WHERE first_name = ? AND last_name = ?", (selected_guest[1], selected_guest[2]))
    result = cur.fetchone()
    guest_id = result[0] if result else None

    cur.execute("INSERT INTO booking (guest_id, bed_number, check_in_date) VALUES (?, ?, ?)",
                (guest_id, selected_bed, check_in_date))
    conn.commit()

    assign_bed_window.destroy()
    messagebox.showinfo("Bed Assignment", f"Bed {selected_bed} assigned for {selected_guest[1]} {selected_guest[2]}!")

    # Update the "Current Guests" tab
    update_current_guests_tab(bed_frame)



def get_current_date():
    # You may need to adjust this based on your date format and database requirements
    return datetime.today().strftime('%Y-%m-%d')




def login():
    username = username_entry.get()
    password = password_entry.get()

    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cur.fetchone()

    if user:
        messagebox.showinfo("Login Successful", "Welcome, " + username + "!")
        window.destroy()
        create_main_screen()
    else:
        messagebox.showerror("Login Failed", "Invalid username or password. Please try again.")

def create_beds_grid(bed_frame):
    row = 0
    col = 0
    total_beds = 24  # Assuming you have 24 beds

    for bed_number in range(1, total_beds + 1):
        guest_data = fetch_guest_for_bed(bed_number)

        if guest_data:
            guest_name = f"{guest_data[1]} {guest_data[2]}"
        else:
            guest_name = "No guest assigned to this bed"

        bed_label = tk.Label(bed_frame, text=f"Bed {bed_number}: {guest_name}")
        bed_label.grid(row=row, column=col, padx=10, pady=5)

        col += 1
        if col >= 6:
            col = 0
            row += 1

def fetch_guest_for_bed(bed_number):
    cur.execute("""
        SELECT guests.*
        FROM guests
        LEFT JOIN booking ON guests.id = booking.guest_id
        WHERE booking.bed_number = ?
    """, (bed_number,))
    return cur.fetchone()

def create_main_screen():
    global bed_frame
    main_screen = tk.Tk()
    main_screen.title("Shelter Beds")
    main_screen.geometry("1400x600")

    notebook = ttk.Notebook(main_screen)
    current_guests_tab = ttk.Frame(notebook)
    guests_tab = ttk.Frame(notebook)

    notebook.add(current_guests_tab, text="Current Guests")
    notebook.add(guests_tab, text="Guests")

    notebook.pack(expand=1, fill="both")

    current_guests_label = tk.Label(current_guests_tab, text="Current Guests")
    current_guests_label.grid(row=0, column=0, pady=10)

    bed_frame = tk.Frame(current_guests_tab)
    bed_frame.grid(row=1, column=0)

    create_beds_grid(bed_frame)

    populate_guests_tab(guests_tab)

    main_screen.mainloop()

def guest_creation():
    def update_guest_list():
        guest_data = fetch_guest_data()
        guest_listbox.delete(0, tk.END)
        for guest in guest_data:
            guest_listbox.insert("end", f"Name: {guest[1]} {guest[2]}, Birth Date: {guest[3]}")

    def submit_request():
        first_name = first_name_entry.get()
        last_name = last_name_entry.get()
        dob = dob_entry.get()

        cur.execute("INSERT INTO guests (first_name, last_name, birth_date) VALUES (?, ?, ?)", (first_name, last_name, dob))
        conn.commit()

        request_window.destroy()

        update_guest_list()

    request_window = tk.Tk()
    request_window.title("Guest Creation")
    request_window.geometry("300x200")

    first_name_label = tk.Label(request_window, text="First Name:")
    first_name_label.pack()
    first_name_entry = tk.Entry(request_window)
    first_name_entry.pack()

    last_name_label = tk.Label(request_window, text="Last Name:")
    last_name_label.pack()
    last_name_entry = tk.Entry(request_window)
    last_name_entry.pack()

    dob_label = tk.Label(request_window, text="Date of Birth (YYYY-MM-DD):")
    dob_label.pack()
    dob_entry = tk.Entry(request_window)
    dob_entry.pack()

    submit_button = tk.Button(request_window, text="Submit", command=submit_request)
    submit_button.pack()

    request_window.mainloop()

def request_user_creation():
    # Create a new window for the request
    request_window = tk.Tk()
    request_window.title("Request User Creation")
    request_window.geometry("300x200")

    full_name_label = tk.Label(request_window, text="Full Name:")
    full_name_label.pack()
    full_name_entry = tk.Entry(request_window)
    full_name_entry.pack()

    dob_label = tk.Label(request_window, text="Date of Birth:")
    dob_label.pack()
    dob_entry = tk.Entry(request_window)
    dob_entry.pack()

    def send_request():
        port = 465  # For SSL
        smtp_server = "smtp.gmail.com"
        sender_email = "pedrocabrialca@gmail.com"
        receiver_email = "pedrocabrial@gmail.com"
        password = "okia bqft zuel tloe"

        msg = EmailMessage()
        msg.set_content(f"Full Name: {full_name_entry.get()}\nDate of Birth: {dob_entry.get()}")
        msg['Subject'] = "New User Request!"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(sender_email, password)
                server.send_message(msg, from_addr=sender_email, to_addrs=receiver_email)
                messagebox.showinfo("Done", "Request sent!")
                request_window.destroy()

        except Exception as e:
            print("Error:", str(e))
            messagebox.showerror("Error", "Unable to send the request. Please try again later.")
            request_window.destroy()

    send_button = tk.Button(request_window, text="Send Request", command=send_request)
    send_button.pack()

    request_window.mainloop()


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