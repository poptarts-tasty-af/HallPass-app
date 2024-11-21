import qrcode
import time
import os

def generate_qr_code(teacher, classroom):
    # Get the current timestamp (the time when the QR code is created)
    timestamp = int(time.time())
    
    # URL to encode in the QR code (we'll dynamically create the URL)
    url = f"https://example.com/scan?teacher={teacher}&classroom={classroom}&timestamp={timestamp}"
    
    # Create the QR code
    qr = qrcode.QRCode(
        version=1,  # Size of the QR code (1 is the smallest, 40 is the largest)
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Error correction level
        box_size=10,  # Size of each box in the QR code
        border=4,  # Thickness of the border
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Create an image from the QR code
    img = qr.make_image(fill='black', back_color='white')

    # Ensure the directory exists for saving the images
    os.makedirs('qr_codes', exist_ok=True)

    # Save the QR code image with a filename based on teacher and classroom
    filename = f"qr_codes/{teacher}_{classroom}_{timestamp}.png"
    img.save(filename)
    print(f"QR code saved as {filename}")

# You can change this to generate more QR codes as needed.
teacher = "Mr_Sierra"
classroom = "2080"
generate_qr_code(teacher, classroom)