import os
import base64
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import aiofiles
from PIL import Image
import PyPDF2
import io

from config import settings
from services.logger import get_logger

class FileHandler:
    """Dosya işleme ve yönetim sınıfı"""
    
    def __init__(self):
        self.logger = get_logger("FileHandler")
        self.allowed_image_types = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.allowed_pdf_types = {'.pdf'}
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        
    async def save_upload(self, file, request_id: str) -> Path:
        """Yüklenen dosyayı kaydet"""
        try:
            # Dosya adını güvenli hale getir
            safe_filename = f"{request_id}_{file.filename}"
            file_path = settings.upload_dir / safe_filename
            
            # Dosyayı kaydet
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            self.logger.info(f"File saved: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"File save error: {str(e)}")
            raise
    
    async def process_file(self, file_path: Path) -> Dict[str, Any]:
        """Dosyayı işle ve base64'e dönüştür"""
        try:
            file_ext = file_path.suffix.lower()
            
            if file_ext in self.allowed_image_types:
                return await self._process_image(file_path)
            elif file_ext in self.allowed_pdf_types:
                return await self._process_pdf(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
                
        except Exception as e:
            self.logger.error(f"File processing error: {str(e)}")
            raise
    
    async def _process_image(self, file_path: Path) -> Dict[str, Any]:
        """Görsel dosyayı işle"""
        try:
            # Görseli aç ve optimize et
            with Image.open(file_path) as img:
                # EXIF orientation düzelt
                img = self._fix_orientation(img)
                
                # Boyut kontrolü ve yeniden boyutlandırma
                max_size = (1920, 1080)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Base64'e dönüştür
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                image_data = buffer.getvalue()
                
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            return {
                "type": "image",
                "data": image_b64,
                "metadata": {
                    "filename": file_path.name,
                    "size": len(image_data),
                    "dimensions": img.size
                }
            }
            
        except Exception as e:
            self.logger.error(f"Image processing error: {str(e)}")
            raise
    
    async def _process_pdf(self, file_path: Path) -> Dict[str, Any]:
        """PDF dosyayı işle"""
        try:
            with open(file_path, 'rb') as f:
                pdf_data = f.read()
                
            # PDF bilgilerini oku
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
            num_pages = len(pdf_reader.pages)
            
            # İlk sayfadan metin çıkar
            first_page_text = ""
            if num_pages > 0:
                first_page_text = pdf_reader.pages[0].extract_text()[:500]
            
            pdf_b64 = base64.b64encode(pdf_data).decode('utf-8')
            
            return {
                "type": "pdf",
                "data": pdf_b64,
                "metadata": {
                    "filename": file_path.name,
                    "size": len(pdf_data),
                    "pages": num_pages,
                    "preview": first_page_text
                }
            }
            
        except Exception as e:
            self.logger.error(f"PDF processing error: {str(e)}")
            raise
    
    def _fix_orientation(self, img: Image.Image) -> Image.Image:
        """EXIF verilerine göre görsel yönünü düzelt"""
        try:
            # EXIF verilerini kontrol et
            exif = img._getexif()
            if exif is not None:
                orientation = exif.get(0x0112)
                if orientation:
                    rotations = {
                        3: 180,
                        6: 270,
                        8: 90
                    }
                    if orientation in rotations:
                        img = img.rotate(rotations[orientation], expand=True)
        except:
            pass
        return img
    
    def cleanup_old_files(self, days: int = 7):
        """Eski dosyaları temizle"""
        import time
        current_time = time.time()
        
        for file_path in settings.upload_dir.iterdir():
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > days * 24 * 3600:
                    file_path.unlink()
                    self.logger.info(f"Deleted old file: {file_path}")