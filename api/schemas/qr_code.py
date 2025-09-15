from pydantic import BaseModel, Field 

# Models
class PairingRequest(BaseModel):
    device_id: str
    room_id: str

class PairingResponse(BaseModel):
    success: bool
    message: str
    
class GenerateQRRequest(BaseModel):
    api_base_url: str = Field(..., description="Base URL of the API")
    instructions: str = Field("Scan to connect your mobile app", description="Instructions text on the QR code")
    
class GenerateQRResponse(BaseModel):
    device_id: str
    qr_code_base64: str
    expiration_time: int