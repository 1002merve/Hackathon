# BinaryGirls: AI Destekli Eğitim Asistanı 🚀

### *Matematiği Sanata Dönüştüren Video Platformu*


![BINARYGIRLS](/docs/avatar.png)

## Tanıtım Videosu

[![BinaryGirls Demo Videosu](/docs/binary.gif)](/docs/video.mp4)

-------

[[BinaryGirls Demo Videosu](/docs/example.gif)]

## 💡 Projenin Doğuş Hikayesi

Biz, **Merve Dinçer**, **Nesibe Dinçer** ve **Meral Hamarat**, teknoloji ve eğitimin gücüne inanan üç kadın girişimciyiz. Ekibimizdeki **Matematik** ve **Bilgisayar Mühendisliği** uzmanlıklarımızı birleştirerek, "Çocukların ve gençlerin matematiğe olan ilgisini nasıl artırabiliriz?" sorusuna bir cevap aradık. Bu sorunun yanıtı olarak, **BTK 2025 Hackathon**'u için **BinaryGirls** platformunu geliştirdik.

Misyonumuz, öğrenmeyi ezberci bir süreçten çıkarıp, her öğrencinin kendi hızında keşfedebileceği, etkileşimli, görsel ve eğlenceli bir maceraya dönüştürmektir. BinaryGirls, sadece bir soru-cevap platformu değil, aynı zamanda her öğrenciye özel bir yapay zeka mentör ve kişiselleştirilmiş bir video ders stüdyosu sunan bütünleşik bir ekosistemdir.

## ✨ Neden BinaryGirls?

Platformumuz, öğrencilere sadece doğru cevabı vermekle kalmaz, aynı zamanda "neden" ve "nasıl" sorularını sorarak kavramsal bir anlayış geliştirmelerine yardımcı olur.

-   **🤖 Kişiselleştirilmiş Öğrenme:** Yapay zeka asistanımız "Maya", her öğrencinin seviyesine ve öğrenme stiline uyum sağlar.
-   **🎥 Anında Video Çözümler:** Yazılı bir soruyu veya bir görseli saniyeler içinde sesli ve animasyonlu bir video derse dönüştürür.
-   **🎨 Etkileşimli ve Eğlenceli:** 3D avatar sistemi ve modern arayüzü ile öğrenme sürecini oyunlaştırır.
-   **🧠 Uzman Bakış Açısı:** Matematiksel doğruluğu ve pedagojik etkinliği bir arada sunarak, öğrencilerin konuları derinlemesine anlamasını sağlar.
-   **💪 Kendi Kendini İyileştiren Sistem:** Video oluşturma sırasında bir sorunla karşılaşırsa, yapay zeka hatayı analiz eder, kodu düzeltir ve tekrar dener.

## 🏗️ Sistem Mimarisi

Proje, servis odaklı bir mimari benimser. Django uygulaması kullanıcı arayüzünü, veri yönetimini ve genel iş akışını yönetirken, FastAPI servisi yoğun işlem gücü gerektiren video oluşturma görevlerini asenkron olarak yürütür. Bu ayrım, sistemin ölçeklenebilir ve dayanıklı olmasını sağlar.

```
+--------------------------+      (API İsteği: Metin/Görsel)      +-----------------------------+
|                          | ----------------------------------> |                             |
|  Django Web Uygulaması   |                                     |  FastAPI Video Servisi      |
| (Kullanıcı Arayüzü, DB)  |                                     |  (Asenkron Video Üretimi)   |
|                          | <---------------------------------- |                             |
+--------------------------+      (Cevap: request_id, durum)     +-----------------------------+
                                                                          |
                                                                          | (Agent'ları ve Servisleri Tetikler)
                                                                          V
                                                         +-------------------------------------+
                                                         |  BinaryGirls Agent Sistemi & Manim  |
                                                         |  (Video Render & Seslendirme)       |
                                                         +-------------------------------------+
```

## 🧠 Akıllı Agent Sistemi Nasıl Çalışıyor?

Video oluşturma sürecimiz, belirli görevler için özelleştirilmiş bir dizi "agent" tarafından yönetilen sofistike bir iş akışıdır. Bu agent'lar, bir soruyu alıp onu tam teşekküllü bir eğitim videosuna dönüştürmek için bir "düşünce zinciri" (chain of thought) oluşturur.

1.  **Girdi Analizi (`SolutionAgent` / `TopicAgent`):**
    -   Kullanıcıdan gelen metin veya görsel, ilk olarak bu agent'lar tarafından işlenir.
    -   Görevleri, ham girdiyi pedagojik olarak anlamlı, adım adım ilerleyen yapılandırılmış bir metne dönüştürmektir. Bu metin, videonun senaryosunu oluşturur.

