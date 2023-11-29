import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime, timedelta

conn = sqlite3.connect('shelter.db')
cur = conn.cursor()
conn.commit()

timer_id = None

def start_timer():
    global timer_id
    timer_id = window.after(21600000, update_tabs)

def update_tabs():
    update_current_guests_tab(bed_frame)
    update_suspensions_tab(suspensions_frame)
    print("tables updated")
    start_timer()


def fetch_suspensions_data(search_query=None):
    if search_query:
        cur.execute("""
            SELECT id, guest_first_name, guest_last_name, suspension_date, return_date, reason
            FROM suspensions
            WHERE guest_first_name LIKE ? OR guest_last_name LIKE ?
            ORDER BY id DESC
        """, ('%' + search_query + '%', '%' + search_query + '%'))
    else:
        cur.execute("""
            SELECT id, guest_first_name, guest_last_name, suspension_date, return_date, reason
            FROM suspensions
            ORDER BY id DESC
        """)
    data = cur.fetchall()
    return data


def update_suspensions_tab(suspensions_frame, search_query=None):
    suspensions_frame.delete(0, tk.END)

    if not search_query:
        suspensions_data = fetch_suspensions_data()
    else:
        suspensions_data = fetch_suspensions_data(search_query)

    for suspension in suspensions_data:
        suspension_text = f"Name: {suspension[1]} {suspension[2]}, Suspension Date: {suspension[3]}, Return Date: {suspension[4]}, Reason: {suspension[5]}\n"
        suspensions_frame.insert(tk.END, suspension_text)


def fetch_guest_data(search_query=None):
    guests = {}
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

    for guest in data:
        guest_id = guest[0]
        if guest_id not in guests:
            guests[guest_id] = guest

    return list(guests.values())


def search_guests(search_query):
    guest_listbox.delete(0, tk.END)

    guest_data = fetch_guest_data(search_query)
    for guest in guest_data:
        result_text = f"Name: {guest[1]} {guest[2]}, Birth Date: {guest[3]}\n"
        guest_listbox.insert(tk.END, result_text)


def populate_guests_tab(guests_tab):
    global search_results_text
    guest_data = fetch_guest_data()
    global guest_listbox

    search_entry = tk.Entry(guests_tab)
    search_entry.pack()

    search_button = tk.Button(guests_tab, text="Search", command=lambda: search_guests(search_entry.get()))
    search_button.pack()

    guest_listbox = tk.Listbox(guests_tab)
    guest_listbox.pack(fill="both", expand=True)

    for guest in guest_data:
        guest_listbox.insert("end", f"Name: {guest[1]} {guest[2]}, Birth Date: {guest[3]}")

    button_frame = tk.Frame(guests_tab)
    button_frame.pack(pady=10)

    assign_bed_button = tk.Button(button_frame, text="Assign Bed", command=assign_bed)
    assign_bed_button.pack(side="left", padx=10)

    request_button = tk.Button(button_frame, text="Add a New Guest", command=guest_creation)
    request_button.pack(side="left", padx=10)

    suspension_button = tk.Button(button_frame, text="Suspend Guest", command=suspend_guest)
    suspension_button.pack(side="left", padx=10)

    create_beds_grid(guests_tab)


def assign_bed():
    selected_index = guest_listbox.curselection()
    if selected_index:
        selected_guest_name = guest_listbox.get(selected_index[0])

        guest_data_from_db = fetch_guest_data()

        selected_guest_index = None
        selected_guest_name_parts = selected_guest_name.split(", Birth Date:")[0]

        for index, guest_info in enumerate(guest_data_from_db):
            db_guest_name_parts = f"{guest_info[1]} {guest_info[2]}"
            if selected_guest_name_parts == ("Name: " + db_guest_name_parts):
                selected_guest_index = index
                break

        if selected_guest_index is not None:
            selected_guest = guest_data_from_db[selected_guest_index]
            assign_bed_dialog(selected_guest)
            return
        else:
            print("No matching guest found.")

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
    for widget in bed_frame.winfo_children():
        widget.destroy()

    create_beds_grid(bed_frame)


