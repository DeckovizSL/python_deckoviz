import qrcode
import json
import uuid
import time
from PIL import Image, ImageDraw, ImageFont
import io
import base64

class TVQRCodeGenerator:
    def __init__(self, websocket_endpoint="wss://your-server.com/ws"):
        """
        Initialize the QR code generator with the WebSocket endpoint.
        
        Args:
            websocket_endpoint (str): The WebSocket server endpoint
        """
        self.websocket_endpoint = websocket_endpoint
        

    def generate_qr_token(self):
        """Generate a unique QR token (UUID) for pairing."""
        return str(uuid.uuid4())
        

    def encode_qr_token_data(self, qr_token):
        """
        Create data to be encoded in the QR code for TV pairing (only qr_token).
        """
        return {
            "qr_token": qr_token,
            "timestamp": int(time.time()),
            "ver": "1.0"
        }
    
    def create_pairing_data(self, expiration_minutes=5):
        """
        Create pairing data to be encoded in the QR code.
        
        Args:
            expiration_minutes (int): Minutes until the QR code expires
            
        Returns:
            dict: Pairing data including device ID, endpoint, and expiration
        """
        device_id = self.generate_device_id()
        expiration = int(time.time()) + (expiration_minutes * 60)
        
        return {
            "device_id": device_id,
            "endpoint": self.websocket_endpoint,
            "exp": expiration,
            "ver": "1.0"
        }
    
    def generate_qr_code(self, data, size=300, logo=None):
        """
        Generate a QR code with the given data.
        
        Args:
            data (dict): Data to encode in the QR code
            size (int): Size of the QR code in pixels
            logo (str, optional): Path to a logo to place in the center of the QR code
            
        Returns:
            Image: PIL Image object containing the QR code
        """
        # Convert data to JSON string
        json_data = json.dumps(data)
        
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        
        # Add data to the QR code
        qr.add_data(json_data)
        qr.make(fit=True)
        
        # Create an image from the QR Code instance
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
        
        # Resize to the specified size
        qr_img = qr_img.resize((size, size))
        
        # Add logo if provided
        if logo:
            try:
                logo_img = Image.open(logo).convert('RGBA')
                logo_size = size // 4
                logo_img = logo_img.resize((logo_size, logo_size))
                
                # Calculate position to place the logo
                position = ((size - logo_size) // 2, (size - logo_size) // 2)
                
                # Create a white background behind the logo
                white_box = Image.new('RGBA', (logo_size + 10, logo_size + 10), (255, 255, 255, 255))
                qr_img.paste(white_box, (position[0] - 5, position[1] - 5), white_box)
                
                # Place the logo
                qr_img.paste(logo_img, position, logo_img)
            except Exception as e:
                print(f"Error adding logo: {e}")
        
        return qr_img
    
    def add_instructions(self, qr_img, text="Scan with Mobile App"):
        """
        Add instructions text below the QR code.
        
        Args:
            qr_img (Image): QR code image
            text (str): Instructions text
            
        Returns:
            Image: Combined image with QR code and instructions
        """
        # Create a new image with extra space for text
        width, height = qr_img.size
        new_img = Image.new('RGBA', (width, height + 60), (255, 255, 255, 255))
        
        # Paste the QR code
        new_img.paste(qr_img, (0, 0))
        
        # Add text
        draw = ImageDraw.Draw(new_img)
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except IOError:
            font = ImageFont.load_default()
            
        text_width = draw.textlength(text, font=font)
        position = ((width - text_width) // 2, height + 15)
        draw.text(position, text, fill=(0, 0, 0), font=font)
        
        return new_img
    
    def save_qr_code(self, img, filename="tv_pairing_qr.png"):
        """
        Save the QR code image to a file.
        
        Args:
            img (Image): QR code image
            filename (str): Output filename
            
        Returns:
            str: Path to the saved file
        """
        img.save(filename)
        return filename
        
    def get_qr_as_base64(self, img):
        """
        Convert QR code image to base64 string (useful for displaying in web/TV apps).
        
        Args:
            img (Image): QR code image
            
        Returns:
            str: Base64 encoded image string
        """
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def generate(self, include_instructions=True, logo_path=None, save_file=True):
        """
        Generate a complete QR code with pairing data.
        
        Args:
            include_instructions (bool): Whether to add instructions text
            logo_path (str, optional): Path to logo image
            save_file (bool): Whether to save the QR code to a file
            
        Returns:
            tuple: (Image object, base64 string, pairing data)
        """
        # Create pairing data
        pairing_data = self.create_pairing_data()
        
        # Generate QR code
        qr_img = self.generate_qr_code(pairing_data, logo=logo_path)
        
        # Add instructions if needed
        if include_instructions:
            qr_img = self.add_instructions(qr_img)
        
        # Save to file if needed
        if save_file:
            self.save_qr_code(qr_img)
        
        # Get base64 representation
        base64_qr = self.get_qr_as_base64(qr_img)
        
        return qr_img, base64_qr, pairing_data
        
    def generate_qr_pairing(self, include_instructions=True, logo_path=None, save_file=False, instruction_text="Scan to connect your mobile app"):
        """
        Generate a QR code for TV pairing (encodes only qr_token).
        Returns: (Image, base64, pairing_data, qr_token)
        """
        qr_token = self.generate_qr_token()
        pairing_data = self.encode_qr_token_data(qr_token)
        qr_img = self.generate_qr_code(pairing_data, logo=logo_path)
        if include_instructions:
            qr_img = self.add_instructions(qr_img, text=instruction_text)
        if save_file:
            filename = f"tv_qr_pairing_{qr_token[:8]}.png"
            self.save_qr_code(qr_img, filename=filename)
        base64_qr = self.get_qr_as_base64(qr_img)
        return qr_img, base64_qr, pairing_data, qr_token