2.  **Kod Üretimi (`CodeAgent`):**
    -   Yapılandırılmış çözüm metni, `CodeAgent`'a gönderilir.
    -   Bu agent, uzman bir Manim geliştiricisi gibi davranarak, senaryoyu görselleştirecek Python kodunu üretir. Bu kod, animasyonları, formülleri ve seslendirme metinlerini içerir.

3.  **Sahne Yönetimi (`SceneManager`):**
    -   Daha karmaşık videolar için `SceneManager` devreye girer.
    -   Giriş (`intro`), ana içerik, geçişler ve kapanış (`outro`) gibi farklı sahneler için ayrı ayrı kodlar ürettirir ve bunları akıcı bir bütün halinde birleştirir.

4.  **Video Oluşturma ve Kendi Kendini İyileştirme (`VideoCreator`):**
    -   `CodeAgent`'tan gelen nihai Manim kodu, `VideoCreator` servisine iletilir.
    -   Servis, kodu çalıştırarak videoyu render etmeye başlar.
    -   **Eğer bir hata oluşursa:**
        -   Sistem çökmez. Hata mesajı yakalanır.
        -   Hatalı kod ve hata mesajı, `error_prompt` ile birlikte tekrar LLM'e gönderilir.
        -   Yapay zeka, hatayı analiz eder ve düzeltilmiş bir kod önerir.
        -   `VideoCreator`, bu yeni kodla render işlemini **3 defaya kadar** tekrar dener.

Bu çok adımlı ve kendi kendini iyileştiren süreç, hem yüksek kaliteli hem de hatasız videolar üretmemizi sağlar.

```
Kullanıcı Girdisi (Metin/Görsel)
       |
       V
+---------------------+      +-------------------+
|   SolutionAgent     |----->|    TopicAgent     |  (1. Adım: Anlama ve Yapılandırma)
+---------------------+      +-------------------+
       |
       V (Yapılandırılmış Metin)
+---------------------+
|      CodeAgent      |-------------------------> (2. Adım: Manim Kodu Üretimi)
+---------------------+                           |
       | (Manim Kodu)                             |
       V                                          V
+---------------------+      +---------------------------------+
|   SceneManager      |----->|         VideoCreator            | (3. Adım: Sahneleme ve Render)
+---------------------+      +---------------------------------+
                                     |
                                     V (Hata oluşursa?)
                             +-------------------------------+
                             |  Hata Analizi -> Kod Düzeltme | (4. Adım: Kendi Kendini İyileştirme)
                             +-------------------------------+
                                     |
                                     V (Başarılı)
                                Final Video (MP4)
```

## 📁 Proje Yapısı

Proje, birbirinden bağımsız çalışabilen iki ana bölümden oluşur: `binarygirls` (Django) ve `agents` (FastAPI).

```
Hackathon/
├── agents/                     # FastAPI Video Üretim Servisi
│   ├── agents/                 # Akıllı Agent'lar
│   ├── config/                 # Servis konfigürasyonu
│   ├── main.py                 # FastAPI ana uygulama dosyası
│   ├── prompts/                # LLM için kullanılan prompt'lar
│   ├── services/               # Video oluşturma, LLM, logger gibi servisler
│   └── static/                 # Üretilen videoların ve geçici dosyaların tutulduğu yer
├── binarygirls/                # Django Proje Çekirdeği
│   ├── settings.py
│   └── urls.py
├── core/                       # Django Ana Uygulama (Dashboard, Chat, Çözümler)
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── member/                     # Django Üyelik Sistemi Uygulaması
│   ├── models.py
│   ├── forms.py
│   └── views.py
├── static/                     # Django'nun statik dosyaları (CSS, JS, 3D Modeller)
├── templates/                  # Django şablonları
├── docker-compose.yml          # Docker ile kolay kurulum için
├── Dockerfile                  # Django uygulaması için Docker imajı
└── manage.py                   # Django yönetim betiği
```

## 🛠️ Teknoloji Yığını

-   **Backend:** Python, Django, FastAPI, Uvicorn
-   **Frontend:** HTML, Tailwind CSS, JavaScript, **Three.js** (3D Avatar için)
-   **Yapay Zeka:** Google Gemini, OpenAI (opsiyonel)
-   **Video & Animasyon:** **Manim Community Edition**, FFmpeg
-   **Veritabanı:** SQLite (geliştirme), PostgreSQL (production için önerilir)
-   **Containerization:** Docker, Docker Compose

## 🚀 Kurulum ve Çalıştırma

Projeyi yerel makinenizde çalıştırmak için iki seçeneğiniz vardır: Docker (önerilen) veya manuel kurulum.

### Gereksinimler
-   Docker ve Docker Compose
-   Python 3.9+
-   Git

### 🐳 Seçenek 1: Docker ile Hızlı Kurulum (Önerilen)