def assign_bed_action(assign_bed_window, selected_guest, selected_bed):
    check_in_date = get_current_date()

    cur.execute("SELECT * FROM booking WHERE bed_number = ? AND bed_number != 0", (selected_bed,))
    existing_bed_assignments = cur.fetchall()

    if existing_bed_assignments:
        messagebox.showinfo("Bed Assignment", f"Bed {selected_bed} is already assigned to a guest.")
        return

    cur.execute("""
            SELECT id
            FROM suspensions
            WHERE guest_id = ? AND return_date >= DATE('now', 'localtime')
        """, (selected_guest[0],))
    suspended_record = cur.fetchone()

    if suspended_record:
        messagebox.showinfo("Bed Assignment",
                            f"{selected_guest[1]} {selected_guest[2]} is currently suspended. Cannot assign a bed.")
        return

    cur.execute("SELECT * FROM booking WHERE guest_id = ? AND bed_number != 0", (selected_guest[0],))
    existing_bed_assignments = cur.fetchall()

    if existing_bed_assignments:
        messagebox.showinfo("Bed Assignment", f"{selected_guest[1]} {selected_guest[2]} already has a bed assigned.")
        return

    cur.execute("INSERT INTO booking (guest_id, bed_number, check_in_date) VALUES (?, ?, ?)",
                (selected_guest[0], selected_bed, check_in_date))
    conn.commit()

    assign_bed_window.destroy()
    messagebox.showinfo("Bed Assignment",
                        f"Bed {selected_bed} assigned for {selected_guest[1]} {selected_guest[2]}!")

    update_current_guests_tab(bed_frame)


def get_current_date():
    return datetime.today().strftime('%Y-%m-%d')


def unassign_bed():
    selected_index = guest_listbox.curselection()
    unassign_bed_dialog()
    if selected_index:
        selected_guest = fetch_guest_data()[selected_index[0]]
        unassign_bed_dialog(selected_guest)


def unassign_bed_dialog():
    unassign_bed_window = tk.Tk()
    unassign_bed_window.title("Unassign Bed")
    unassign_bed_window.geometry("300x200")

    bed_label = tk.Label(unassign_bed_window, text="Select Bed:")
    bed_label.pack()

    bed_options = list(range(1, 25))
    selected_bed = tk.StringVar()
    bed_dropdown = ttk.Combobox(unassign_bed_window, values=bed_options)
    bed_dropdown.pack()

    def unassign_and_close():
        selected_bed_value = bed_dropdown.get()
        unassign_bed_action(unassign_bed_window, selected_bed_value)

        update_current_guests_tab(bed_frame)

    unassign_button = tk.Button(unassign_bed_window, text="Unassign", command=unassign_and_close)
    unassign_button.pack()

    unassign_bed_window.mainloop()


def unassign_bed_action(unassign_bed_window, selected_bed):
    checkout_date = get_current_date()

    cur.execute("UPDATE booking SET bed_number = 0, check_out_date = ? WHERE bed_number = ?",
                (checkout_date, selected_bed))
    conn.commit()

    unassign_bed_window.destroy()
    messagebox.showinfo("Bed Unassignment", f"Bed {selected_bed} unassigned!")

    update_current_guests_tab(bed_frame)


