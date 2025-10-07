# 🎥 Video2Text Article Generator (AI Blog Creator)

AI destekli bu Django projesi, bir **YouTube videosunun linkini** alarak:
1. Videonun sesini indirir 🎧  
2. AssemblyAI ile sesi yazıya çevirir ✍️  
3. Ollama (yerel LLM modeli) ile transkriptten **tam teşekküllü bir blog yazısı üretir** 🧠  
4. Kullanıcı hesabına kaydeder, arayüzden görüntülemeyi sağlar 💾

---

## 🚀 Özellikler

- 🔑 Kullanıcı girişi / kayıt sistemi (Django Auth)
- 📺 YouTube video sesini `yt-dlp` ile indirme
- 🎙️ Otomatik ses → metin dönüştürme (AssemblyAI API)
- 🧠 AI tabanlı blog oluşturma (yerel Ollama modeli – örn. `llama3.1`)
- 💾 Blog yazılarını veritabanına kaydetme
- 📋 Kişisel blog listesi ve detay sayfaları
- 🎨 TailwindCSS ile modern UI tasarımı

---

## 🧩 Teknolojiler

| Katman | Teknoloji |
|:--|:--|
| Backend | Django 5.2 |
| Database | SQLite (varsayılan) |
| AI Text Gen | Ollama (llama3.1) |
| Speech-to-Text | AssemblyAI API |
| Video Download | yt-dlp / pytubefix |
| Frontend | HTML + TailwindCSS |
| Auth | Django built-in Authentication |

---

## 🗂️ Proje Yapısı

berkustuner-video2text_article_generator/
├── manage.py
├── ai_blog_app/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── blog_generator/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
│       ├── 0001_initial.py
│       └── __init__.py
├── templates/
│   ├── all-blogs.html
│   ├── blog-details.html
│   ├── index.html
│   ├── login.html
│   └── signup.html
└── ai-blog/
    ├── pyvenv.cfg
    ├── Scripts/
    │   ├── activate
    │   ├── activate.bat
    │   ├── Activate.ps1
    │   └── deactivate.bat
    └── share/
        ├── bash-completion/
        │   └── completions/
        │       └── yt-dlp
        ├── fish/
        │   └── vendor_completions.d/
        │       └── yt-dlp.fish
        └── zsh/
            └── site-functions/
                └── _yt-dlp


---

## ⚙️ Kurulum

1. Projeyi klonla  
   git clone https://github.com/<kullanıcı_adın>/berkustuner-video2text_article_generator.git  
   cd berkustuner-video2text_article_generator  

2. Sanal ortam oluştur  
   python -m venv venv  
   source venv/bin/activate  (Windows: venv\Scripts\activate)  

3. Bağımlılıkları yükle  
   pip install -r requirements.txt  

   Eğer requirements.txt henüz oluşturmadıysan, içine şunları yaz:  
   Django>=5.2  
   yt-dlp  
   pytubefix  
   assemblyai  
   ollama  
   python-dotenv  
   dj-database-url  

4. Ortam değişkenleri ayarla  
   Proje kök dizinine `.env` dosyası oluştur:  

   DATABASE_URL=sqlite:///db.sqlite3  
   ASSEMBLYAI_API_KEY=<your_assemblyai_api_key>  

5. Veritabanı migrate et  
   python manage.py migrate  

6. Sunucuyu başlat  
   python manage.py runserver  

7. Kullanıcı oluştur  
   http://127.0.0.1:8000/signup adresine git ve hesap oluştur.

---

## 🧠 Nasıl Çalışır?

1. Kullanıcı YouTube linkini girer.  
2. Sistem yt-dlp ile sesi indirir ve mp3’e dönüştürür.  
3. AssemblyAI API sesi metne çevirir.  
4. Ollama (örneğin llama3.1) modeli bu transkriptten özgün bir blog yazısı üretir.  
5. Yazı veritabanına kaydedilir ve kullanıcıya gösterilir.  

---

## 🖥️ Ekran Görüntüleri

| Sayfa | Açıklama |
|:--|:--|
| 🏠 index.html | Ana sayfa, YouTube linkinden blog oluşturma |
| 📚 all-blogs.html | Kullanıcının tüm bloglarını listeler |
| 📝 blog-details.html | Blog detaylarını gösterir |
| 🔐 login.html / signup.html | Kullanıcı kimlik doğrulama sayfaları |

---

## 🧩 Akış Şeması

YouTube Link  
↓  
yt-dlp: Audio Download  
↓  
ffmpeg: Convert to MP3  
↓  
AssemblyAI: Speech-to-Text  
↓  
Ollama: Generate Blog Text  
↓  
Django ORM: Save BlogPost  
↓  
Frontend: Display Result

---

## 💡 Geliştirici Notları

- FFMPEG_BINARY yolu `settings.py` içinde tanımlı. Windows kullanıyorsan kendi yolunu güncelle.  
- Ollama modelini (`llama3.1`) indirmen gerekebilir:  
  ollama pull llama3.1  
- AssemblyAI API anahtarını `.env` içine koymayı unutma.  
- Blog’lar kullanıcıya özel olarak saklanır (her kullanıcı kendi yazılarını görür).

---

## 👤 Yazar

**Berk Üstüner**  
GitHub: https://github.com/berkustuner  

---

## 🪪 Lisans

Bu proje MIT lisansı altındadır.  
Kodu özgürce kullanabilir, değiştirebilir ve paylaşabilirsin.
