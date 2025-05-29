import assemblyai as aai
from dotenv import load_dotenv
import os 

load_dotenv()

class AudioProcessor:
    """
    A class to handle audio transcription using AssemblyAI.
    """
    def __init__(self, api_key: str = None):
        """
        Initialize the AudioProcessor.
        
        Args:
            api_key: API key for AssemblyAI
        """
        self.api_key = api_key or os.getenv("ASSEMBLYAI_API_KEY")
        if not self.api_key:
            raise ValueError("ASSEMBLYAI_API_KEY not found in environment variables")
        aai.settings.api_key = self.api_key
        self.config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.slam_1)
        self.transcriber = aai.Transcriber()

    def _transcribe(self, file_path) -> str:
        """
        Transcribe an audio file and return the transcript.
        
        Args:
            file_path: Path to the audio file
        
        Returns:
            str: Transcribed text
        """
        print(f"Transcribing audio from file: {file_path}")
        try:
            transcript = self.transcriber.transcribe(file_path, self.config) 
            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"Transcription failed: {transcript.error}")
            return transcript.text
        except Exception as e:
            raise Exception(f"Error transcribing audio: {str(e)}")

    def get_transcript(self, audio_file_path):
        """
        Transcribe an audio file and return the transcript.
        
        Args:
            audio_file_path: Path to the audio file
        
        Returns:
            str: Transcribed text
        """
        return self._transcribe(audio_file_path)