def login():
    global username_entry
    global username
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
    total_beds = 24

    checkboxes = []

    for bed_number in range(1, total_beds + 1):
        guest_data = fetch_guest_for_bed(bed_number)
        checkbox_var = tk.IntVar()

        if guest_data:
            guest_name = f"{guest_data[1]} {guest_data[2]}"
            checkbox = tk.Checkbutton(bed_frame, text=f"Bed {bed_number}: {guest_name}", variable=checkbox_var)
        else:
            checkbox = tk.Checkbutton(bed_frame, text=f"Bed {bed_number}: No guest assigned", variable=checkbox_var)

        checkbox.grid(row=row, column=col, padx=15, pady=10, sticky="w")
        checkboxes.append((checkbox, checkbox_var))

        col += 1
        if col >= 4:
            col = 0
            row += 1


    def clear_checked_checkboxes():
        for checkbox, checkbox_var in checkboxes:
            if checkbox_var.get() == 1:
                checkbox.deselect()

    clear_button = tk.Button(bed_frame, text="Clear Checked", command=clear_checked_checkboxes)
    clear_button.grid(row=row, column=0, columnspan=1, pady=10, padx=15, sticky="ew")

    return checkboxes





def fetch_guest_for_bed(bed_number):
    cur.execute("""
        SELECT guests.*
        FROM guests
        LEFT JOIN booking ON guests.id = booking.guest_id
        WHERE booking.bed_number = ?
    """, (bed_number,))
    return cur.fetchone()

first_name_entry = None
last_name_entry = None
username_entry = None
password_entry = None
admin_var = None

def create_main_screen():
    global bed_frame
    global suspensions_frame
    global first_name_entry, last_name_entry, username_entry, password_entry, admin_var
    main_screen = tk.Tk()
    main_screen.title("Shelter Beds")
    main_screen.geometry("840x700")

    notebook = ttk.Notebook(main_screen)
    current_guests_tab = ttk.Frame(notebook)
    guests_tab = ttk.Frame(notebook)
    suspensions_tab = ttk.Frame(notebook)

    is_admin = fetch_user_admin_status(username)

    def check_existing_user(first_name, last_name):

        query = "SELECT id FROM guests WHERE first_name = ? AND last_name = ?"

        cursor.execute(query, (first_name, last_name))
        result = cursor.fetchone()

        return result is not None

    def add_new_user():
        global first_name_entry, last_name_entry, username_entry, password_entry, admin_var

        new_first_name = first_name_entry.get()
        new_last_name = last_name_entry.get()
        new_username = username_entry.get()
        new_password = password_entry.get()
        is_admin_value = admin_var.get()

        success = add_user_to_db(new_first_name, new_last_name, new_username, new_password, is_admin_value)

        if success:
            messagebox.showinfo("Success", "User created successfully!")

            first_name_entry.delete(0, tk.END)
            last_name_entry.delete(0, tk.END)
            username_entry.delete(0, tk.END)
            password_entry.delete(0, tk.END)
            admin_var.set(0)


    if is_admin == 1:
        admin_tab = ttk.Frame(notebook)
        notebook.add(admin_tab, text="Admin")
        first_name_label = tk.Label(admin_tab, text="First Name:")
        first_name_label.pack()
        first_name_entry = tk.Entry(admin_tab)
        first_name_entry.pack()

        last_name_label = tk.Label(admin_tab, text="Last Name:")
        last_name_label.pack()
        last_name_entry = tk.Entry(admin_tab)
        last_name_entry.pack()

        username_label = tk.Label(admin_tab, text="Username:")
        username_label.pack()
        username_entry = tk.Entry(admin_tab)
        username_entry.pack()

        password_label = tk.Label(admin_tab, text="Password:")
        password_label.pack()
        password_entry = tk.Entry(admin_tab, show="*")
        password_entry.pack()

        admin_var = tk.IntVar()
        admin_checkbox = tk.Checkbutton(admin_tab, text="Admin", variable=admin_var)
        admin_checkbox.pack()

        add_user_button = tk.Button(admin_tab, text="Add User", command=add_new_user)
        add_user_button.pack()


    notebook.add(current_guests_tab, text="Current Guests")
    notebook.add(guests_tab, text="Guests")
    notebook.add(suspensions_tab, text="Suspensions")


    start_timer()

    suspensions_frame = tk.Listbox(suspensions_tab)
    suspensions_frame.pack(fill="both", expand=True)

    search_entry_suspensions = tk.Entry(suspensions_tab)
    search_entry_suspensions.pack()

    search_button_suspensions = tk.Button(suspensions_tab, text="Search",
                                          command=lambda: update_suspensions_tab(suspensions_frame,
                                                                                 search_entry_suspensions.get()))
    search_button_suspensions.pack()

    remove_suspension_button = tk.Button(suspensions_tab, text="Remove Suspension", command=remove_suspension)
    remove_suspension_button.pack()

    update_suspensions_tab(suspensions_frame)

    notebook.pack(expand=1, fill="both")

    current_guests_label = tk.Label(current_guests_tab, text="Current Guests")
    current_guests_label.grid(row=0, column=0, pady=10)

    bed_frame = tk.Frame(current_guests_tab)
    bed_frame.grid(row=1, column=0, pady=80)

    create_beds_grid(bed_frame)

    unassign_button = tk.Button(current_guests_tab, text="Unassign Bed", command=unassign_bed)
    unassign_button.grid(row=3, column=0, pady=50)

    populate_guests_tab(guests_tab)

    main_screen.mainloop()

