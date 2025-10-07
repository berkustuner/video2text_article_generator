from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from .models import BlogPost

import json
import os
import traceback
import requests


def _resolve_ffmpeg_path():
    """
    ffmpeg'in tam yolunu bulur.
    Öncelik: settings.FFMPEG_BINARY -> ENV FFMPEG_BINARY -> yaygın Windows yolları -> 'ffmpeg'
    """
    p = getattr(settings, "FFMPEG_BINARY", None)
    if p and os.path.exists(p):
        return p

    p = os.getenv("FFMPEG_BINARY")
    if p and os.path.exists(p):
        return p

    common_windows = [
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\tools\ffmpeg\bin\ffmpeg.exe",
    ]
    for cand in common_windows:
        if os.path.exists(cand):
            return cand

    return "ffmpeg"  # PATH'te ise çalışır






# ---- YouTube (pytube yerine gerekirse pytubefix) ----
try:
    from pytubefix import YouTube   # daha dayanıklı fork
except Exception:
    from pytube import YouTube      # mevcut kurulum varsa buraya düşer

# yt-dlp ile indirme
import yt_dlp as ytdl

import assemblyai as aai



@login_required
def index(request):
    return render(request, 'index.html')

@login_required
@csrf_exempt
def generate_blog(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    # JSON body
    try:
        body = request.body.decode('utf-8') if isinstance(request.body, (bytes, bytearray)) else request.body
        data = json.loads(body)
        yt_link = data['link'].strip()
        if not yt_link:
            return JsonResponse({'error': 'Missing "link"'}, status=400)
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid data sent'}, status=400)

    # get yt title (oEmbed -> pytube fallback)
    try:
        title = yt_title(yt_link)
        if not title:
            return JsonResponse({'error': 'Failed to fetch title'}, status=502)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': f'Failed to fetch title: {str(e)}'}, status=502)

    # get transcript
    try:
        transcription = get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error': 'Failed to get transcript'}, status=500)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': f'Transcription failed: {str(e)}'}, status=502)

   # blog content
    try:
        blog_content = generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error': 'Failed to generate blog article'}, status=500)
    except Exception as e:
        msg = str(e)
        status_code = 429 if "429" in msg or "quota" in msg.lower() else 502
        return JsonResponse({'error': msg}, status=status_code)


    # save blog article to database
    new_blog_article = BlogPost.objects.create(
        user=request.user,
        youtube_title=title,
        youtube_link=yt_link,
        generated_content=blog_content,
    )

    new_blog_article.save()

    return JsonResponse({'title': title, 'content': blog_content}, status=200)



def yt_title(link):
    """
    Başlık: önce YouTube oEmbed (stabil), olmazsa pytube/pytubefix.
    """
    try:
        r = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": link, "format": "json"},
            timeout=10
        )
        r.raise_for_status()
        t = (r.json().get("title") or "").strip()
        if t:
            return t
    except Exception:
        pass

    yt = YouTube(link)
    return yt.title


