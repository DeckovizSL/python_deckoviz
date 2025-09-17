import qrcode
import base64
from io import BytesIO


def generate_qr_base64(session_id: str) -> str:
    """
    Generate a base64-encoded QR code containing the given session ID.

    Args:
        session_id (str): The session ID to encode inside the QR code.

    Returns:
        str: A base64 string representation of the QR code image (PNG).
    """
    # Create QR code
    qr = qrcode.QRCode(
        version=1,  # auto adjust size if needed
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(session_id)
    qr.make(fit=True)

    # Render QR as an image
    img = qr.make_image(fill_color="black", back_color="white")

    # Save to in-memory buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Encode as base64
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{qr_base64}"