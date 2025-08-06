from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import shutil
import os
import uuid
from pathlib import Path
import mimetypes

from config import settings
from services.create_video import VideoCreator
from services.logger import get_logger
from utils.file_handler import FileHandler
from utils.validators import validate_file_type

app = FastAPI(title="Eğitim Video Oluşturucu", version="2.2")
logger = get_logger("API")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static dosyaları servis et
app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")

# Final videos dizinini ayrıca servis et - video erişimi için
final_videos_dir = settings.static_dir / "final_videos"
final_videos_dir.mkdir(exist_ok=True)
app.mount("/videos", StaticFiles(directory=str(final_videos_dir)), name="videos")

# Global değişkenler
file_handler = FileHandler()
video_creator = VideoCreator()

@app.post("/api/create_video")
async def create_video(
    background_tasks: BackgroundTasks,
    text: str = Form(...),
    video_type: str = Form("solution"),  # solution, topic, full
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Video oluşturma endpoint'i
    
    Args:
        text: Soru veya konu metni
        video_type: Video tipi (solution, topic, full)
        files: Yüklenen dosyalar (görsel, PDF)
    """
    request_id = str(uuid.uuid4())
    logger.info(f"New video request: {request_id}, type: {video_type}")
    
    try:
        # Dosyaları işle
        processed_files = []
        if files:
            for file in files:
                if not validate_file_type(file.filename):
                    raise HTTPException(400, f"Desteklenmeyen dosya tipi: {file.filename}")
                
                file_path = await file_handler.save_upload(file, request_id)
                file_data = await file_handler.process_file(file_path)
                processed_files.append(file_data)
        
        # Video oluşturmayı arka planda başlat
        background_tasks.add_task(
            video_creator.create_video,
            request_id,
            text,
            video_type,
            processed_files
        )
        
        return JSONResponse({
            "request_id": request_id,
            "status": "processing",
            "message": "Video oluşturma işlemi başlatıldı",
            "check_status_url": f"/api/status/{request_id}",
            "video_url": f"/api/video/{request_id}",
            "direct_video_url": f"/videos/{request_id}.mp4"
        })
        
    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        raise HTTPException(500, f"Video oluşturma hatası: {str(e)}")

@app.get("/api/status/{request_id}")
async def check_status(request_id: str):
    """Video oluşturma durumunu kontrol et"""
    status = video_creator.get_status(request_id)
    
    if not status:
        raise HTTPException(404, "İstek bulunamadı")
    
    # Video hazırsa URL'leri ekle
    if status["status"] == "completed":
        status["video_urls"] = {
            "api": f"/api/video/{request_id}",
            "direct": f"/videos/{request_id}.mp4",
            "static": f"/static/final_videos/{request_id}.mp4"
        }
    
    return JSONResponse(status)

@app.get("/api/video/{request_id}")
async def get_video(request_id: str):
    """Oluşturulan videoyu indir - Geliştirilmiş erişim"""
    
    # Önce final_videos dizininde ara
    final_video_path = final_videos_dir / f"{request_id}.mp4"
    
    if final_video_path.exists():
        video_path = final_video_path
        logger.info(f"Video found in final_videos: {video_path}")
    else:
        # Eski konumda ara (backward compatibility)
        video_path = settings.video_output_dir / f"{request_id}.mp4"
        if video_path.exists():
            logger.info(f"Video found in old location: {video_path}")
        else:
            # Son çare: tüm dizinlerde ara
            import glob
            search_patterns = [
                str(settings.video_output_dir / "**" / f"{request_id}.mp4"),
                str(settings.static_dir / "**" / f"{request_id}.mp4")
            ]
            
            found_files = []
            for pattern in search_patterns:
                found_files.extend(glob.glob(pattern, recursive=True))
            
            if found_files:
                video_path = Path(found_files[0])
                logger.info(f"Video found via search: {video_path}")
            else:
                logger.error(f"Video not found for request_id: {request_id}")
                raise HTTPException(404, f"Video bulunamadı: {request_id}")
    
    # Dosya varlığını tekrar kontrol et
    if not video_path.exists():
        raise HTTPException(404, f"Video dosyası bulunamadı: {video_path}")
    
    # MIME type'ı belirle
    media_type = mimetypes.guess_type(str(video_path))[0] or "video/mp4"
    
    try:
        return FileResponse(
            path=str(video_path),
            media_type=media_type,
            filename=f"egitim_video_{request_id}.mp4",
            headers={
                "Content-Length": str(video_path.stat().st_size),
                "Accept-Ranges": "bytes"
            }
        )
    except Exception as e:
        logger.error(f"Error serving video {request_id}: {str(e)}")
        raise HTTPException(500, f"Video servis hatası: {str(e)}")

@app.get("/api/stream/{request_id}")
async def stream_video(request_id: str):
    """Video streaming endpoint'i - büyük dosyalar için"""
    
    # Video dosyasını bul
    final_video_path = final_videos_dir / f"{request_id}.mp4"
    
    if not final_video_path.exists():
        # Eski konumda ara
        video_path = settings.video_output_dir / f"{request_id}.mp4"
        if not video_path.exists():
            raise HTTPException(404, "Video bulunamadı")
        final_video_path = video_path
    
    def generate():
        with open(final_video_path, "rb") as video_file:
            while True:
                chunk = video_file.read(8192)  # 8KB chunks
                if not chunk:
                    break
                yield chunk
    
    return StreamingResponse(
        generate(),
        media_type="video/mp4",
        headers={
            "Content-Length": str(final_video_path.stat().st_size),
            "Accept-Ranges": "bytes"
        }
    )

@app.get("/api/videos")
async def list_videos():
    """Oluşturulan videoları listele - Geliştirilmiş"""
    videos = []
    
    # Final videos dizinindeki videoları listele
    if final_videos_dir.exists():
        for video_file in final_videos_dir.glob("*.mp4"):
            try:
                stat = video_file.stat()
                videos.append({
                    "id": video_file.stem,
                    "filename": video_file.name,
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / 1024 / 1024, 2),
                    "created": stat.st_ctime,
                    "modified": stat.st_mtime,
                    "urls": {
                        "api": f"/api/video/{video_file.stem}",
                        "direct": f"/videos/{video_file.stem}.mp4",
                        "stream": f"/api/stream/{video_file.stem}",
                        "static": f"/static/final_videos/{video_file.stem}.mp4"
                    },
                    "location": "final",
                    "has_audio": await _check_video_has_audio(video_file),
                    "related_files": _get_related_files(video_file)
                })
            except Exception as e:
                logger.warning(f"Error processing video {video_file}: {e}")
    
    # Eski konumdaki videoları da listele (backward compatibility)
    for video_file in settings.video_output_dir.glob("*.mp4"):
        # Final videos'da yoksa ekle
        if not any(v["id"] == video_file.stem for v in videos):
            try:
                stat = video_file.stat()
                videos.append({
                    "id": video_file.stem,
                    "filename": video_file.name,
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / 1024 / 1024, 2),
                    "created": stat.st_ctime,
                    "modified": stat.st_mtime,
                    "urls": {
                        "api": f"/api/video/{video_file.stem}",
                        "stream": f"/api/stream/{video_file.stem}"
                    },
                    "location": "old",
                    "has_audio": await _check_video_has_audio(video_file),
                    "related_files": _get_related_files(video_file)
                })
            except Exception as e:
                logger.warning(f"Error processing old video {video_file}: {e}")
    
    # Oluşturma tarihine göre sırala (en yeni önce)
    videos.sort(key=lambda x: x["created"], reverse=True)
    
    return JSONResponse({
        "videos": videos,
        "count": len(videos),
        "total_size_mb": round(sum(v["size"] for v in videos) / 1024 / 1024, 2)
    })

