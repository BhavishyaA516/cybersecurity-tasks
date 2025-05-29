from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw
import re
from cryptography.fernet import Fernet
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import string
import random
import io
from PIL import Image
import tempfile
import os


# Global variables for original image
original_image = None
original_image_path = None

# Function to validate key
def validate_key(key):
    # Ensure key length is 16 characters
    if len(key) != 16:
        return False
    
    # Check if the key contains at least one special symbol, one number, one uppercase, and one lowercase
    if not any(char in string.punctuation for char in key):
        return False
    if not any(char.isdigit() for char in key):
        return False
    if not any(char.isupper() for char in key):
        return False
    if not any(char.islower() for char in key):
        return False
    
    return True

# Function to generate a random and strong key
def generate_key():
    # Define character sets for special symbols, numbers, uppercase, and lowercase letters
    special_symbols = string.punctuation  # Special symbols
    numbers = string.digits  # Numbers
    uppercase_letters = string.ascii_uppercase  # Uppercase letters
    lowercase_letters = string.ascii_lowercase  # Lowercase letters
    
    # Ensure at least one character from each character set
    key = random.choice(special_symbols) + \
          random.choice(numbers) + \
          random.choice(uppercase_letters) + \
          random.choice(lowercase_letters)
    
    # Generate remaining characters randomly
    remaining_characters = special_symbols + numbers + uppercase_letters + lowercase_letters
    key += ''.join(random.choice(remaining_characters) for _ in range(16 - len(key)))
    
    # Shuffle the key to randomize the order of characters
    key_list = list(key)
    random.shuffle(key_list)
    key = ''.join(key_list)
    
    return key

# Function to encrypt image
def encrypt_image(filepath, key):
    if filepath and key:
        if validate_key(key):
            try:
                img = Image.open(filepath)

                # Add some visual indication that the image is encrypted
                draw = ImageDraw.Draw(img)
                draw.rectangle([(0, 0), img.size], fill=(255, 105, 97))  # White background
                draw.text((20, 20), "Image encrypted", fill=(0, 0, 0))  # Text indicating encrypted

                # Example of simple encryption (XOR with key)
                key_bytes = bytes(key, 'utf-8')
                data = img.tobytes()
                encrypted_data = bytes([data[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(data))])

                # Create a temporary file to save the encrypted image
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_filepath = temp_file.name
                    temp_file.write(encrypted_data)

                # Replace the original image with the encrypted image
                img.close()  # Close the original image
                os.replace(temp_filepath, filepath)  # Replace original file with encrypted image
                messagebox.showinfo("Success", "Image encrypted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to encrypt image: {str(e)}")
        else:
            messagebox.showerror("Error", "Generated key does not meet the criteria.")
    else:
        messagebox.showerror("Error", "Please select an image file and enter a key.")

# Function to open a new window for sending decryption key via email
def open_send_key_window(key):
    def send_key():
        recipient_email = recipient_email_entry.get()
        sender_email = sender_email_entry.get()
        send_mail(recipient_email, sender_email, key)

    send_key_window = Toplevel(root)
    send_key_window.title("Send Decryption Key")
    send_key_window.geometry("400x200")
    send_key_window.configure(bg="#77DD77")  # Pastel green background

    recipient_email_label = Label(send_key_window, text="Recipient Email:", bg="#FFA07A")
    recipient_email_label.pack(pady=5)

    recipient_email_entry = Entry(send_key_window)
    recipient_email_entry.pack(pady=5)

    sender_email_label = Label(send_key_window, text="Your Email:", bg="#FFA07A")
    sender_email_label.pack(pady=5)

    sender_email_entry = Entry(send_key_window)
    sender_email_entry.pack(pady=5)

    send_key_button = Button(send_key_window, text="Send Key", command=send_key, bg="#87CEEB")  # Green button
    send_key_button.pack(pady=5)

# Function to open a new window for decryption
def open_decrypt_window(key):
    def decrypt():
        filepath = filedialog.askopenfilename(title="Select Encrypted Image File")
        if filepath:
            key = key_entry.get()  # Get the decryption key from the entry field
            decrypt_image(filepath, key)

    decrypt_window = Toplevel(root)
    decrypt_window.title("Decrypt Image")
    decrypt_window.geometry("400x200")
    decrypt_window.configure(bg="#87CEEB")  # Pastel blue background

    key_label = Label(decrypt_window, text="Decryption Key:", bg="#87CEEB")
    key_label.pack(pady=5)

    key_entry = Entry(decrypt_window)
    key_entry.insert(0, key)  # Insert the received key into the entry field
    key_entry.pack(pady=5)

    decrypt_button = Button(decrypt_window, text="Decrypt", command=decrypt, bg="#32CD32")  # Green button
    decrypt_button.pack(pady=5)

