from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import os

class VoiceCallHandler:
    def __init__(self, twilio_sid: str, twilio_token: str, twilio_phone: str):
        self.client = Client(twilio_sid, twilio_token)
        self.twilio_phone = twilio_phone
        self.recognizer = sr.Recognizer()
    
    async def initiate_call(self, user_phone: str, session_id: str):
        """Initiate outbound call"""
        try:
            call = self.client.calls.create(
                to=user_phone,
                from_=self.twilio_phone,
                url=f"https://deckoviz.com/voice/handle/{session_id}",
                method="POST"
            )
            return call.sid
        except Exception as e:
            print(f"Error initiating call: {e}")
            return None
    
    def generate_twiml_response(self, message: str, gather_input: bool = True):
        """Generate TwiML response for voice interaction"""
        response = VoiceResponse()
        response.say(message, voice='alice')
        
        if gather_input:
            gather = response.gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action='/voice/process_speech',
                method='POST'
            )
            gather.say("Please speak after the tone.")
        
        return str(response)
    
    async def process_speech_to_text(self, audio_url: str) -> str:
        """Convert speech to text using speech recognition"""
        try:
            # Download audio from Twilio
            # This is simplified - you'd want proper audio handling
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                # Download and convert audio
                # Implementation depends on your audio processing needs
                
                with sr.AudioFile(temp_file.name) as source:
                    audio = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(audio)
                    return text
        except Exception as e:
            print(f"Speech recognition error: {e}")
            return ""
        finally:
            if 'temp_file' in locals():
                os.unlink(temp_file.name)