def add_user_to_db(first_name, last_name, username, password, is_admin):

    conn = sqlite3.connect('shelter.db')
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    existing_user = cur.fetchone()

    if existing_user:

        messagebox.showerror("Error", "Username already exists. Please choose another username.")
        return False


    cur.execute("""
            INSERT INTO users (first_name, last_name, username, password, is_admin)
            VALUES (?, ?, ?, ?, ?)
        """, (first_name, last_name, username, password, is_admin))


    conn.commit()
    conn.close()

    messagebox.showinfo("Success", "User created successfully!")

    first_name_entry.delete(0, tk.END)
    last_name_entry.delete(0, tk.END)
    username_entry.delete(0, tk.END)
    password_entry.delete(0, tk.END)
    admin_var.set(0)


def fetch_user_admin_status(username):

    cur.execute("SELECT is_admin FROM users WHERE username=?", (username,))
    admin_status = cur.fetchone()
    return admin_status[0] if admin_status else 0



def suspend_guest():
    selected_index = guest_listbox.curselection()

    if selected_index:

        search_query = guest_listbox.get(selected_index[0])
        search_query_parts = search_query.split(", Birth Date:")
        search_name_parts = search_query_parts[0].split(": ")[1].split(" ")
        search_first_name = search_name_parts[0]
        search_last_name = search_name_parts[1]

        cur.execute("""
            SELECT guests.id, guests.first_name, guests.last_name, guests.birth_date,
                   booking.bed_number, booking.check_in_date, booking.check_out_date
            FROM guests
            LEFT JOIN booking ON guests.id = booking.guest_id
            WHERE guests.first_name = ? AND guests.last_name = ?
        """, (search_first_name, search_last_name))

        selected_guest = cur.fetchone()
        if selected_guest:
            selected_bed = fetch_bed_for_guest(selected_guest)
            suspend_guest_dialog(selected_guest, selected_bed)
        else:
            messagebox.showinfo("Suspension", "Selected guest details not found.")
    else:
        messagebox.showinfo("Suspension", "Please select a guest before suspending.")



def fetch_bed_for_guest(selected_guest):
    cur.execute("SELECT bed_number FROM booking WHERE guest_id = ?", (selected_guest[0],))
    bed = cur.fetchone()
    return bed[0] if bed else 0