# Function to open a new window for encryption
def open_encrypt_window():
    def browse_image():
        filepath = filedialog.askopenfilename(title="Select Image File")
        if filepath:
            image_path.set(filepath)
            key_entry.delete(0, END)
            key_entry.insert(0, generate_key())

    def encrypt():
        filepath = image_path.get()
        key = key_entry.get()
        encrypt_image(filepath, key)
        open_send_key_window(key)  # Open the window for sending the decryption key via email

    encrypt_window = Toplevel(root)
    encrypt_window.title("Encrypt Image")
    encrypt_window.geometry("400x200")
    encrypt_window.configure(bg="#FFB6C1")  # Pastel pink background

    image_path = StringVar()
    image_path_entry = Entry(encrypt_window, textvariable=image_path, width=50)
    image_path_entry.pack(pady=10)

    browse_button = Button(encrypt_window, text="Browse", command=browse_image, bg="#87CEEB")  # Pastel blue button
    browse_button.pack(pady=5)

    key_label = Label(encrypt_window, text="Encryption Key:", bg="#FFB6C1")  # Pastel pink background
    key_label.pack(pady=5)

    key_entry = Entry(encrypt_window)
    key_entry.pack(pady=5)

    encrypt_button = Button(encrypt_window, text="Encrypt", command=encrypt, bg="#87CEEB")  # pastel blue button
    encrypt_button.pack(pady=5)



# Function to decrypt image
def decrypt_image(filepath, key):
    if filepath and key:
        if validate_key(key):
            try:
                # Read the encrypted image data
                with open(filepath, "rb") as f:
                    encrypted_data = f.read()

                # Example of simple decryption (XOR with key)
                key_bytes = bytes(key, 'utf-8')
                decrypted_data = bytes([encrypted_data[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(encrypted_data))])

                # Load the decrypted data as a PIL Image
                decrypted_image = Image.open(io.BytesIO(decrypted_data))

                # Save the decrypted image back to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                    temp_filepath = temp_file.name
                    decrypted_image.save(temp_filepath)

                # Replace the original encrypted image with the decrypted image
                os.replace(temp_filepath, filepath)
                messagebox.showinfo("Decryption Successful", "Image decrypted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to decrypt image: {str(e)}")
        else:
            messagebox.showerror("Error", "Provided key does not meet the criteria.")
    else:
        messagebox.showerror("Error", "Please select an image file and enter a key.")
# Function to open a new window for decryption
def open_decrypt_window():
    def browse_image():
        filepath = filedialog.askopenfilename(title="Select Encrypted Image File")
        if filepath:
            image_path_entry.delete(0, END)
            image_path_entry.insert(0, filepath)

    def decrypt():
        key = key_entry.get()
        filepath = image_path_entry.get()
        if filepath:
            decrypt_image(filepath, key)

    decrypt_window = Toplevel(root)
    decrypt_window.title("Decrypt Image")
    decrypt_window.geometry("400x300")
    decrypt_window.configure(bg="#87CEEB")  # Set background color

    image_path_label = Label(decrypt_window, text="Encrypted Image Path:", bg="#87CEEB")
    image_path_label.pack(pady=5)

    image_path_entry = Entry(decrypt_window, width=50)
    image_path_entry.pack(pady=5)

    browse_button = Button(decrypt_window, text="Browse", command=browse_image, bg="#32CD38")  # Green button
    browse_button.pack(pady=5)

    key_label = Label(decrypt_window, text="Decryption Key:", bg="#87CEEB")
    key_label.pack(pady=5)

    key_entry = Entry(decrypt_window)
    key_entry.pack(pady=5)

    decrypt_button = Button(decrypt_window, text="Decrypt", command=decrypt, bg="#32CD38")  # Green button
    decrypt_button.pack(pady=5)

def send_mail(recipient_email, sender_email, key):
    # SMTP server settings
    smtp_server = "smtp.gmail.com"  # Update with your SMTP server
    smtp_port = 587  # Update with your SMTP port
    smtp_username = "malumhyterakissa@gmail.com"  # Update with your SMTP username
    smtp_password = "qewehcwsnqhcpure"  # Update with your SMTP password

    # Email content
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "Key for Image Decryption"
    body = f"The key for decrypting the image is: {key}"
    msg.attach(MIMEText(body, 'plain'))

    # Connect to SMTP server and send email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        messagebox.showinfo("Success", "Email sent successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send email: {str(e)}")

# Main window
root = Tk()
root.title("Image Encryptor and Decryptor")
root.geometry("300x200")  # Wider main window
root.configure(bg="#DA70D6")  # Pastel purple background

title_label = Label(root, text="ImageEncrypt", font=("Arial", 20), bg="#DA70D6")  # Pastel purple background
title_label.pack(pady=20)

encrypt_button = Button(root, text="Encrypt", command=open_encrypt_window, bg="#FFB6C1")  # Pastel pink button
encrypt_button.pack(pady=10)

decrypt_button = Button(root, text="Decrypt", command=open_decrypt_window, bg="#87CEEB")  # Pastel blue button
decrypt_button.pack(pady=10)

root.mainloop()
