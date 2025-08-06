import os
import sys
import asyncio
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import traceback
import shutil
import glob
import subprocess

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from manim import *
from agents.code_agent import CodeAgent
from agents.topic_agent import TopicAgent
from agents.solution_agent import SolutionAgent
from agents.scene_manager import SceneManager
from services.logger import get_logger
from services.video_merger import VideoMerger
from services.gemini import generate
from prompts.error_prompt import get_error_fix_prompt
from config import settings, manim_config

class VideoCreator:
    """Video oluşturma ve yönetim sınıfı - Ses ve erişim düzeltmeleri ile"""
    
    def __init__(self):
        self.logger = get_logger("VideoCreator")
        self.topic_agent = TopicAgent()
        self.solution_agent = SolutionAgent()
        self.code_agent = CodeAgent()
        self.scene_manager = SceneManager()
        self.video_merger = VideoMerger()
        self.status_db = {}
        
        # Retry ayarları
        self.max_fix_attempts = 3
        self.max_regenerate_attempts = 2
        
        # Video çıktı dizinini oluştur
        self.final_video_dir = settings.static_dir / "final_videos"
        self.final_video_dir.mkdir(exist_ok=True)
        
        # Ses ayarları
        self.audio_config = {
            "codec": "aac",
            "bitrate": "128k",
            "sample_rate": "44100"
        }
        
    async def create_video(self, 
                          request_id: str,
                          content: str,
                          video_type: str,
                          files: List[Dict[str, Any]] = None) -> str:
        """Ana video oluşturma metodu"""
        try:
            self.update_status(request_id, "processing", "Video oluşturma başladı")
            
            # Dosyaları işle
            image_b64 = None
            pdf_b64 = None
            if files:
                for file in files:
                    if file["type"] == "image":
                        image_b64 = file["data"]
                    elif file["type"] == "pdf":
                        pdf_b64 = file["data"]
            
            # Video tipine göre işlem yap
            if video_type == "full":
                video_path = await self._create_full_video_with_retry(
                    request_id, content, image_b64, pdf_b64
                )
            elif video_type == "topic":
                video_path = await self._create_topic_video_with_retry(
                    request_id, content
                )
            else:  # solution
                video_path = await self._create_solution_video_with_retry(
                    request_id, content, image_b64, pdf_b64
                )
            
            self.update_status(request_id, "completed", "Video hazır", video_path)
            return video_path
            
        except Exception as e:
            self.logger.error(f"Video creation error: {str(e)}\n{traceback.format_exc()}")
            self.update_status(request_id, "failed", f"Video oluşturulamadı: {str(e)}")
            raise
    
    async def _create_solution_video_with_retry(self,
                                              request_id: str,
                                              content: str,
                                              image_b64: Optional[str],
                                              pdf_b64: Optional[str]) -> str:
        """Çözüm videosu oluştur - Retry ile"""
        self.logger.info(f"Creating solution video with retry for request: {request_id}")
        
        for regenerate_attempt in range(self.max_regenerate_attempts):
            try:
                self.update_status(
                    request_id, 
                    "processing", 
                    f"Kod oluşturuluyor (Deneme {regenerate_attempt + 1}/{self.max_regenerate_attempts})"
                )
                
                # Çözümü al
                solution = self.solution_agent.process(content, image_b64, pdf_b64)
                
                # Manim kodunu oluştur
                manim_code = self.code_agent.process(solution, image_b64, "solution")
                
                # Retry mekanizması ile renderla
                video_path = await self._render_video_with_retry(
                    request_id, manim_code, content, image_b64, "solution"
                )
                
                return video_path
                
            except Exception as e:
                self.logger.warning(f"Regeneration attempt {regenerate_attempt + 1} failed: {str(e)}")
                if regenerate_attempt == self.max_regenerate_attempts - 1:
                    raise Exception("Video oluşturulamadı: Tüm denemeler başarısız")
                
                await asyncio.sleep(2)
        
        raise Exception("Video oluşturulamadı: Beklenmeyen hata")
    
    async def _create_topic_video_with_retry(self,
                                           request_id: str,
                                           content: str) -> str:
        """Konu anlatım videosu oluştur - Retry ile"""
        self.logger.info(f"Creating topic video with retry for request: {request_id}")
        
        for regenerate_attempt in range(self.max_regenerate_attempts):
            try:
                self.update_status(
                    request_id, 
                    "processing", 
                    f"Konu anlatımı oluşturuluyor (Deneme {regenerate_attempt + 1}/{self.max_regenerate_attempts})"
                )
                
                # Konu anlatımını al
                explanation = self.topic_agent.process(content)
                
                # Manim kodunu oluştur
                manim_code = self.code_agent.process(explanation, scene_type="topic")
                
                # Retry mekanizması ile renderla
                video_path = await self._render_video_with_retry(
                    request_id, manim_code, content, None, "topic"
                )
                
                return video_path
                
            except Exception as e:
                self.logger.warning(f"Topic generation attempt {regenerate_attempt + 1} failed: {str(e)}")
                if regenerate_attempt == self.max_regenerate_attempts - 1:
                    raise Exception("Video oluşturulamadı: Tüm konu anlatımı denemeleri başarısız")
                
                await asyncio.sleep(2)
        
        raise Exception("Video oluşturulamadı: Beklenmeyen hata")
    
    async def _create_full_video_with_retry(self, 
                                          request_id: str,
                                          content: str,
                                          image_b64: Optional[str],
                                          pdf_b64: Optional[str]) -> str:
        """Tam video oluştur - Retry ile"""
        self.logger.info(f"Creating full video with retry for request: {request_id}")
        
        for regenerate_attempt in range(self.max_regenerate_attempts):
            try:
                self.update_status(
                    request_id, 
                    "processing", 
                    f"Tam video oluşturuluyor (Deneme {regenerate_attempt + 1}/{self.max_regenerate_attempts})"
                )
                
                # Çözümü al
                solution = self.solution_agent.process(content, image_b64, pdf_b64)
                
                # Sahneleri oluştur
                self.scene_manager.create_intro_scene(
                    title="Matematik Çözümü",
                    subtitle=content[:50] + "..."
                )
                
                self.scene_manager.create_content_scene(
                    solution,
                    scene_type="solution",
                    image_b64=image_b64
                )
                
                self.scene_manager.create_outro_scene(
                    summary="Bu videoda " + content[:100] + " problemini çözdük",
                    call_to_action="Daha fazla çözüm için kanalımıza abone olun!"
                )
                
                # Sahneleri birleştir ve renderla
                combined_code = self.scene_manager.combine_all_scenes()
                
                video_path = await self._render_video_with_retry(
                    request_id, combined_code, content, image_b64, "full"
                )
                
                return video_path
                
            except Exception as e:
                self.logger.warning(f"Full video generation attempt {regenerate_attempt + 1} failed: {str(e)}")
                if regenerate_attempt == self.max_regenerate_attempts - 1:
                    raise Exception("Video oluşturulamadı: Tüm tam video denemeleri başarısız")
                
                await asyncio.sleep(2)
        
        raise Exception("Video oluşturulamadı: Beklenmeyen hata")
    
    async def _render_video_with_retry(self, 
                                     request_id: str, 
                                     initial_code: str,
                                     original_content: str,
                                     image_b64: Optional[str],
                                     scene_type: str) -> str:
        """Retry mekanizması ile video render et"""
        current_code = initial_code
        
        for fix_attempt in range(self.max_fix_attempts):
            try:
                self.update_status(
                    request_id, 
                    "rendering", 
                    f"Video renderleniyor (Düzeltme denemesi {fix_attempt + 1}/{self.max_fix_attempts})"
                )
                
                video_path = await self._render_video(request_id, current_code)
                
                # Başarılı, video dosyasını döndür
                self.logger.info(f"Video successfully rendered on attempt {fix_attempt + 1}")
                return video_path
                
            except Exception as e:
                error_message = str(e)
                self.logger.warning(f"Render attempt {fix_attempt + 1} failed: {error_message}")
                
                if fix_attempt < self.max_fix_attempts - 1:
                    # Kodu düzelt ve tekrar dene
                    self.update_status(
                        request_id, 
                        "processing", 
                        f"Kod düzeltiliyor... (Hata: {error_message[:100]})"
                    )
                    
                    try:
                        current_code = await self._fix_manim_code(current_code, error_message)
                        self.logger.info(f"Code fixed for attempt {fix_attempt + 2}")
                    except Exception as fix_error:
                        self.logger.error(f"Code fix failed: {str(fix_error)}")
                        raise e
                else:
                    self.logger.error(f"All fix attempts failed. Final error: {error_message}")
                    raise e
        
        raise Exception("Video oluşturulamadı: Tüm düzeltme denemeleri başarısız")
    
    async def _fix_manim_code(self, broken_code: str, error_message: str) -> str:
        """Hatalı Manim kodunu düzelt"""
        self.logger.info("Attempting to fix Manim code...")
        
        # Error message'ı güvenli hale getir
        safe_error_message = error_message.replace('"', "'").replace("{", "{{").replace("}", "}}")
        safe_broken_code = broken_code.replace("{", "{{").replace("}", "}}")
        
        fix_prompt = get_error_fix_prompt().format(
            code=safe_broken_code,
            error=safe_error_message
        )
        
        try:
            # AI'dan düzeltilmiş kod al
            fixed_response = generate({"text": fix_prompt})
            
            # Kod bloğunu çıkar
            fixed_code = self._extract_python_code(fixed_response)
            
            # Eğer kod çıkarılamadıysa, yanıtın tamamını kullan
            if not fixed_code or len(fixed_code) < 100:
                fixed_code = fixed_response
            
            self.logger.info(f"Code fix generated, length: {len(fixed_code)}")
            return fixed_code
            
        except Exception as e:
            self.logger.error(f"Error during code fix: {str(e)}")
            raise Exception(f"Kod düzeltme başarısız: {str(e)}")
    
    async def _render_video(self, request_id: str, manim_code: str) -> str:
        """Manim kodunu renderla - Ses düzeltmeleri ile"""
        # Geçici dosya oluştur
        temp_file = Path(settings.temp_dir) / f"{request_id}_manim.py"
        temp_file.write_text(manim_code, encoding="utf-8")
        
        # Manim config ayarla - Ses desteği ile
        config.media_dir = str(settings.video_output_dir)
        config.output_file = request_id
        
        # Ses ayarları - Önemli!
        config.enable_gui = False
        config.write_to_movie = True
        config.save_last_frame = False
        
        manim_config.setup_defaults()
        
        # Modülü yükle ve çalıştır
        try:
            # Mevcut modülü temizle
            module_name = f"temp_manim_{request_id}"
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # Yeni modülü yükle
            spec = importlib.util.spec_from_file_location(module_name, temp_file)
            if spec is None or spec.loader is None:
                raise ImportError("Module spec veya loader bulunamadı")
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Solution class'ını bul ve çalıştır
            if hasattr(module, 'Solution'):
                scene = module.Solution()
                
                # Render işlemi - Ses ile birlikte
                self.update_status(request_id, "rendering", "Video ses ile birlikte render ediliyor...")
                scene.render()
                
                # Video dosyasını bul ve taşı
                video_path = await self._find_and_move_video(request_id)
                
                if video_path and video_path.exists():
                    # Ses kontrolü ve düzeltmesi
                    video_with_audio = await self._ensure_audio_in_video(video_path)
                    
                    self.logger.info(f"Video successfully created with audio: {video_with_audio}")
                    return str(video_with_audio)
                else:
                    raise FileNotFoundError("Video dosyası bulunamadı veya taşınamadı")
            else:
                raise AttributeError("Solution class bulunamadı")
                
        except Exception as e:
            self.logger.error(f"Render error: {str(e)}")
            raise
        finally:
            # Geçici dosyayı temizle
            if temp_file.exists():
                temp_file.unlink()
    
    async def _ensure_audio_in_video(self, video_path: Path) -> Path:
        """Video'da ses olduğundan emin ol, yoksa ekle"""
        try:
            self.logger.info(f"Checking audio in video: {video_path}")
            
            # Video'da ses var mı kontrol et
            check_cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'a:0', 
                '-show_entries', 'stream=codec_name', '-of', 'csv=p=0', 
                str(video_path)
            ]
            
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            has_audio = result.returncode == 0 and result.stdout.strip()
            
            if has_audio:
                self.logger.info("Video already has audio")
                return video_path
            
            self.logger.warning("Video has no audio, looking for separate audio files...")
            
            # Aynı isimli ses dosyalarını ara
            video_base = video_path.with_suffix('')
            audio_files = []
            
            # Muhtemel ses dosyası uzantıları
            audio_extensions = ['.wav', '.mp3', '.aac', '.m4a']
            
            for ext in audio_extensions:
                audio_file = video_base.with_suffix(ext)
                if audio_file.exists():
                    audio_files.append(audio_file)
                    self.logger.info(f"Found audio file: {audio_file}")
            
            # Voiceover cache dizininde de ara
            voiceover_dir = settings.static_dir / "videomedia" / "voiceovers"
            if voiceover_dir.exists():
                for audio_file in voiceover_dir.glob("*.mp3"):
                    audio_files.append(audio_file)
                    self.logger.info(f"Found voiceover audio: {audio_file}")
            
            if not audio_files:
                self.logger.warning("No audio files found, returning video without audio")
                return video_path
            
            # En uygun ses dosyasını seç (en büyük boyutlu genellikle ana ses)
            main_audio = max(audio_files, key=lambda f: f.stat().st_size)
            self.logger.info(f"Using main audio file: {main_audio}")
            
            # Ses ve video'yu birleştir
            output_with_audio = video_path.with_name(f"{video_path.stem}_with_audio.mp4")
            
            merge_cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-i', str(main_audio),
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-shortest',
                str(output_with_audio)
            ]
            
            self.logger.info(f"Merging video with audio: {' '.join(merge_cmd)}")
            
            result = subprocess.run(merge_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and output_with_audio.exists():
                # Eski dosyayı sil ve yenisini ana isimle değiştir
                video_path.unlink()
                output_with_audio.rename(video_path)
                self.logger.info("Successfully merged video with audio")
                return video_path
            else:
                self.logger.error(f"Audio merge failed: {result.stderr}")
                return video_path
                
        except Exception as e:
            self.logger.warning(f"Audio processing failed: {str(e)}, returning original video")
            return video_path
    
    async def _find_and_move_video(self, request_id: str) -> Optional[Path]:
        """Oluşturulan video dosyasını bul ve güvenli yere taşı"""
        try:
            # Manim'in video çıktı dizininde ara
            video_output_base = settings.video_output_dir / "videos"
            
            # Muhtemel video dosyası yolları
            possible_paths = [
                video_output_base / "1080p60" / f"{request_id}.mp4",
                video_output_base / "720p30" / f"{request_id}.mp4",
                video_output_base / "480p15" / f"{request_id}.mp4",
                settings.video_output_dir / f"{request_id}.mp4",
            ]
            
            # Glob ile de ara
            glob_patterns = [
                str(video_output_base / "*" / f"{request_id}.mp4"),
                str(video_output_base / "*" / "*" / f"{request_id}.mp4"),
                str(settings.video_output_dir / f"*{request_id}*.mp4"),
            ]
            
            found_video = None
            
            # Önce doğrudan yollarda ara
            for path in possible_paths:
                if path.exists():
                    found_video = path
                    self.logger.info(f"Found video at: {path}")
                    break
            
            # Bulamazsa glob ile ara
            if not found_video:
                for pattern in glob_patterns:
                    matches = glob.glob(pattern)
                    if matches:
                        found_video = Path(matches[0])  # İlk eşleşeni al
                        self.logger.info(f"Found video via glob: {found_video}")
                        break
            
            if not found_video:
                self.logger.error(f"Video file not found for request_id: {request_id}")
                # Debug için tüm video dosyalarını listele
                all_videos = list(video_output_base.rglob("*.mp4"))
                self.logger.info(f"Available video files: {[str(v) for v in all_videos[-10:]]}")
                return None
            
            # Güvenli yere taşı
            final_path = self.final_video_dir / f"{request_id}.mp4"
            shutil.copy2(found_video, final_path)
            
            # İlgili dosyaları da taşı (srt, wav vs.)
            self._move_related_files(found_video, final_path)
            
            self.logger.info(f"Video moved from {found_video} to {final_path}")
            return final_path
            
        except Exception as e:
            self.logger.error(f"Error finding/moving video: {str(e)}")
            return None
    
    def _move_related_files(self, source_video: Path, target_video: Path):
        """Video ile ilgili diğer dosyaları da taşı (srt, wav vb.)"""
        try:
            source_base = source_video.with_suffix("")
            target_base = target_video.with_suffix("")
            
            # İlgili dosya uzantıları
            related_extensions = [".srt", ".wav", ".txt", ".json", ".mp3", ".aac"]
            
            for ext in related_extensions:
                source_file = source_base.with_suffix(ext)
                if source_file.exists():
                    target_file = target_base.with_suffix(ext)
                    shutil.copy2(source_file, target_file)
                    self.logger.info(f"Related file moved: {source_file} -> {target_file}")
                    
        except Exception as e:
            self.logger.warning(f"Error moving related files: {str(e)}")
    
    def _extract_python_code(self, response: str) -> str:
        """Yanıttan Python kodunu çıkarır"""
        import re
        code_match = re.search(r'```python\n(.*?)```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Alternatif pattern
        code_match = re.search(r'```\n(.*?)```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        return response.strip()
    
    def update_status(self, 
                     request_id: str, 
                     status: str, 
                     message: str,
                     video_path: Optional[str] = None):
        """İstek durumunu güncelle"""
        self.status_db[request_id] = {
            "status": status,
            "message": message,
            "video_path": video_path,
            "updated_at": datetime.now().isoformat()
        }
        self.logger.info(f"Status updated for {request_id}: {status} - {message}")
    
    def get_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """İstek durumunu getir"""
        return self.status_db.get(request_id)
    
    def clear_status(self, request_id: str):
        """İstek durumunu temizle"""
        if request_id in self.status_db:
            del self.status_db[request_id]
    
    def cleanup_old_videos(self, days: int = 7):
        """Eski video dosyalarını temizle"""
        import time
        current_time = time.time()
        
        for video_file in self.final_video_dir.glob("*.mp4"):
            file_age = current_time - video_file.stat().st_mtime
            if file_age > days * 24 * 3600:
                # İlgili dosyaları da sil
                base_name = video_file.stem
                for related_file in self.final_video_dir.glob(f"{base_name}.*"):
                    related_file.unlink()
                    self.logger.info(f"Deleted old file: {related_file}")