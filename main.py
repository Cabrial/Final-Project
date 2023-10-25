import smtplib
import ssl
import tkinter as tk
from email.message import EmailMessage
from tkinter import ttk, messagebox

# Sample user data (username and password)
user_data = {
    "Pedro": "phc",
    "Vinicius": "vini",
}

bed_data = {f"Bed {i}": {"Guest Name": "", "Checkbox": None} for i in range(1, 25)}

def login():
    username = username_entry.get()
    password = password_entry.get()

    if username in user_data and user_data[username] == password:
        messagebox.showinfo("Login Successful", "Welcome, " + username + "!")
        # Close the login window
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
    main_screen.geometry("800x400")  # Adjust the size as needed

    notebook = ttk.Notebook(main_screen)
    current_guests_tab = ttk.Frame(notebook)
    guests_tab = ttk.Frame(notebook)

    notebook.add(current_guests_tab, text="Current Guests")
    notebook.add(guests_tab, text="Guests")

    # Place the notebook in the main window
    notebook.pack(expand=1, fill="both")

    # Add content to the "Current Guests" tab
    current_guests_label = tk.Label(current_guests_tab, text="Current Guests")
    current_guests_label.pack()

    # Create a frame for the beds grid
    bed_frame = tk.Frame(current_guests_tab)
    bed_frame.pack()

    # Call the function to create the beds grid
    create_beds_grid(bed_frame)

    main_screen.mainloop()


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
        sender_email = "pedrocabrialca@gmail.com"  # Enter your address
        receiver_email = "pedrocabrial@gmail.com"  # Enter receiver address
        password = "okia bqft zuel tloe"

        msg = EmailMessage()
        msg.set_content(f"Full Name: {full_name_entry.get()}\nDate of Birth: {dob_entry.get()}")
        msg['Subject'] = "New User Request!"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        context = ssl.create_default_context()

        # Send the email using your SMTP server
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


# Create a new window for login
window = tk.Tk()
window.title("Login Interface")

# Set the window size to 300x200 pixels (adjust as needed)
window.geometry("300x200")

# Create and place labels, entry fields, and buttons
username_label = tk.Label(window, text="Username:")
username_label.pack()
username_entry = tk.Entry(window)
username_entry.pack()

password_label = tk.Label(window, text="Password:")
password_label.pack()
password_entry = tk.Entry(window, show="*")  # Passwords should be hidden
password_entry.pack()

login_button = tk.Button(window, text="Login", command=login)
login_button.pack()

# Add a "Request Account" button
request_button = tk.Button(window, text="Request Account", command=request_user_creation)
request_button.pack()

# Start the GUI event loop for the login window
window.mainloop()