async def _check_video_has_audio(video_path: Path) -> bool:
    """Video'da ses olup olmadığını kontrol et"""
    try:
        import subprocess
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-select_streams', 'a:0', 
            '-show_entries', 'stream=codec_name', '-of', 'csv=p=0', 
            str(video_path)
        ], capture_output=True, text=True, timeout=10)
        
        return result.returncode == 0 and result.stdout.strip()
    except Exception:
        return False

def _get_related_files(video_path: Path) -> List[str]:
    """Video ile ilgili dosyaları bul"""
    related = []
    base_name = video_path.stem
    parent_dir = video_path.parent
    
    for ext in ['.srt', '.wav', '.mp3', '.txt', '.json']:
        related_file = parent_dir / f"{base_name}{ext}"
        if related_file.exists():
            related.append(ext[1:])  # Nokta olmadan uzantı
    
    return related

@app.delete("/api/video/{request_id}")
async def delete_video(request_id: str):
    """Videoyu sil"""
    deleted_files = []
    
    try:
        # Final videos dizininden sil
        for ext in [".mp4", ".srt", ".wav", ".mp3", ".txt", ".json"]:
            file_path = final_videos_dir / f"{request_id}{ext}"
            if file_path.exists():
                file_path.unlink()
                deleted_files.append(str(file_path))
        
        # Eski konumdan da sil (eğer varsa)
        old_video_path = settings.video_output_dir / f"{request_id}.mp4"
        if old_video_path.exists():
            old_video_path.unlink()
            deleted_files.append(str(old_video_path))
        
        if not deleted_files:
            raise HTTPException(404, "Video bulunamadı")
        
        # Status'u temizle
        video_creator.clear_status(request_id)
        
        return JSONResponse({
            "message": "Video başarıyla silindi",
            "deleted_files": deleted_files,
            "count": len(deleted_files)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting video: {str(e)}")
        raise HTTPException(500, f"Video silme hatası: {str(e)}")

@app.post("/api/cleanup")
async def cleanup_old_videos(days: int = 7):
    """Eski video dosyalarını temizle"""
    try:
        # Cleanup öncesi istatistikler
        old_count = len(list(final_videos_dir.glob("*.mp4"))) if final_videos_dir.exists() else 0
        
        video_creator.cleanup_old_videos(days)
        
        # Cleanup sonrası istatistikler
        new_count = len(list(final_videos_dir.glob("*.mp4"))) if final_videos_dir.exists() else 0
        cleaned_count = old_count - new_count
        
        return JSONResponse({
            "message": f"{days} günden eski videolar temizlendi",
            "cleaned_count": cleaned_count,
            "remaining_count": new_count
        })
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        raise HTTPException(500, f"Temizlik hatası: {str(e)}")

@app.get("/api/system/status")
async def system_status():
    """Sistem durumu"""
    try:
        old_videos_dir = settings.video_output_dir
        
        final_count = len(list(final_videos_dir.glob("*.mp4"))) if final_videos_dir.exists() else 0
        old_count = len(list(old_videos_dir.glob("*.mp4"))) if old_videos_dir.exists() else 0
        temp_count = len(list(settings.temp_dir.glob("*.py"))) if settings.temp_dir.exists() else 0
        
        # Disk kullanımı
        total_size = 0
        if final_videos_dir.exists():
            for f in final_videos_dir.rglob("*"):
                if f.is_file():
                    total_size += f.stat().st_size
        
        return JSONResponse({
            "status": "healthy",
            "video_counts": {
                "final_videos": final_count,
                "old_videos": old_count, 
                "temp_files": temp_count,
                "total_videos": final_count + old_count
            },
            "storage": {
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "total_size_gb": round(total_size / 1024 / 1024 / 1024, 2)
            },
            "directories": {
                "final_videos": str(final_videos_dir),
                "video_output": str(old_videos_dir),
                "temp": str(settings.temp_dir)
            },
            "endpoints": {
                "health": "/api/system/status",
                "videos": "/api/videos",
                "create": "/api/create_video",
                "cleanup": "/api/cleanup"
            }
        })
    except Exception as e:
        logger.error(f"System status error: {str(e)}")
        raise HTTPException(500, f"Sistem durumu alınamadı: {str(e)}")

@app.get("/api/video/{request_id}/info")
async def get_video_info(request_id: str):
    """Video detay bilgilerini al"""
    try:
        # Video dosyasını bul
        final_video_path = final_videos_dir / f"{request_id}.mp4"
        
        if not final_video_path.exists():
            video_path = settings.video_output_dir / f"{request_id}.mp4"
            if not video_path.exists():
                raise HTTPException(404, "Video bulunamadı")
            final_video_path = video_path
        
        # Video bilgilerini al
        stat = final_video_path.stat()
        
        # FFprobe ile video metadata'sını al
        import subprocess
        import json
        
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(final_video_path)
            ], capture_output=True, text=True, timeout=10)
            
            metadata = json.loads(result.stdout) if result.returncode == 0 else {}
        except Exception:
            metadata = {}
        
        return JSONResponse({
            "id": request_id,
            "filename": final_video_path.name,
            "path": str(final_video_path),
            "size": {
                "bytes": stat.st_size,
                "mb": round(stat.st_size / 1024 / 1024, 2),
                "human": f"{stat.st_size / 1024 / 1024:.1f} MB"
            },
            "timestamps": {
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime
            },
            "urls": {
                "download": f"/api/video/{request_id}",
                "stream": f"/api/stream/{request_id}",
                "direct": f"/videos/{request_id}.mp4"
            },
            "related_files": _get_related_files(final_video_path),
            "has_audio": await _check_video_has_audio(final_video_path),
            "metadata": metadata
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        raise HTTPException(500, f"Video bilgisi alınamadı: {str(e)}")

@app.get("/")
async def root():
    """API bilgileri"""
    return {
        "title": "Eğitim Video Oluşturucu API",
        "version": "2.2",
        "description": "Matematik problemleri için sesli eğitim videoları oluşturur",
        "endpoints": {
            "create_video": "/api/create_video",
            "check_status": "/api/status/{request_id}",
            "get_video": "/api/video/{request_id}",
            "stream_video": "/api/stream/{request_id}",
            "video_info": "/api/video/{request_id}/info",
            "list_videos": "/api/videos",
            "delete_video": "/api/video/{request_id}",
            "cleanup": "/api/cleanup",
            "system_status": "/api/system/status"
        },
        "features": [
            "✅ Sesli video oluşturma (TTS ile)",
            "✅ Matematik problemleri çözümü",
            "✅ Görsel ve PDF desteği",
            "✅ Otomatik hata düzeltme",
            "✅ Video streaming desteği",
            "✅ İlgili dosyaların yönetimi",
            "✅ Sistem durumu izleme"
        ],
        "improvements": [
            "🔊 Ses sorunu düzeltildi",
            "🎥 Video erişim sorunları çözüldü",
            "📁 Güvenli dosya yönetimi",
            "🔄 Gelişmiş retry mekanizması",
            "📊 Detaylı video bilgileri",
            "🎯 Multiple erişim URL'leri"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.host, 
        port=settings.port,
        reload=settings.debug
    )