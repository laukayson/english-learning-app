# Image Generation Service for Language Learning App

import os
import requests
import json
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.huggingface_token = config.get('HUGGINGFACE_TOKEN', '')
        self.image_model = config.get('IMAGE_MODEL', 'runwayml/stable-diffusion-v1-5')
        self.cache_dir = config.get('IMAGE_CACHE_DIR', 'cache/images')
        self.fallback_enabled = config.get('FALLBACK_ENABLED', True)
        
        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Educational prompt templates
        self.educational_prompts = {
            'greetings': 'friendly people greeting each other, educational illustration, clean background',
            'family': 'happy family members together, educational style, simple illustration',
            'food': 'healthy food items on a table, educational poster style, bright colours',
            'daily_routines': 'person doing daily activities, educational infographic style',
            'shopping': 'people shopping at a market, educational illustration, clear details',
            'transportation': 'various transportation methods, educational diagram style',
            'weather': 'different weather conditions, educational illustration, simple design',
            'colors_shapes': 'colourful shapes and objects, educational poster, bright and clear',
            'body_parts': 'human body diagram, educational style, labeled illustration',
            'emotions': 'facial expressions showing emotions, educational chart style',
            'numbers_time': 'clocks and numbers, educational illustration, clear and simple',
            'clothing': 'different types of clothing, educational poster style',
            'house_home': 'house rooms and furniture, educational illustration, clean design',
            'work_professions': 'people in different professions, educational style',
            'hobbies': 'people enjoying hobbies, educational illustration style',
            'health_medical': 'medical items and health symbols, educational poster',
            'travel': 'travel destinations and activities, educational illustration',
            'technology': 'modern technology devices, educational diagram style',
            'environment': 'nature and environmental scenes, educational illustration',
            'culture': 'cultural symbols and activities, educational poster style'
        }

    def generate_image(self, topic_id: str, custom_prompt: str = None, style: str = 'educational') -> Dict[str, Any]:
        """
        Generate an image for a specific topic
        
        Args:
            topic_id: The topic identifier
            custom_prompt: Custom prompt override
            style: Image style (educational, realistic, cartoon)
            
        Returns:
            Dictionary with image data and metadata
        """
        try:
            # Check cache first
            cache_key = f"{topic_id}_{style}_{hash(custom_prompt or '')}"
            cached_image = self._get_cached_image(cache_key)
            if cached_image:
                logger.info(f"Returning cached image for topic: {topic_id}")
                return cached_image

            # Prepare prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self.educational_prompts.get(topic_id, f"educational illustration about {topic_id}")
            
            # Add style modifiers
            style_modifiers = {
                'educational': ', educational illustration, clean design, appropriate for language learning',
                'realistic': ', photorealistic, high quality, detailed',
                'cartoon': ', cartoon style, friendly, colourful, simple'
            }
            
            full_prompt = prompt + style_modifiers.get(style, style_modifiers['educational'])
            
            # Try to generate with AI service
            if self.huggingface_token:
                result = self._generate_with_huggingface(full_prompt, topic_id)
                if result['success']:
                    # Cache the result
                    self._cache_image(cache_key, result)
                    return result
            
            # Fallback to generated placeholder
            if self.fallback_enabled:
                logger.warning(f"Using fallback image generation for topic: {topic_id}")
                result = self._generate_fallback_image(topic_id, prompt)
                self._cache_image(cache_key, result)
                return result
            
            return {
                'success': False,
                'error': 'Image generation service unavailable',
                'image_url': None,
                'alt_text': f"Image for {topic_id}"
            }

        except Exception as e:
            logger.error(f"Error generating image for topic {topic_id}: {str(e)}")
            return self._generate_error_image(topic_id, str(e))

    def _generate_with_huggingface(self, prompt: str, topic_id: str) -> Dict[str, Any]:
        """Generate image using Hugging Face API"""
        try:
            api_url = f"https://api-inference.huggingface.co/models/{self.image_model}"
            headers = {"Authorization": f"Bearer {self.huggingface_token}"}
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_inference_steps": 20,
                    "guidance_scale": 7.5,
                    "width": 512,
                    "height": 512
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                # Save image
                image_filename = f"{topic_id}_{hash(prompt)}.png"
                image_path = os.path.join(self.cache_dir, image_filename)
                
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                
                return {
                    'success': True,
                    'image_url': f"/images/{image_filename}",
                    'local_path': image_path,
                    'alt_text': f"AI generated image for {topic_id}",
                    'prompt_used': prompt,
                    'generated_with': 'huggingface'
                }
            
            elif response.status_code == 503:
                logger.warning("Hugging Face model is loading, using fallback")
                return {'success': False, 'error': 'Model loading'}
            
            else:
                logger.error(f"Hugging Face API error: {response.status_code}")
                return {'success': False, 'error': f"API error: {response.status_code}"}

        except requests.exceptions.Timeout:
            logger.error("Hugging Face API timeout")
            return {'success': False, 'error': 'API timeout'}
        
        except Exception as e:
            logger.error(f"Hugging Face generation error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _generate_fallback_image(self, topic_id: str, prompt: str) -> Dict[str, Any]:
        """Generate a fallback image using PIL"""
        try:
            # Create a simple illustration
            width, height = 512, 512
            image = Image.new('RGB', (width, height), color='#f0f8ff')
            draw = ImageDraw.Draw(image)
            
            # Try to load a font
            try:
                font_large = ImageFont.truetype("arial.ttf", 48)
                font_small = ImageFont.truetype("arial.ttf", 24)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Get topic emoji and colours
            topic_info = self._get_topic_visual_info(topic_id)
            
            # Draw background gradient
            for y in range(height):
                colour_ratio = y / height
                r = int(240 + colour_ratio * 15)
                g = int(248 + colour_ratio * 7)
                b = int(255 - colour_ratio * 15)
                colour = (r, g, b)
                draw.line([(0, y), (width, y)], fill=colour)
            
            # Draw decorative border
            border_colour = topic_info['border_colour']
            draw.rectangle([10, 10, width-10, height-10], outline=border_colour, width=5)
            
            # Draw topic emoji/icon
            emoji_size = 120
            emoji_x = (width - emoji_size) // 2
            emoji_y = height // 3
            
            # Since we can't easily render emojis with PIL, draw a placeholder shape
            shape_colour = topic_info['shape_colour']
            if topic_info['shape'] == 'circle':
                draw.ellipse([emoji_x, emoji_y, emoji_x + emoji_size, emoji_y + emoji_size], 
                           fill=shape_colour, outline=border_colour, width=3)
            else:
                draw.rectangle([emoji_x, emoji_y, emoji_x + emoji_size, emoji_y + emoji_size], 
                             fill=shape_colour, outline=border_colour, width=3)
            
            # Draw topic name
            topic_name = topic_id.replace('_', ' ').title()
            name_bbox = draw.textbbox((0, 0), topic_name, font=font_large)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = (width - name_width) // 2
            name_y = emoji_y + emoji_size + 30
            
            # Draw text with shadow
            shadow_offset = 2
            draw.text((name_x + shadow_offset, name_y + shadow_offset), topic_name, 
                     fill='#cccccc', font=font_large)
            draw.text((name_x, name_y), topic_name, fill='#333333', font=font_large)
            
            # Draw subtitle
            subtitle = "Language Learning Topic"
            subtitle_bbox = draw.textbbox((0, 0), subtitle, font=font_small)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (width - subtitle_width) // 2
            subtitle_y = name_y + 60
            
            draw.text((subtitle_x, subtitle_y), subtitle, fill='#666666', font=font_small)
            
            # Save image
            image_filename = f"fallback_{topic_id}_{hash(prompt)}.png"
            image_path = os.path.join(self.cache_dir, image_filename)
            image.save(image_path, 'PNG')
            
            return {
                'success': True,
                'image_url': f"/images/{image_filename}",
                'local_path': image_path,
                'alt_text': f"Educational illustration for {topic_name}",
                'prompt_used': prompt,
                'generated_with': 'fallback',
                'is_fallback': True
            }

        except Exception as e:
            logger.error(f"Fallback image generation error: {str(e)}")
            return self._generate_error_image(topic_id, str(e))

    def _get_topic_visual_info(self, topic_id: str) -> Dict[str, Any]:
        """Get visual styling information for topics"""
        topic_styles = {
            'greetings': {'shape': 'circle', 'shape_colour': '#FFE4B5', 'border_colour': '#FF6B6B'},
            'family': {'shape': 'rectangle', 'shape_colour': '#E6F3FF', 'border_colour': '#4ECDC4'},
            'food': {'shape': 'circle', 'shape_colour': '#FFE4E1', 'border_colour': '#FF8C69'},
            'daily_routines': {'shape': 'rectangle', 'shape_colour': '#F0F8FF', 'border_colour': '#87CEEB'},
            'shopping': {'shape': 'circle', 'shape_colour': '#F5F5DC', 'border_colour': '#DEB887'},
            'transportation': {'shape': 'rectangle', 'shape_colour': '#E0E0E0', 'border_colour': '#808080'},
            'weather': {'shape': 'circle', 'shape_colour': '#E6F3FF', 'border_colour': '#4682B4'},
            'colors_shapes': {'shape': 'rectangle', 'shape_colour': '#FFFACD', 'border_colour': '#FFD700'},
            'body_parts': {'shape': 'circle', 'shape_colour': '#FFF8DC', 'border_colour': '#F4A460'},
            'emotions': {'shape': 'circle', 'shape_colour': '#FFE4E1', 'border_colour': '#FF69B4'},
            'numbers_time': {'shape': 'rectangle', 'shape_colour': '#F0FFFF', 'border_colour': '#00CED1'},
            'clothing': {'shape': 'rectangle', 'shape_colour': '#F5F0FF', 'border_colour': '#9370DB'},
            'house_home': {'shape': 'rectangle', 'shape_colour': '#F0F8FF', 'border_colour': '#228B22'},
            'work_professions': {'shape': 'rectangle', 'shape_colour': '#FFF8DC', 'border_colour': '#B8860B'},
            'hobbies': {'shape': 'circle', 'shape_colour': '#F0FFF0', 'border_colour': '#32CD32'},
            'health_medical': {'shape': 'circle', 'shape_colour': '#F0FFFF', 'border_colour': '#00CED1'},
            'travel': {'shape': 'rectangle', 'shape_colour': '#FFFACD', 'border_colour': '#DAA520'},
            'technology': {'shape': 'rectangle', 'shape_colour': '#F5F5F5', 'border_colour': '#696969'},
            'environment': {'shape': 'circle', 'shape_colour': '#F0FFF0', 'border_colour': '#228B22'},
            'culture': {'shape': 'rectangle', 'shape_colour': '#FFF8DC', 'border_colour': '#CD853F'}
        }
        
        return topic_styles.get(topic_id, {
            'shape': 'rectangle', 
            'shape_colour': '#F8F8FF', 
            'border_colour': '#708090'
        })

    def _generate_error_image(self, topic_id: str, error_message: str) -> Dict[str, Any]:
        """Generate an error placeholder image"""
        try:
            width, height = 512, 512
            image = Image.new('RGB', (width, height), color='#ffebee')
            draw = ImageDraw.Draw(image)
            
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Draw error indicator
            draw.rectangle([50, 50, width-50, height-50], outline='#f44336', width=3)
            
            # Draw error text
            error_text = "Image Unavailable"
            text_bbox = draw.textbbox((0, 0), error_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (width - text_width) // 2
            text_y = height // 2 - 20
            
            draw.text((text_x, text_y), error_text, fill='#f44336', font=font)
            
            # Save error image
            image_filename = f"error_{topic_id}_{hash(error_message)}.png"
            image_path = os.path.join(self.cache_dir, image_filename)
            image.save(image_path, 'PNG')
            
            return {
                'success': False,
                'image_url': f"/images/{image_filename}",
                'local_path': image_path,
                'alt_text': f"Error generating image for {topic_id}",
                'error': error_message,
                'is_error': True
            }

        except Exception as e:
            logger.error(f"Error image generation failed: {str(e)}")
            return {
                'success': False,
                'image_url': None,
                'alt_text': f"Image for {topic_id}",
                'error': f"Complete image generation failure: {str(e)}"
            }

    def _get_cached_image(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached image if available"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Check if image file still exists
                if cache_data.get('local_path') and os.path.exists(cache_data['local_path']):
                    return cache_data
                
        except Exception as e:
            logger.error(f"Cache retrieval error: {str(e)}")
        
        return None

    def _cache_image(self, cache_key: str, image_data: Dict[str, Any]) -> None:
        """Cache image data"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            with open(cache_file, 'w') as f:
                json.dump(image_data, f)
                
        except Exception as e:
            logger.error(f"Cache storage error: {str(e)}")

    def get_image_variations(self, topic_id: str, count: int = 3) -> List[Dict[str, Any]]:
        """Generate multiple image variations for a topic"""
        variations = []
        base_prompt = self.educational_prompts.get(topic_id, f"educational illustration about {topic_id}")
        
        style_variations = [
            ('educational', base_prompt),
            ('cartoon', base_prompt + ', cartoon style'),
            ('realistic', base_prompt + ', photorealistic style')
        ]
        
        for i, (style, prompt) in enumerate(style_variations[:count]):
            result = self.generate_image(topic_id, prompt, style)
            if result['success']:
                result['variation_id'] = i
                variations.append(result)
        
        return variations

    def cleanup_cache(self, max_age_days: int = 30) -> None:
        """Clean up old cached images"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        logger.info(f"Removed old cache file: {filename}")
                        
        except Exception as e:
            logger.error(f"Cache cleanup error: {str(e)}")

def create_image_service(config: Dict[str, Any]) -> ImageService:
    """Factory function to create ImageService instance"""
    return ImageService(config)