Bu yöntem, tüm bağımlılıkları ve servisleri izole bir ortamda çalıştırarak en kolay kurulumu sağlar.

1.  **Projeyi Klonlayın:**
    ```bash
    git clone https://github.com/kullanici/Hackathon.git
    cd Hackathon
    ```

2.  **Ortam Değişkenlerini Ayarlayın:**
    -   Ana dizinde (`Hackathon/`) `.env` adında bir dosya oluşturun:
        ```env
        # Hackathon/.env
        SECRET_KEY=django-insecure-m#v@6t69^^^bbi9fyf&qm03)nt19#2#t&_xpjs)fjuphin6z7m
        DEBUG=True
        GEMINI_API_KEY=YOUR_GOOGLE_GEMINI_API_KEY
        VIDEO_API_BASE_URL=http://agents:8001
        ```
    -   `agents/` dizini içinde `.env` adında bir dosya daha oluşturun:
        ```env
        # Hackathon/agents/.env
        GEMINI_API_KEY=YOUR_GOOGLE_GEMINI_API_KEY
        LLM_PROVIDER=gemini
        ```

3.  **Docker Compose'u Çalıştırın:**
    ```bash
    docker-compose up --build
    ```
    Bu komut, hem Django web sunucusunu hem de FastAPI video servisini başlatacaktır.

4.  **Uygulamaya Erişin:**
    -   **BinaryGirls Web Arayüzü:** `http://localhost:8000`
    -   **FastAPI Servisi (API dokümantasyonu):** `http://localhost:8001/docs`

### 🔧 Seçenek 2: Manuel Kurulum (Sanal Ortam ile)

Her servisi kendi terminalinde ayrı ayrı çalıştırın.

#### 1. FastAPI Video Servisi'ni Başlatma

```bash
# Yeni bir terminal açın
cd Hackathon/agents

# Sanal ortam oluşturun ve aktifleştirin
python -m venv venv
source venv/bin/activate  # Mac/Linux için
# venv\Scripts\activate  # Windows için

# Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt

# Ortam değişkenlerini ayarlayın (`agents/.env` dosyası)
echo "GEMINI_API_KEY=YOUR_GEMINI_API_KEY" > .env

# FastAPI sunucusunu başlatın
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

#### 2. Django Web Uygulamasını Başlatma

```bash
# Yeni bir terminal daha açın
cd Hackathon

# Sanal ortam oluşturun ve aktifleştirin
python -m venv venv
source venv/bin/activate  # Mac/Linux için
# venv\Scripts\activate  # Windows için

# Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt

# Ortam değişkenlerini ayarlayın (Ana dizindeki .env dosyası)
echo "GEMINI_API_KEY=YOUR_GEMINI_API_KEY" >> .env
echo "VIDEO_API_BASE_URL=http://localhost:8001" >> .env

# Veritabanı migrate işlemlerini yapın
python manage.py migrate

# Süper kullanıcı oluşturun (isteğe bağlı)
python manage.py createsuperuser

# Django sunucusunu başlatın
python manage.py runserver
```
Uygulamaya `http://localhost:8000` adresinden erişebilirsiniz.

## 🌟 Ekibimiz

Bu proje, farklı yeteneklerini ortak bir vizyon için birleştiren üç kadının tutkusu ve emeğiyle ortaya çıktı:

| İsim            | Rol                               |
| --------------- | --------------------------------- |
| **Merve Dinçer**  | Proje Lideri & Matematik Uzmanı & AI Mühendisi   |
| **Nesibe Dinçer** | Frontend Geliştirici & UI/UX Tasarımcısı |
| **Meral Hamarat** | Bilgisayar Mühendisi & AI Mühendisi   |


## 🔮 Gelecek Vizyonumuz

BinaryGirls, sürekli gelişen bir platformdur. Gelecek için hedeflerimiz:

-   [ ] **Daha Fazla Ders:** Kimya, Biyoloji ve Fizik gibi diğer fen bilimleri için de destek eklemek.
-   [ ] **Farklı Animasyon Stilleri:** Kullanıcıların "beyaz tahta", "modern UI" gibi farklı video stilleri seçebilmesi.
-   [ ] **Oyunlaştırma:** Başarı rozetleri, puanlama sistemi ve liderlik tablosu ile öğrenmeyi daha eğlenceli hale getirmek.
-   [ ] **Gerçek Zamanlı İşbirliği:** Öğrencilerin arkadaşlarıyla birlikte problem çözebileceği ortamlar oluşturmak.
-   [ ] **Mobil Uygulama:** Platformun tüm özelliklerini mobil cihazlara taşımak.

En iyi proje

## 🙏 Teşekkür

Bu projeyi hayata geçirmemize olanak sağlayan **BTK (Bilgi Teknolojileri ve İletişim Kurumu)**'na ve **2025 Hackathon** organizasyon ekibine sonsuz teşekkürler. 
