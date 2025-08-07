"""
Free Speech-to-Text Service using Open Source Alternatives
Provides real speech-to-text without API costs using local models
"""

import logging
import os
import tempfile
import json
import subprocess
import sys
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class FreeSpeechService:
    def __init__(self):
        self.ready = False
        self.available_engines = {}
        self.active_engine = None
        self.initialize()
    
    def initialize(self):
        """Initialize free speech recognition services"""
        try:
            logger.info("Initializing free speech recognition services...")
            
            # Check available free engines
            self.check_speech_recognition()
            self.check_vosk()
            self.check_wav2vec2()
            
            # Set the best available engine
            self.select_best_engine()
            
        except Exception as e:
            logger.error(f"Error initializing free speech service: {e}")
            self.ready = False
    
    def check_speech_recognition(self):
        """Check if SpeechRecognition library is available (uses Google's free API)"""
        try:
            import speech_recognition as sr
            
            # Test basic functionality
            recognizer = sr.Recognizer()
            
            self.available_engines['speech_recognition'] = {
                'name': 'SpeechRecognition + Google Web API',
                'type': 'online_free',
                'accuracy': 'high',
                'languages': 'many',
                'cost': 'free (with limits)',
                'ready': True,
                'recognizer': recognizer
            }
            logger.info("SpeechRecognition library available")
            
        except ImportError:
            logger.info("SpeechRecognition not installed")
            self.available_engines['speech_recognition'] = {
                'name': 'SpeechRecognition + Google Web API',
                'type': 'online_free',
                'ready': False,
                'install_command': 'pip install SpeechRecognition'
            }
        except Exception as e:
            logger.warning(f"SpeechRecognition check failed: {e}")
    
    def check_vosk(self):
        """Check if Vosk offline speech recognition is available"""
        try:
            import vosk
            
            # Check if we have a model
            model_path = self.get_vosk_model_path()
            if model_path and os.path.exists(model_path):
                model = vosk.Model(model_path)
                
                self.available_engines['vosk'] = {
                    'name': 'Vosk Offline Speech Recognition',
                    'type': 'offline_free',
                    'accuracy': 'good',
                    'languages': 'english',
                    'cost': 'completely free',
                    'ready': True,
                    'model': model
                }
                logger.info("Vosk offline speech recognition available")
            else:
                self.available_engines['vosk'] = {
                    'name': 'Vosk Offline Speech Recognition',
                    'type': 'offline_free',
                    'ready': False,
                    'install_commands': [
                        'pip install vosk',
                        'Download model from https://alphacephei.com/vosk/models'
                    ]
                }
                
        except ImportError:
            logger.info("Vosk not installed")
            self.available_engines['vosk'] = {
                'name': 'Vosk Offline Speech Recognition',
                'type': 'offline_free',
                'ready': False,
                'install_command': 'pip install vosk'
            }
        except Exception as e:
            logger.warning(f"Vosk check failed: {e}")
    
    def check_wav2vec2(self):
        """Check if Wav2Vec2 (Facebook's model) is available via transformers"""
        # DISABLED: Skip transformers to avoid cache warnings and unnecessary imports
        logger.info("Wav2Vec2 check skipped to avoid dependencies")
        self.available_engines['wav2vec2'] = {
            'name': 'Wav2Vec2 (Facebook AI)',
            'type': 'offline_free',
            'ready': False,
            'disabled_reason': 'Skipped to keep app lightweight',
            'install_commands': [
                'pip install transformers torch',
                'Model will auto-download on first use'
            ]
        }
    
    def select_best_engine(self):
        """Select the best available engine"""
        # Priority order: SpeechRecognition (easiest) > Vosk (offline)
        
        if self.available_engines.get('speech_recognition', {}).get('ready'):
            self.active_engine = 'speech_recognition'
            self.ready = True
            logger.info("Using SpeechRecognition with Google Web API")
            
        elif self.available_engines.get('vosk', {}).get('ready'):
            self.active_engine = 'vosk'
            self.ready = True
            logger.info("Using Vosk offline speech recognition")
            
        else:
            self.ready = False
            logger.info("No offline speech recognition engines available - using web-based alternatives")
    
    def transcribe_audio_file(self, audio_file_path: str, language: str = 'en') -> Dict[str, Any]:
        """Transcribe audio file using the best available free engine"""
        if not self.ready:
            return self._no_engine_result()
        
        try:
            if self.active_engine == 'speech_recognition':
                return self._transcribe_with_speech_recognition(audio_file_path, language)
            elif self.active_engine == 'vosk':
                return self._transcribe_with_vosk(audio_file_path)
            else:
                return self._no_engine_result()
                
        except Exception as e:
            logger.error(f"Error transcribing with {self.active_engine}: {e}")
            return {
                'success': False,
                'text': '',
                'transcription': '',
                'confidence': 0.0,
                'error': 'TRANSCRIPTION_ERROR',
                'message': f'Failed to transcribe: {str(e)}',
                'engine': self.active_engine
            }
    
    def _transcribe_with_speech_recognition(self, audio_file_path: str, language: str = 'en') -> Dict[str, Any]:
        """Transcribe using SpeechRecognition library with Google Web API"""
        import speech_recognition as sr
        
        recognizer = self.available_engines['speech_recognition']['recognizer']
        
        # Convert webm to wav if needed
        wav_path = self._convert_to_wav(audio_file_path)
        
        try:
            with sr.AudioFile(wav_path) as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Record the audio
                audio = recognizer.record(source)
            
            # Recognize speech using Google Web Speech API (free tier)
            text = recognizer.recognize_google(audio, language=language)
            
            if not text.strip():
                return {
                    'success': False,
                    'text': '',
                    'transcription': '',
                    'confidence': 0.0,
                    'error': 'SILENCE_DETECTED',
                    'message': 'No speech detected in audio',
                    'engine': 'speech_recognition'
                }
            
            return {
                'success': True,
                'text': text.strip(),
                'transcription': text.strip(),
                'confidence': 0.8,  # SpeechRecognition doesn't provide confidence
                'engine': 'speech_recognition',
                'cost': 'free',
                'message': 'Transcribed using Google Web Speech API (free)'
            }
            
        except sr.UnknownValueError:
            return {
                'success': False,
                'text': '',
                'transcription': '',
                'confidence': 0.0,
                'error': 'SILENCE_DETECTED',
                'message': 'Could not understand audio',
                'engine': 'speech_recognition'
            }
        except sr.RequestError as e:
            return {
                'success': False,
                'text': '',
                'transcription': '',
                'confidence': 0.0,
                'error': 'SERVICE_ERROR',
                'message': f'Google API error: {e}',
                'engine': 'speech_recognition'
            }
        finally:
            # Clean up converted file
            if wav_path != audio_file_path:
                try:
                    os.unlink(wav_path)
                except:
                    pass
    
    def _transcribe_with_vosk(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe using Vosk offline speech recognition"""
        import vosk
        import wave
        import json
        
        model = self.available_engines['vosk']['model']
        
        # Convert to wav format that Vosk expects
        wav_path = self._convert_to_wav(audio_file_path, sample_rate=16000)
        
        try:
            wf = wave.open(wav_path, 'rb')
            
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                return {
                    'success': False,
                    'text': '',
                    'error': 'AUDIO_FORMAT_ERROR',
                    'message': 'Audio must be mono WAV, 16kHz, 16-bit',
                    'engine': 'vosk'
                }
            
            rec = vosk.KaldiRecognizer(model, wf.getframerate())
            
            transcription_parts = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if result.get('text'):
                        transcription_parts.append(result['text'])
            
            # Get final result
            final_result = json.loads(rec.FinalResult())
            if final_result.get('text'):
                transcription_parts.append(final_result['text'])
            
            full_text = ' '.join(transcription_parts).strip()
            
            if not full_text:
                return {
                    'success': False,
                    'text': '',
                    'transcription': '',
                    'confidence': 0.0,
                    'error': 'SILENCE_DETECTED',
                    'message': 'No speech detected in audio',
                    'engine': 'vosk'
                }
            
            return {
                'success': True,
                'text': full_text,
                'transcription': full_text,
                'confidence': 0.85,
                'engine': 'vosk',
                'cost': 'completely free (offline)',
                'message': 'Transcribed using Vosk offline model'
            }
            
        finally:
            wf.close()
            if wav_path != audio_file_path:
                try:
                    os.unlink(wav_path)
                except:
                    pass
    
    def _convert_to_wav(self, audio_file_path: str, sample_rate: int = 16000) -> str:
        """Convert audio file to WAV format using ffmpeg if available"""
        # If already wav, check if conversion needed
        if audio_file_path.lower().endswith('.wav'):
            return audio_file_path
        
        # Try to convert using ffmpeg
        try:
            output_path = audio_file_path.rsplit('.', 1)[0] + '_converted.wav'
            
            # Use ffmpeg if available
            result = subprocess.run([
                'ffmpeg', '-i', audio_file_path, 
                '-ar', str(sample_rate), 
                '-ac', '1',  # mono
                '-y',  # overwrite
                output_path
            ], capture_output=True, check=True)
            
            return output_path
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # ffmpeg not available, return original file
            logger.warning("ffmpeg not available for audio conversion")
            return audio_file_path
    
    def get_vosk_model_path(self) -> Optional[str]:
        """Get path to Vosk model if available"""
        possible_paths = [
            'vosk-model-en-us-0.22',
            'vosk-model-small-en-us-0.15',
            './models/vosk-model-en-us-0.22',
            './models/vosk-model-small-en-us-0.15'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def transcribe_from_flask_file(self, flask_file, language: str = 'en') -> Dict[str, Any]:
        """Transcribe audio from Flask file upload"""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
                flask_file.seek(0)
                temp_file.write(flask_file.read())
                temp_file.flush()
                
                # Transcribe the file
                result = self.transcribe_audio_file(temp_file.name, language)
                
                # Clean up
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
                
                return result
                
        except Exception as e:
            logger.error(f"Error transcribing Flask file: {e}")
            return {
                'success': False,
                'text': '',
                'transcription': '',
                'confidence': 0.0,
                'error': 'FLASK_FILE_ERROR',
                'message': f'Failed to process uploaded file: {str(e)}'
            }
    
    def _no_engine_result(self) -> Dict[str, Any]:
        """Return result when no engine is available"""
        return {
            'success': False,
            'text': '',
            'transcription': '',
            'confidence': 0.0,
            'error': 'NO_ENGINE',
            'message': 'No free speech recognition engines available',
            'available_engines': self.available_engines,
            'setup_instructions': self.get_setup_instructions()
        }
    
    def get_setup_instructions(self) -> Dict[str, Any]:
        """Get setup instructions for free speech recognition"""
        return {
            'quick_setup': {
                'name': 'SpeechRecognition (Easiest)',
                'steps': [
                    'pip install SpeechRecognition',
                    'pip install pyaudio  # for microphone support',
                    'Uses Google Web Speech API (free with limits)'
                ],
                'pros': ['Easy to install', 'Good accuracy', 'Multiple languages'],
                'cons': ['Requires internet', 'Has usage limits']
            },
            'offline_setup': {
                'name': 'Vosk (Completely Offline)',
                'steps': [
                    'pip install vosk',
                    'Download model: wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip',
                    'Extract model to project directory'
                ],
                'pros': ['Completely free', 'No internet needed', 'No limits'],
                'cons': ['Requires model download (~40MB)', 'English only']
            },
            'advanced_setup': {
                'name': 'Wav2Vec2 (Best Quality)',
                'steps': [
                    'pip install transformers torch',
                    'Model downloads automatically on first use'
                ],
                'pros': ['Highest accuracy', 'State-of-the-art', 'Free'],
                'cons': ['Larger download', 'Requires more CPU']
            }
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            'service': 'Free Speech Recognition',
            'ready': self.ready,
            'active_engine': self.active_engine,
            'available_engines': self.available_engines,
            'cost': 'completely free',
            'setup_required': not self.ready
        }
    
    def is_ready(self) -> bool:
        """Check if service is ready"""
        return self.ready

# Singleton instance
_free_speech_service = None

def get_free_speech_service() -> FreeSpeechService:
    """Get singleton instance of FreeSpeechService"""
    global _free_speech_service
    if _free_speech_service is None:
        _free_speech_service = FreeSpeechService()
    return _free_speech_service
