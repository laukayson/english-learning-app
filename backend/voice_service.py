"""
Lightweight Voice Service for Language Learning App
Provides mock voice functionality without heavy audio dependencies
"""

import logging
import json
from typing import Dict, Any, Optional, Union
import difflib
import random

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.ready = False
        self.use_lightweight_only = True  # Force lightweight mode
        
        # Mock pronunciation scores and feedback
        self.pronunciation_feedback = {
            'excellent': [
                "Excellent pronunciation! Perfect!",
                "Outstanding! Your pronunciation is very clear.",
                "Perfect! You sound like a native speaker!"
            ],
            'good': [
                "Good pronunciation! Well done!",
                "Nice job! Your pronunciation is clear.",
                "Great effort! Keep practicing!"
            ],
            'needs_improvement': [
                "Good try! Practice makes perfect.",
                "Keep working on it! You're improving.",
                "Nice effort! Try to focus on clarity."
            ]
        }
        
        # Common pronunciation issues and tips
        self.pronunciation_tips = {
            'th': "For 'th' sounds, put your tongue between your teeth",
            'r': "For 'r' sounds, curl your tongue slightly back",
            'l': "For 'l' sounds, touch your tongue to the roof of your mouth",
            'v': "For 'v' sounds, touch your bottom lip with your upper teeth",
            'w': "For 'w' sounds, round your lips like saying 'oo'"
        }
        
        self.initialise_lightweight()
    
    def initialise_lightweight(self):
        """Initialise lightweight voice service"""
        try:
            logger.info("Initialising lightweight voice service...")
            self.ready = True
            logger.info("Lightweight voice service initialised successfully")
        except Exception as e:
            logger.error(f"Error initialising lightweight voice: {e}")
            self.ready = True  # Still ready with mock functionality
    
    def is_ready(self) -> bool:
        """Check if voice service is ready"""
        return self.ready
    
    def generate_speech(self, text: str, language: str = 'en'):
        """Generate speech audio (lightweight mode returns None to trigger browser TTS)"""
        try:
            # In lightweight mode, return None to trigger browser fallback
            logger.info(f"TTS requested for: {text[:50]}... (using browser fallback)")
            return None
        except Exception as e:
            logger.error(f"Error in generate_speech: {e}")
            return None
    
    def text_to_speech(self, text: str, language: str = 'en') -> Dict[str, Any]:
        """Mock text-to-speech - returns instructions for user"""
        try:
            if not text.strip():
                return {'error': 'Empty text provided'}
            
            # Mock response with pronunciation guide
            response = {
                'success': True,
                'text': text,
                'language': language,
                'audio_url': None,  # No actual audio in lightweight mode
                'pronunciation_guide': self._generate_pronunciation_guide(text),
                'message': 'Audio not available in lightweight mode. Please read the text aloud.',
                'phonetic': self._generate_phonetic_guide(text)
            }
            
            logger.info(f"TTS mock response for: {text[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            return {'error': str(e)}
    
    def speech_to_text(self, audio_data: bytes) -> Dict[str, Any]:
        """Mock speech-to-text - returns instructions for user"""
        try:
            # Mock response encouraging text input
            response = {
                'success': True,
                'text': '[Speech recognition not available in lightweight mode]',
                'confidence': 0.0,
                'message': 'Please type your response instead of using voice input.',
                'alternative': 'Use the text input box below to practice writing.'
            }
            
            logger.info("STT mock response provided")
            return response
            
        except Exception as e:
            logger.error(f"Error in speech-to-text: {e}")
            return {'error': str(e)}
    
    def check_pronunciation(self, target_text: str, audio_data: bytes = None, user_text: str = None) -> Dict[str, Any]:
        """Mock pronunciation checking based on text similarity"""
        try:
            if user_text:
                # Text-based pronunciation check
                return self._check_text_pronunciation(target_text, user_text)
            else:
                # Mock audio-based check
                return self._mock_audio_pronunciation_check(target_text)
                
        except Exception as e:
            logger.error(f"Error checking pronunciation: {e}")
            return {'error': str(e)}
    
    def _check_text_pronunciation(self, target: str, user_input: str) -> Dict[str, Any]:
        """Check pronunciation based on text similarity"""
        try:
            # Normalize texts
            target_clean = target.lower().strip()
            user_clean = user_input.lower().strip()
            
            # Calculate similarity
            similarity = difflib.SequenceMatcher(None, target_clean, user_clean).ratio()
            score = int(similarity * 100)
            
            # Determine feedback level
            if score >= 90:
                feedback_type = 'excellent'
            elif score >= 70:
                feedback_type = 'good'
            else:
                feedback_type = 'needs_improvement'
            
            # Generate specific feedback
            feedback = random.choice(self.pronunciation_feedback[feedback_type])
            
            # Find common issues
            issues = self._find_pronunciation_issues(target_clean, user_clean)
            tips = [self.pronunciation_tips.get(issue, f"Practice the '{issue}' sound") for issue in issues]
            
            response = {
                'success': True,
                'score': score,
                'feedback': feedback,
                'target_text': target,
                'user_text': user_input,
                'issues': issues,
                'tips': tips[:3],  # Limit to 3 tips
                'phonetic_target': self._generate_phonetic_guide(target),
                'message': 'Based on text comparison. Try speaking aloud for practice!'
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in text pronunciation check: {e}")
            return {'error': str(e)}
    
    def _mock_audio_pronunciation_check(self, target_text: str) -> Dict[str, Any]:
        """Mock audio pronunciation check"""
        # Generate random but realistic score
        base_score = random.randint(70, 95)
        
        response = {
            'success': True,
            'score': base_score,
            'feedback': random.choice(self.pronunciation_feedback['good']),
            'target_text': target_text,
            'phonetic_target': self._generate_phonetic_guide(target_text),
            'message': 'Audio pronunciation checking not available in lightweight mode. Keep practicing!',
            'tips': ['Practice speaking clearly', 'Record yourself and listen back', 'Try breaking words into syllables']
        }
        
        return response
    
    def _generate_pronunciation_guide(self, text: str) -> str:
        """Generate basic pronunciation guide"""
        # Simple pronunciation tips
        guides = {
            'th': 'θ (put tongue between teeth)',
            'ch': 'tʃ (like "church")',
            'sh': 'ʃ (like "shoe")',
            'ng': 'ŋ (like "sing")',
            'oo': 'u: (like "food")',
            'ee': 'i: (like "see")'
        }
        
        guide_parts = []
        for pattern, guide in guides.items():
            if pattern in text.lower():
                guide_parts.append(f"{pattern} → {guide}")
        
        if guide_parts:
            return "Pronunciation tips: " + ", ".join(guide_parts)
        else:
            return "Speak clearly and slowly for best results!"
    
    def _generate_phonetic_guide(self, text: str) -> str:
        """Generate basic phonetic representation"""
        # Simple phonetic mapping for common sounds
        phonetic_map = {
            'th': 'θ', 'ch': 'tʃ', 'sh': 'ʃ', 'ng': 'ŋ',
            'ee': 'i:', 'oo': 'u:', 'ar': 'ɑr', 'er': 'ər',
            'a': 'æ', 'e': 'e', 'i': 'ɪ', 'o': 'ɔ', 'u': 'ʌ'
        }
        
        phonetic = text.lower()
        for english, ipa in phonetic_map.items():
            phonetic = phonetic.replace(english, ipa)
        
        return f"/{phonetic}/"
    
    def _find_pronunciation_issues(self, target: str, user_input: str) -> list:
        """Find common pronunciation issues"""
        issues = []
        
        # Check for common problem sounds
        problem_sounds = ['th', 'r', 'l', 'v', 'w']
        
        for sound in problem_sounds:
            if sound in target and sound not in user_input:
                issues.append(sound)
        
        return issues[:3]  # Limit to 3 issues
    
    def get_voice_settings(self) -> Dict[str, Any]:
        """Get current voice service settings"""
        return {
            'tts_available': False,
            'stt_available': False,  # STT now handled by web_stt_service
            'pronunciation_check_available': True,  # Text-based only
            'languages': ['en', 'fa'],
            'mode': 'lightweight',
            'features': {
                'text_to_speech': 'Mock only (use browser TTS)',
                'speech_to_text': 'Use web STT service for unlimited voice recognition', 
                'pronunciation_check': 'Text-based similarity',
                'phonetic_guide': 'Available',
                'pronunciation_tips': 'Available'
            },
            'stt_migration': {
                'old_service': 'SpeechRecognition with 50-call daily limit',
                'new_service': 'Google Translate STT with unlimited usage',
                'endpoint': '/api/stt with action=microphone'
            }
        }
    
    def practice_pronunciation(self, word_list: list) -> Dict[str, Any]:
        """Generate pronunciation practice session"""
        try:
            if not word_list:
                return {'error': 'No words provided for practice'}
            
            practice_session = {
                'success': True,
                'words': [],
                'session_id': f"practice_{random.randint(1000, 9999)}",
                'instructions': 'Read each word aloud and type what you said for feedback.'
            }
            
            for word in word_list[:10]:  # Limit to 10 words
                word_info = {
                    'word': word,
                    'phonetic': self._generate_phonetic_guide(word),
                    'pronunciation_guide': self._generate_pronunciation_guide(word),
                    'tips': 'Break the word into syllables and say each part slowly.'
                }
                practice_session['words'].append(word_info)
            
            return practice_session
            
        except Exception as e:
            logger.error(f"Error creating practice session: {e}")
            return {'error': str(e)}
