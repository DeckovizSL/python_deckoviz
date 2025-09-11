from pydantic import BaseModel, Field 

# Models
class PairingRequest(BaseModel):
    qr_token: str

class PairingResponse(BaseModel):
    success: bool
    message: str
    
class GenerateQRRequest(BaseModel):
    user_id: str = Field(..., description="User ID to pair with TV")
    instructions: str = Field("Scan to connect your mobile app", description="Instructions text on the QR code")
    
class GenerateQRResponse(BaseModel):
    qr_token: str
    qr_code_base64: str
    expiration_time: int