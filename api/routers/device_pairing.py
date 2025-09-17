from fastapi import APIRouter, Depends, HTTPException
from datetime import timedelta
import uuid, secrets, bcrypt
from api.utils.device_tokens import create_jwt, decode_jwt, get_current_user
from common.apps.authentication.models import User, DeviceLink
from django.utils import timezone
from api.utils.create_qr import generate_qr_base64
router = APIRouter(prefix="/device", tags=["Device Pairing"])
 
TV_ACCESS_EXPIRE_MINUTES = 24 * 60  # 24 hours
MOBILE_ACCESS_EXPIRE_MINUTES = 15   # 15 minutes (default)
REFRESH_EXPIRE_DAYS = 365

@router.post("/session/new")
def create_session():
    session_id = str(uuid.uuid4())
    qr_code=generate_qr_base64(session_id)
    return {"session_id": session_id, "qr_url": f"https://app.com/qr/{session_id}", "qr_code":qr_code}

@router.post("/pair-tv")
def pair_tv(session_id: str, current_user: User = Depends(get_current_user)):
    refresh_token = secrets.token_urlsafe(64)
    refresh_hash = bcrypt.hashpw(refresh_token.encode(), bcrypt.gensalt()).decode()
    expiry = timezone.now() + timezone.timedelta(days=REFRESH_EXPIRE_DAYS)

    # Ensure current_user is a User instance
    if isinstance(current_user, str):
        user_obj = User.objects.get(id=current_user)
    else:
        user_obj = current_user

    DeviceLink.objects.create(
        user=user_obj,
        refresh_token_hash=refresh_hash,
        expires_at=expiry
    )

    access_token = create_jwt({"user_id": str(user_obj.id), "role": "tv"}, exp_minutes=TV_ACCESS_EXPIRE_MINUTES)

    return {"access_token": access_token, "refresh_token": refresh_token}

@router.post("/refresh")
def refresh_token(refresh_token: str):
    devices = DeviceLink.objects.all()
    for device in devices:
        if bcrypt.checkpw(refresh_token.encode(), device.refresh_token_hash.encode()):
            if device.is_expired():
                raise HTTPException(401, "Refresh token expired")
            # Use 24h expiry for TV, 15m for mobile (default)
            role = getattr(device, 'device_type', 'tv')
            if role == 'tv':
                exp_minutes = TV_ACCESS_EXPIRE_MINUTES
            else:
                exp_minutes = MOBILE_ACCESS_EXPIRE_MINUTES
            new_access = create_jwt({"user_id": str(device.user.id), "role": role}, exp_minutes=exp_minutes)
            return {"access_token": new_access}
    raise HTTPException(401, "Invalid refresh token")

@router.post("/logout-tv")
def logout_tv(refresh_token: str):
    devices = DeviceLink.objects.all()
    for device in devices:
        if bcrypt.checkpw(refresh_token.encode(), device.refresh_token_hash.encode()):
            device.delete()
            return {"detail": "Device unlinked successfully"}
    raise HTTPException(401, "Invalid refresh token")
