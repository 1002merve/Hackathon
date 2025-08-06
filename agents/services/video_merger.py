import os
import subprocess
from pathlib import Path
from typing import List, Optional
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
import numpy as np

from services.logger import get_logger
from config import settings

class VideoMerger:
    """Video birleştirme ve düzenleme sınıfı"""
    
    def __init__(self):
        self.logger = get_logger("VideoMerger")
        
    def merge_videos(self, 
                    video_paths: List[Path], 
                    output_path: Path,
                    transition_duration: float = 0.5) -> Path:
        """
        Birden fazla videoyu birleştirir
        
        Args:
            video_paths: Birleştirilecek video dosyaları
            output_path: Çıktı dosya yolu
            transition_duration: Geçiş süresi (saniye)
            
        Returns:
            Birleştirilmiş video dosya yolu
        """
        try:
            self.logger.info(f"Merging {len(video_paths)} videos")
            
            clips = []
            for i, video_path in enumerate(video_paths):
                clip = VideoFileClip(str(video_path))
                
                # Geçiş efekti ekle (ilk video hariç)
                if i > 0 and transition_duration > 0:
                    clip = clip.crossfadein(transition_duration)
                
                clips.append(clip)
            
            # Videoları birleştir
            final_clip = concatenate_videoclips(clips, method="compose")
            
            # Çıktıyı kaydet
            final_clip.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                fps=60,
                preset='medium',
                threads=4
            )
            
            # Belleği temizle
            for clip in clips:
                clip.close()
            final_clip.close()
            
            self.logger.info(f"Videos merged successfully: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Video merge error: {str(e)}")
            raise
    
    def add_watermark(self, 
                     video_path: Path,
                     watermark_text: str = "Eğitim Videoları",
                     position: str = "bottom-right") -> Path:
        """Video'ya watermark ekler"""
        try:
            # FFmpeg komutu oluştur
            output_path = video_path.with_name(f"{video_path.stem}_watermarked.mp4")
            
            position_map = {
                "top-left": "x=10:y=10",
                "top-right": "x=W-tw-10:y=10",
                "bottom-left": "x=10:y=H-th-10",
                "bottom-right": "x=W-tw-10:y=H-th-10",
                "center": "x=(W-tw)/2:y=(H-th)/2"
            }
            
            filter_complex = f"drawtext=text='{watermark_text}':fontcolor=white@0.5:fontsize=24:box=1:boxcolor=black@0.2:{position_map.get(position, position_map['bottom-right'])}"
            
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vf', filter_complex,
                '-codec:a', 'copy',
                str(output_path),
                '-y'
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            self.logger.info(f"Watermark added: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Watermark error: {e.stderr.decode()}")
            raise
        except Exception as e:
            self.logger.error(f"Watermark error: {str(e)}")
            raise
    
    def add_intro_outro(self,
                       main_video: Path,
                       intro_video: Optional[Path] = None,
                       outro_video: Optional[Path] = None) -> Path:
        """Ana videoya intro ve outro ekler"""
        videos_to_merge = []
        
        if intro_video and intro_video.exists():
            videos_to_merge.append(intro_video)
        
        videos_to_merge.append(main_video)
        
        if outro_video and outro_video.exists():
            videos_to_merge.append(outro_video)
        
        if len(videos_to_merge) == 1:
            return main_video
        
        output_path = main_video.with_name(f"{main_video.stem}_complete.mp4")
        return self.merge_videos(videos_to_merge, output_path)
    
    def optimize_video(self, video_path: Path, quality: str = "high") -> Path:
        """Video boyutunu optimize eder"""
        try:
            output_path = video_path.with_name(f"{video_path.stem}_optimized.mp4")
            
            quality_settings = {
                "low": {"crf": 28, "preset": "faster"},
                "medium": {"crf": 23, "preset": "medium"},
                "high": {"crf": 18, "preset": "slow"}
            }
            
            settings = quality_settings.get(quality, quality_settings["medium"])
            
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-c:v', 'libx264',
                '-crf', str(settings["crf"]),
                '-preset', settings["preset"],
                '-c:a', 'aac',
                '-b:a', '128k',
                str(output_path),
                '-y'
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Boyut karşılaştırması
            original_size = video_path.stat().st_size
            optimized_size = output_path.stat().st_size
            reduction = (1 - optimized_size/original_size) * 100
            
            self.logger.info(f"Video optimized: {reduction:.1f}% size reduction")
            return output_path
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Optimization error: {e.stderr.decode()}")
            raise
        except Exception as e:
            self.logger.error(f"Optimization error: {str(e)}")
            raise