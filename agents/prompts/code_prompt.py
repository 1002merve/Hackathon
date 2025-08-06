def get_manim_prompt() -> str:
    """Geliştirilmiş ve hatasız Manim kod üretim promptu"""
    return """
  
{content}
  
  
Yukardaki Metni incele
**Video Üretimi**
Sen, Manim kütüphanesini kullanarak verilen metinde sorunun çözümünü adım adım bir video haline getirecek uzman bir geliştiricisin.

Görseli veya metni inceleyerek, içindeki sorunun çözümünü aşağıda verilen adımlara göre Python'un Manim kütüphanesini kullanarak bir video haline getir.

Kodu yazarken planla bir öğretmen olarak öğrenciyi etkileyen, öğretmenlik açısından etkili ve akıcı bir video üret. şekiller açıklamalar hikayeler ve grafikler ile destekle.

### Yapılması Gerekenler:

1. **Görseli Analiz Et:**
   - Görseldeki tüm çizimleri ve grafikleri dikkate al.

2. **Adım Adım Çözüm:**
   - Verilen çözümü adım adım takip et. Her bir adımı net bir şekilde belirt.

3. **Grafikler ve Betimlemeler:**
   - Gerektiğinde grafikler çizerek açıklamaları destekle.
   - Grafiklerin üzerinde anlatım yaparak görselliği artır.

4. **FadeOut Efekti:**
   - Her adımın ardından FadeOut efekti kullanarak, önceki elemanların kaybolmasını sağla. Bu, üst üste gelmeleri önleyecektir.

5. **Sesli Anlatım:**
   - Her adımda Manim Voicer kullanarak çözümü sesli bir şekilde anlat.

6. En az 5 stepten oluşsun.

7. Her işlem en az 3 saniye sürmesi gerekiyor.örnek wait(3)

8. Her işlemi 0.8 Scale ile kullan. elemanları ortala

9. Dışardan hergangi bir görsel vb alma!.

NOTE: Her Stepte with self.voiceover kullanmayı unutma.
NOTE: self.voiceover textleri uzun olsun tüm step i anlatsın. text uzunluğu en az 100 karakterden oluşsun 
NOTE: Textleri renkli renkli yap. bu renkleri kullan RED,GREEN,BLUE,PINK,PURPLE,BLACK . Kesinlikle WHITE kullanma. 
NOTE: Önemli yerlerin altını çiz.
NOTE: Hız ayarını tuttur. şekiller ve yazılar normal hızlarda gelsin ne çok hızlı ne de çok yavaş olsun.

Note: Anlatımlar tamamen türkçe olsun. Sesli anlatım tamamen türkçe olsun.


### Örnek Kod Yapısı:

```python
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService
from manim import *

class Solution(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService())
        step_1()
        step_2()

    def step_1():
        with self.voiceover(text="") as tracker: # text="" için latex ,markdown ve renk kullanman yasak. text="" içinde sadece normal metin olsun.
            self.play((....).scale(0.8))
            self.wait(..)
        self.play(FadeOut(....))
    
    def step_2():
        with self.voiceover(text="") as tracker: # text="" için latex ,markdown ve renk kullanman yasak. text="" içinde sadece normal metin olsun.
            self.play((....).scale(0.8))
            self.wait(..)
        self.play(FadeOut(....))
```

### Örnek Çıktı Yapısı:

- **(Sesli Anlatım)**
  - 1. Adım
  - Başlık
  - **FadeOut**
  
- **(Sesli Anlatım)**
  - Çözüm_1
  - ----
  - Çözüm_1 (yukarı kaydır)
  - Çözüm_2
  - -----
  
- **(Sesli Anlatım)**
  - Çözüm_1 (yukarı kaydır)
  - Çözüm_2 (yukarı kaydır)
  - Çözüm_3 
  - **FadeOut**
  - Grafik_1
  - ------
  
- **(Sesli Anlatım)**
  - Grafik_1 (yukarı kaydır)
  - Çözüm_4
  - **FadeOut**
  
- **(Sesli Anlatım)**
  - 2. Adım
  - Başlık
  - **FadeOut**
  - Çözüm_5
  - ------
  
- **(Sesli Anlatım)**
  - Çözüm_5 (yukarı kaydır)
  - Çözüm_6
  - **FadeOut**
  - Grafik_2
  - ---------
  
- **(Sesli Anlatım)**
  - Grafik_2 (yukarı kaydır)
  - Çözüm_7
  - **FadeOut**



kod yazarken dikkat etmen gereken bazı yaygın hatalar:

* Render error: 'Write' object has no attribute 'scale'
* LaTeX compilation error: Please use \mathaccent for accents in math mode.

Note: Yukardaki hataları yapma.

Note: Oluşturulan Classın ismi "Solution" olacak.
Note: oluşturduğun formüller vb başına self. koymayı unutma
Note: self.voiceover içine yazdığın textleri markdown ve latex kullanman yasak. text içinde sadece normal yazı olsun.

"""