import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ftplib import FTP


# Function to send an email
def send_email(destination_email, subject, email_text, file_link):
    sender_email = "somelogin@gmail.com"
    sender_password = "somepassword"

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = destination_email
    message['Subject'] = subject
    message.attach(MIMEText(email_text + "\n\nFile link: " + file_link, 'plain'))

    session = smtplib.SMTP('smtp.gmail.com', 587)  # Use Gmail's SMTP server
    session.starttls()  # Enable security
    session.login(sender_email, sender_password)  # Login with email and password
    session.sendmail(sender_email, destination_email, message.as_string())
    session.quit()


# Function to upload a file via FTP
def upload_file_ftp(file_path):
    ftp_server = "138.68.98.108"  # FTP server IP
    username = "yourusername"  # FTP username
    password = "yourpassword"  # FTP password
    remote_path = "/home/somedirectory/faf-212/cara/"  # FTP remote path

    remote_file_path = remote_path + file_path.split('/')[-1]

    ftp = FTP(ftp_server)
    ftp.login(username, password)
    with open(file_path, 'rb') as file:
        ftp.storbinary(f'STOR {remote_file_path}', file)
    ftp.quit()

    web_accessible_path = "/faf-212/cara/" + file_path.split('/')[-1]
    return "http://138.68.98.108" + web_accessible_path


# GUI functions
def browse_file():
    filename = filedialog.askopenfilename()
    file_path_entry.delete(0, tk.END)
    file_path_entry.insert(0, filename)


def submit():
    destination_email = destination_email_entry.get()
    subject = subject_entry.get()
    email_text = email_text_entry.get("1.0", tk.END)
    file_path = file_path_entry.get()

    # Upload the file and send the email
    try:
        file_link = upload_file_ftp(file_path)
        send_email(destination_email, subject, email_text, file_link)
        messagebox.showinfo("Success", "Email has been sent successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))


# Tkinter GUI setup
root = tk.Tk()
root.title("Email Sender UI")

tk.Label(root, text="Enter destination email:").pack()
destination_email_entry = tk.Entry(root, width=50)
destination_email_entry.pack()

tk.Label(root, text="Enter email subject:").pack()
subject_entry = tk.Entry(root, width=50)
subject_entry.pack()

tk.Label(root, text="Enter email text:").pack()
email_text_entry = tk.Text(root, height=10, width=50)
email_text_entry.pack()

tk.Label(root, text="Enter path to the file to upload:").pack()
file_path_entry = tk.Entry(root, width=50)
file_path_entry.pack()

browse_button = tk.Button(root, text="Browse", command=browse_file)
browse_button.pack()

submit_button = tk.Button(root, text="Send Email", command=submit)
submit_button.pack()

root.mainloop()
