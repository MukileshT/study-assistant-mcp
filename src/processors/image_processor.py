"""
Image preprocessing and enhancement utilities.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageEnhance, ImageOps
import io

from src.utils.logger import get_logger
from src.utils.error_handlers import ProcessingError
from src.utils.validators import validate_image_file

logger = get_logger(__name__)


class ImageProcessor:
    """Processor for image preprocessing and enhancement."""
    
    def __init__(self):
        """Initialize image processor."""
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp'}
        logger.info("Image processor initialized")
    
    def load_image(self, image_path: Path) -> Image.Image:
        """
        Load image from file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            PIL Image object
            
        Raises:
            ProcessingError: If image cannot be loaded
        """
        try:
            validate_image_file(image_path)
            img = Image.open(image_path)
            
            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            logger.info(f"Loaded image: {image_path.name} ({img.size[0]}x{img.size[1]})")
            return img
            
        except Exception as e:
            raise ProcessingError(
                f"Failed to load image: {str(e)}",
                file_path=str(image_path),
                stage="load"
            )
    
    def auto_rotate(self, img: Image.Image) -> Image.Image:
        """
        Auto-rotate image based on EXIF orientation.
        
        Args:
            img: PIL Image object
            
        Returns:
            Rotated image
        """
        try:
            # Apply EXIF orientation
            img = ImageOps.exif_transpose(img)
            logger.debug("Applied EXIF orientation")
            return img
        except Exception as e:
            logger.warning(f"Could not apply EXIF orientation: {str(e)}")
            return img
    
    def detect_and_correct_rotation(self, img: Image.Image) -> Image.Image:
        """
        Detect and correct image rotation using text orientation.
        
        Args:
            img: PIL Image object
            
        Returns:
            Corrected image
        """
        try:
            # Convert to OpenCV format
            img_array = np.array(img)
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Detect text orientation using edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                                    minLineLength=100, maxLineGap=10)
            
            if lines is not None and len(lines) > 5:
                # Calculate dominant angle
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    angles.append(angle)
                
                # Find most common angle (within 5 degree bins)
                median_angle = np.median(angles)
                
                # Correct if rotation is significant
                if abs(median_angle) > 2:  # More than 2 degrees
                    # Round to nearest 90 degrees if close
                    if 85 <= abs(median_angle) <= 95:
                        rotation_angle = 90 if median_angle > 0 else -90
                    elif 175 <= abs(median_angle) <= 185:
                        rotation_angle = 180
                    else:
                        rotation_angle = median_angle
                    
                    img = img.rotate(-rotation_angle, expand=True, fillcolor='white')
                    logger.info(f"Corrected rotation by {rotation_angle:.1f} degrees")
            
            return img
            
        except Exception as e:
            logger.warning(f"Rotation detection failed: {str(e)}")
            return img
    
    def enhance_contrast(self, img: Image.Image, factor: float = 1.3) -> Image.Image:
        """
        Enhance image contrast.
        
        Args:
            img: PIL Image object
            factor: Contrast enhancement factor (1.0 = no change)
            
        Returns:
            Enhanced image
        """
        try:
            enhancer = ImageEnhance.Contrast(img)
            enhanced = enhancer.enhance(factor)
            logger.debug(f"Enhanced contrast by factor {factor}")
            return enhanced
        except Exception as e:
            logger.warning(f"Contrast enhancement failed: {str(e)}")
            return img
    
    def enhance_sharpness(self, img: Image.Image, factor: float = 1.5) -> Image.Image:
        """
        Enhance image sharpness.
        
        Args:
            img: PIL Image object
            factor: Sharpness enhancement factor (1.0 = no change)
            
        Returns:
            Enhanced image
        """
        try:
            enhancer = ImageEnhance.Sharpness(img)
            enhanced = enhancer.enhance(factor)
            logger.debug(f"Enhanced sharpness by factor {factor}")
            return enhanced
        except Exception as e:
            logger.warning(f"Sharpness enhancement failed: {str(e)}")
            return img
    
    def adjust_brightness(self, img: Image.Image, factor: float = 1.0) -> Image.Image:
        """
        Adjust image brightness.
        
        Args:
            img: PIL Image object
            factor: Brightness factor (1.0 = no change)
            
        Returns:
            Adjusted image
        """
        try:
            # Auto-adjust if factor is 1.0
            if factor == 1.0:
                # Calculate average brightness
                img_array = np.array(img.convert('L'))
                avg_brightness = np.mean(img_array)
                
                # Adjust if too dark or too bright
                if avg_brightness < 100:
                    factor = 1.2
                elif avg_brightness > 200:
                    factor = 0.9
            
            if factor != 1.0:
                enhancer = ImageEnhance.Brightness(img)
                enhanced = enhancer.enhance(factor)
                logger.debug(f"Adjusted brightness by factor {factor}")
                return enhanced
            
            return img
        except Exception as e:
            logger.warning(f"Brightness adjustment failed: {str(e)}")
            return img
    
    def denoise(self, img: Image.Image) -> Image.Image:
        """
        Remove noise from image.
        
        Args:
            img: PIL Image object
            
        Returns:
            Denoised image
        """
        try:
            img_array = np.array(img)
            
            # Apply bilateral filter for noise reduction while preserving edges
            if len(img_array.shape) == 3:
                denoised = cv2.bilateralFilter(img_array, 9, 75, 75)
            else:
                denoised = cv2.bilateralFilter(img_array, 9, 75, 75)
            
            img_denoised = Image.fromarray(denoised)
            logger.debug("Applied denoising")
            return img_denoised
            
        except Exception as e:
            logger.warning(f"Denoising failed: {str(e)}")
            return img
    
    def remove_shadows(self, img: Image.Image) -> Image.Image:
        """
        Attempt to remove shadows from image.
        
        Args:
            img: PIL Image object
            
        Returns:
            Image with reduced shadows
        """
        try:
            img_array = np.array(img.convert('RGB'))
            
            # Convert to LAB color space
            lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l_clahe = clahe.apply(l)
            
            # Merge channels
            lab_clahe = cv2.merge([l_clahe, a, b])
            
            # Convert back to RGB
            result = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2RGB)
            
            img_result = Image.fromarray(result)
            logger.debug("Applied shadow removal")
            return img_result
            
        except Exception as e:
            logger.warning(f"Shadow removal failed: {str(e)}")
            return img
    
    def resize_for_processing(
        self,
        img: Image.Image,
        max_dimension: int = 2048
    ) -> Image.Image:
        """
        Resize image for optimal processing.
        
        Args:
            img: PIL Image object
            max_dimension: Maximum width or height
            
        Returns:
            Resized image
        """
        try:
            width, height = img.size
            
            if max(width, height) > max_dimension:
                # Calculate new size maintaining aspect ratio
                if width > height:
                    new_width = max_dimension
                    new_height = int(height * (max_dimension / width))
                else:
                    new_height = max_dimension
                    new_width = int(width * (max_dimension / height))
                
                img_resized = img.resize((new_width, new_height), Image.LANCZOS)
                logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
                return img_resized
            
            return img
            
        except Exception as e:
            logger.warning(f"Resizing failed: {str(e)}")
            return img
    
    def preprocess(
        self,
        image_path: Path,
        auto_rotate: bool = True,
        enhance: bool = True,
        denoise: bool = True,
        remove_shadows: bool = False,
        max_dimension: int = 2048,
    ) -> Image.Image:
        """
        Complete preprocessing pipeline.
        
        Args:
            image_path: Path to image file
            auto_rotate: Apply auto-rotation
            enhance: Apply enhancement (contrast, sharpness)
            denoise: Apply denoising
            remove_shadows: Apply shadow removal
            max_dimension: Maximum dimension for resizing
            
        Returns:
            Preprocessed image
            
        Raises:
            ProcessingError: If preprocessing fails
        """
        try:
            logger.info(f"Starting preprocessing: {image_path.name}")
            
            # Load image
            img = self.load_image(image_path)
            
            # Auto-rotate based on EXIF
            if auto_rotate:
                img = self.auto_rotate(img)
                img = self.detect_and_correct_rotation(img)
            
            # Resize if needed
            img = self.resize_for_processing(img, max_dimension)
            
            # Remove shadows (optional, can reduce quality)
            if remove_shadows:
                img = self.remove_shadows(img)
            
            # Denoise
            if denoise:
                img = self.denoise(img)
            
            # Enhance
            if enhance:
                img = self.adjust_brightness(img)
                img = self.enhance_contrast(img)
                img = self.enhance_sharpness(img)
            
            logger.info(f"Preprocessing complete: {image_path.name}")
            return img
            
        except Exception as e:
            raise ProcessingError(
                f"Preprocessing failed: {str(e)}",
                file_path=str(image_path),
                stage="preprocess"
            )
    
    def save_processed(
        self,
        img: Image.Image,
        output_path: Path,
        quality: int = 95,
    ) -> Path:
        """
        Save processed image.
        
        Args:
            img: PIL Image object
            output_path: Output file path
            quality: JPEG quality (1-100)
            
        Returns:
            Path to saved file
        """
        try:
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with high quality
            if output_path.suffix.lower() in ['.jpg', '.jpeg']:
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
            else:
                img.save(output_path, optimize=True)
            
            logger.info(f"Saved processed image: {output_path}")
            return output_path
            
        except Exception as e:
            raise ProcessingError(
                f"Failed to save image: {str(e)}",
                file_path=str(output_path),
                stage="save"
            )
    
    def get_image_info(self, image_path: Path) -> dict:
        """
        Get image information.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with image info
        """
        try:
            img = self.load_image(image_path)
            
            return {
                "filename": image_path.name,
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "width": img.size[0],
                "height": img.size[1],
                "file_size_mb": image_path.stat().st_size / (1024 * 1024),
            }
            
        except Exception as e:
            logger.error(f"Failed to get image info: {str(e)}")
            return {}