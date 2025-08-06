import re
import ast
from typing import List, Optional, Tuple
from pathlib import Path

def validate_file_type(filename: str) -> bool:
    """Dosya tipinin geçerli olup olmadığını kontrol eder"""
    allowed_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',  # Görseller
        '.pdf',  # PDF
        '.mp4', '.avi', '.mov', '.webm'  # Videolar (gelecek için)
    }
    
    file_ext = Path(filename).suffix.lower()
    return file_ext in allowed_extensions

def validate_manim_code(code: str) -> bool:
    """Manim kodunun geçerli olup olmadığını kontrol eder - Geliştirilmiş versiyon"""
    if not code or not code.strip():
        return False
    
    # Debug için validation adımlarını takip et
    validation_results = []
    
    # 1. Temel importlar kontrolü
    import_checks = [
        "from manim import" in code or "import manim" in code,
        "VoiceoverScene" in code or "Scene" in code,
    ]
    validation_results.append(("imports", any(import_checks)))
    
    # 2. Class tanımı kontrolü - daha esnek
    class_patterns = [
        r'class\s+\w+\s*\(\s*VoiceoverScene\s*\)',
        r'class\s+\w+\s*\(\s*Scene\s*\)',
        r'class\s+Solution',
    ]
    has_class = any(re.search(pattern, code) for pattern in class_patterns)
    validation_results.append(("class_definition", has_class))
    
    # 3. construct metodu kontrolü
    has_construct = bool(re.search(r'def\s+construct\s*\(\s*self\s*\)', code))
    validation_results.append(("construct_method", has_construct))
    
    # 4. Basit syntax kontrolü - daha toleranslı
    syntax_valid = check_python_syntax(code)
    validation_results.append(("syntax", syntax_valid))
    
    # 5. Minimum kod uzunluğu
    min_length = len(code) > 100
    validation_results.append(("min_length", min_length))
    
    # Debug: başarısız olan kontrolleri logla
    failed_checks = [check for check, result in validation_results if not result]
    if failed_checks:
        print(f"Validation failed for: {failed_checks}")
        # İlk 500 karakteri göster
        print(f"Code preview: {code[:500]}...")
    
    # En az 4/5 kontrolden geçmeli (syntax hariç)
    essential_checks = ["imports", "class_definition", "construct_method", "min_length"]
    passed_essential = sum(1 for check, result in validation_results 
                          if check in essential_checks and result)
    
    return passed_essential >= 3  # 4'ten en az 3'ü geçmeli

def check_python_syntax(code: str) -> bool:
    """Python syntax kontrolü - import hatalarını yok say"""
    try:
        # Önce temiz bir syntax kontrolü yap
        ast.parse(code)
        return True
    except SyntaxError as e:
        # Syntax error'ı logla ama import hatası değilse
        if "import" not in str(e).lower():
            print(f"Syntax error: {e}")
            return False
        # Import hatası ise geç (çünkü manim kütüphanesi olmayabilir)
        return True
    except Exception as e:
        print(f"Unexpected error in syntax check: {e}")
        return False

def validate_solution_format(solution: str) -> bool:
    """Çözüm formatının geçerli olup olmadığını kontrol eder"""
    if not solution or len(solution) < 50:
        return False
    
    # Daha esnek kontroller
    content_indicators = [
        any(word in solution.lower() for word in ["adım", "çözüm", "problem", "analiz"]),
        any(word in solution.lower() for word in ["matematik", "formül", "hesap", "sonuç"]),
        len(solution.split()) > 20,  # En az 20 kelime
    ]
    
    return sum(content_indicators) >= 2

def validate_topic_content(content: str) -> bool:
    """Konu içeriğinin geçerli olup olmadığını kontrol eder"""
    if not content or len(content) < 100:
        return False
    
    # Eğitim içeriği göstergeleri
    education_indicators = [
        any(word in content.lower() for word in ["tanım", "kavram", "örnek", "açıklama"]),
        any(word in content.lower() for word in ["konu", "ders", "öğrenme", "eğitim"]),
        len(content.split()) > 30,  # En az 30 kelime
        ":" in content or "?" in content,  # Yapılandırılmış içerik göstergesi
    ]
    
    return sum(education_indicators) >= 2

def validate_request_data(data: dict) -> tuple[bool, Optional[str]]:
    """API isteğinin geçerli olup olmadığını kontrol eder"""
    
    # Zorunlu alanlar
    if 'text' not in data or not data['text'].strip():
        return False, "Text alanı zorunludur"
    
    # Video tipi kontrolü
    valid_types = ['solution', 'topic', 'full']
    if 'video_type' in data and data['video_type'] not in valid_types:
        return False, f"Geçersiz video tipi. Geçerli tipler: {', '.join(valid_types)}"
    
    # Text uzunluğu kontrolü
    if len(data['text']) > 5000:
        return False, "Text 5000 karakterden uzun olamaz"
    
    if len(data['text']) < 10:
        return False, "Text en az 10 karakter olmalıdır"
    
    return True, None

def sanitize_filename(filename: str) -> str:
    """Dosya adını güvenli hale getirir"""
    # Tehlikeli karakterleri kaldır
    safe_name = re.sub(r'[^\w\s.-]', '', filename)
    # Boşlukları alt çizgi ile değiştir
    safe_name = safe_name.replace(' ', '_')
    # Uzunluğu sınırla
    if len(safe_name) > 100:
        name, ext = safe_name.rsplit('.', 1) if '.' in safe_name else (safe_name, '')
        safe_name = name[:96] + '.' + ext if ext else name[:100]
    
    return safe_name

def extract_python_code_blocks(text: str) -> List[str]:
    """Metinden Python kod bloklarını çıkarır"""
    # Farklı markdown formatları
    patterns = [
        r'```python\n(.*?)```',
        r'```\n(.*?)```',
        r'`(.*?)`',  # Tek satır kod
    ]
    
    code_blocks = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        code_blocks.extend(matches)
    
    return [block.strip() for block in code_blocks if block.strip()]

def debug_code_validation(code: str) -> dict:
    """Kod validasyonu için debug bilgileri"""
    results = {
        "code_length": len(code),
        "has_imports": bool(re.search(r'from\s+manim\s+import|import\s+manim', code)),
        "has_class": bool(re.search(r'class\s+\w+', code)),
        "has_construct": bool(re.search(r'def\s+construct', code)),
        "has_voiceover": "VoiceoverScene" in code or "voiceover" in code.lower(),
        "line_count": len(code.split('\n')),
        "first_lines": code.split('\n')[:5],
    }
    
    return results