def download_audio(link):
    """
    YouTube sesini yt-dlp ile indirir (postprocessor KAPALI).
    İndirilen kaynak (.webm/.m4a/opus) ffmpeg ile **elle** MP3'e çevrilir.
    Geriye MP3 tam yolunu döndürür.
    """
    import yt_dlp as ytdl
    import subprocess

    media_root = getattr(settings, "MEDIA_ROOT", None)
    if not media_root:
        raise RuntimeError("settings.MEDIA_ROOT is not set")
    os.makedirs(media_root, exist_ok=True)

    ffmpeg_bin = _resolve_ffmpeg_path()

    # Benzersiz ve öngörülebilir isim: audio-<id>.<ext>
    outtmpl = os.path.join(media_root, "audio-%(id)s.%(ext)s")

    # **DİKKAT**: postprocessors yok! Sadece indiriyoruz.
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "noprogress": True,
        "prefer_ffmpeg": True,        # indirici içindeki mux vb. için tercih
        # "ffmpeg_location" belirtmiyoruz çünkü postproc yok; manuel ffmpeg kullanacağız
    }

    with ytdl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)

    vid = info.get("id")
    if not vid:
        raise RuntimeError("Could not resolve video id from yt-dlp info")

    # Kaynak ses dosyasını bul
    src_ext_candidates = []
    if info.get("ext"):
        src_ext_candidates.append(info["ext"])
    src_ext_candidates += ["webm", "m4a", "opus", "mp4"]

    src_path = None
    for ext in src_ext_candidates:
        cand = os.path.join(media_root, f"audio-{vid}.{ext}")
        if os.path.exists(cand):
            src_path = cand
            break

    if not src_path:
        # id ile başlayan en yeni dosyayı bul
        candidates = [p for p in os.listdir(media_root) if p.startswith(f"audio-{vid}.")]
        if candidates:
            candidates = [os.path.join(media_root, p) for p in candidates]
            src_path = max(candidates, key=os.path.getmtime)

    if not src_path or not os.path.exists(src_path):
        raise RuntimeError("Download succeeded but no source audio file was found.")

    mp3_path = os.path.join(media_root, f"audio-{vid}.mp3")

    # ffmpeg ile **manuel** dönüşüm
    cmd = [ffmpeg_bin, "-y", "-i", src_path, "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", mp3_path]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode(errors="ignore") if e.stderr else str(e)
        raise RuntimeError(f"ffmpeg conversion failed: {err}") from e
    finally:
        # mp3 üretildiyse kaynağı silebiliriz
        try:
            if os.path.exists(mp3_path) and os.path.exists(src_path):
                os.remove(src_path)
        except OSError:
            pass

    if not os.path.exists(mp3_path):
        raise RuntimeError("MP3 conversion failed; output file missing")

    return mp3_path





def get_transcription(link):
    """
    AssemblyAI ile local mp3 dosyasını transcribe eder ve metni döndürür.
    API key sabit kaldı (istediğin gibi).
    """
    aai.settings.api_key = "b49dc62429374fcb9dc338900c6c1d13"

    audio_file = download_audio(link)
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)

    status = getattr(transcript, "status", None)
    if status and status != "completed":
        err = getattr(transcript, "error", None)
        raise RuntimeError(f"Transcription status={status}, error={err}")

    return transcript.text


def generate_blog_from_transcription(transcription):
    """
    OpenAI yerine yerel Ollama ile blog üretir.
    (Ücretsiz – yerel model çalışır.)
    """
    import ollama

    system_msg = (
        "You are a helpful writing assistant. "
        "Write a polished blog article based on a transcript. "
        "Make it read like a proper blog post (not a video script), "
        "with a clear intro, logical sections, and a concise conclusion. "
        "Do NOT mention that it was based on a transcript."
    )
    user_msg = (
        "Based on the following transcript from a YouTube video, write a comprehensive blog article. "
        "Structure with headings where appropriate.\n\n"
        f"{transcription}"
    )

    # Ollama "chat" benzeri akış:
    res = ollama.chat(
        model="llama3.1",  # indirdiğin modele göre değiştirilebilir
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        options={
            "temperature": 0.7,
            "num_predict": 1200,  # yaklaşık çıktı uzunluğu
        },
    )
    content = res.get("message", {}).get("content", "").strip()
    if not content:
        raise RuntimeError("Local model returned empty content.")
    return content



def blog_list(request):
    blog_articles = BlogPost.objects.filter(user=request.user)
    return render(request, "all-blogs.html", {'blog_articles': blog_articles})


def blog_details(request, pk):
    blog_article_detail = BlogPost.objects.get(id=pk)
    if request.user == blog_article_detail.user:
        return render(request, 'blog-details.html', {'blog_article_detail': blog_article_detail})
    else: 
        return redirect('/')


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = "Invalid username or password!"
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')


def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']

    # (Orijinal akışını koruyorum)
        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except Exception:
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message': error_message})
        else:
            error_message = 'Passwords do not match'
            return render(request, 'signup.html', {'error_message': error_message})

    return render(request, 'signup.html')


def user_logout(request):
    logout(request)
    return redirect('/')