def suspend_guest_dialog(selected_guest, selected_bed):
    suspend_guest_window = tk.Tk()
    suspend_guest_window.title("Suspend Guest")
    suspend_guest_window.geometry("300x250")

    guest_label = tk.Label(suspend_guest_window, text="Selected Guest:")
    guest_label.pack()

    guest_info_label = tk.Label(suspend_guest_window,
                                text=f"{selected_guest[1]} {selected_guest[2]}, Birth Date: {selected_guest[3]}")
    guest_info_label.pack()

    confirm_label = tk.Label(suspend_guest_window, text="For how long this guest will be suspended?")
    confirm_label.pack()

    duration_var = tk.StringVar(suspend_guest_window)
    duration_var.set("3 months")
    duration_options = ["3 months", "6 months", "Indefinite"]
    duration_dropdown = tk.OptionMenu(suspend_guest_window, duration_var, *duration_options)
    duration_dropdown.pack()

    reason_label = tk.Label(suspend_guest_window, text="Reason:")
    reason_label.pack()

    reason_entry = tk.Entry(suspend_guest_window)
    reason_entry.pack()

    confirm_button = tk.Button(suspend_guest_window, text="Suspend",
                               command=lambda: suspend_guest_action(suspend_guest_window, selected_guest,
                                                                    duration_var.get(), reason_entry.get(), selected_bed))
    confirm_button.pack()

    suspend_guest_window.mainloop()


def suspend_guest_action(suspend_guest_window, selected_guest, duration, reason, selected_bed):
    cur.execute('''SELECT id FROM suspensions
                       WHERE guest_id = ? AND return_date >= DATE('now', 'localtime')''',
                (selected_guest[0],))
    existing_suspension = cur.fetchone()

    if existing_suspension:
        messagebox.showinfo("Suspension",
                            "This guest is already suspended. Cannot suspend again within the specified duration.")
        return

    cur.execute('''INSERT INTO suspensions (guest_id, guest_first_name, guest_last_name, suspension_date, return_date, reason)
                       VALUES (?, ?, ?, DATE('now', 'localtime'), ?, ?)''',
                (selected_guest[0], selected_guest[1], selected_guest[2], calculate_return_date(duration), reason))

    cur.execute("UPDATE booking SET bed_number = 0 WHERE guest_id = ?", (selected_guest[0],))
    conn.commit()

    messagebox.showinfo("Suspension", f"Guest {selected_guest[1]} {selected_guest[2]} suspended!")

    suspend_guest_window.destroy()

    update_current_guests_tab(bed_frame)
    update_suspensions_tab(suspensions_frame)


def remove_suspension():
    selected_index = suspensions_frame.curselection()

    if selected_index:
        selected_suspension = fetch_suspensions_data()[selected_index[0]]
        remove_suspension_dialog(selected_suspension)
    else:
        messagebox.showinfo("Remove Suspension", "Please select a suspension before removing.")


def remove_suspension_dialog(selected_suspension):
    remove_suspension_window = tk.Tk()
    remove_suspension_window.title("Remove Suspension")
    remove_suspension_window.geometry("300x75")

    confirmation_label = tk.Label(remove_suspension_window, text="Are you sure you want to remove this suspension?")
    confirmation_label.pack()

    remove_button = tk.Button(remove_suspension_window, text="Remove", command=lambda: remove_suspension_action(remove_suspension_window, selected_suspension))
    remove_button.pack()

    remove_suspension_window.mainloop()


def remove_suspension_action(remove_suspension_window, selected_suspension):
    cur.execute("DELETE FROM suspensions WHERE id = ?", (selected_suspension[0],))
    conn.commit()

    remove_suspension_window.destroy()
    messagebox.showinfo("Remove Suspension", "Suspension removed successfully!")

    update_suspensions_tab(suspensions_frame)


def calculate_return_date(duration):
    if duration == "3 months":
        return_date = datetime.now() + timedelta(days=3 * 30)
    elif duration == "6 months":
        return_date = datetime.now() + timedelta(days=6 * 30)
    else:
        return_date = datetime.now() + timedelta(days=365 * 100)

    return return_date.strftime('%Y-%m-%d')


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

        cur.execute("INSERT INTO guests (first_name, last_name, birth_date) VALUES (?, ?, ?)",
                    (first_name, last_name, dob))
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
        port = 465
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