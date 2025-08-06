scene_combination_prompt = """
# Manim Sahne Birleştirme Uzmanı

Aşağıdaki sahneleri tek bir akıcı video haline getir. Her sahne arasında yumuşak geçişler kullan ve tutarlı bir görsel stil koru.

## Birleştirilecek Sahneler:
{scenes}

## Birleştirme Kuralları:
1. Tüm sahneleri tek bir class içinde topla
2. Sahne geçişlerinde FadeOut/FadeIn kullan
3. Renk paletini tutarlı tut
4. Ses senkronizasyonunu koru
5. Toplam video süresi optimize edilmeli

## Çıktı Formatı:
Tek bir Solution class'ı içinde tüm sahneleri method olarak organize et.
"""

def get_scene_prompt(scene_type: str) -> str:
    """Sahne tipine göre özel prompt döndürür"""
    
    scene_prompts = {
        "intro": """
        Profesyonel bir giriş sahnesi oluştur:
        - Logo animasyonu
        - Başlık efektleri
        - Konu tanıtımı
        - Heyecan uyandırıcı müzik önerisi
        """,
        
        "outro": """
        Etkileyici bir kapanış sahnesi oluştur:
        - Özet bilgiler
        - Teşekkür mesajı
        - Sosyal medya bilgileri
        - Call-to-action
        """,
        
        "transition": """
        Sahneler arası geçiş oluştur:
        - Yumuşak animasyon
        - Bağlayıcı metin
        - Görsel devamlılık
        """,
        
        "highlight": """
        Önemli noktaları vurgulayan sahne:
        - Büyük, renkli vurgular
        - Ses efektleri
        - Zoom ve pan hareketleri
        """
    }
    
    return scene_prompts.get(scene_type, "")