import os, json, re, asyncio, requests, wave, struct
import numpy as np
import google.generativeai as genai
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, 
    CompositeAudioClip, concatenate_videoclips, ImageClip, ColorClip
)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "").strip())
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY", "").strip()

# 1. Naskah Viral US + Keyword Video Sinematik
data = {
    "keywords": ["storm", "night city", "ocean waves"],
    "script": "Never ignore this dark psychology rule. When someone tries to rush your decision, they are almost always hiding a bad deal. Slow down, go silent, and watch them panic.",
    "caption": "Never Ignore This Psychology Rule #shorts #psychology #mindset #facts"
}

try:
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = """
    Act as a top 1% viral US YouTube Shorts creator. Niche: Dark Psychology & Stoic Mindset.
    Write a high-retention 22-second script (around 55-65 words).
    Rules:
    - First sentence MUST be a curiosity-inducing hook under 4 seconds.
    - Fast-paced, zero fluff, conversational American English.
    Return ONLY valid JSON:
    {
      "keywords": ["rain", "dark forest", "city night"],
      "script": "spoken voiceover text only",
      "caption": "Viral Title #shorts #psychology #facts"
    }
    """
    res = model.generate_content(prompt).text
    match = re.search(r'\{.*\}', res, re.DOTALL)
    if match:
        parsed = json.loads(match.group(0))
        if "script" in parsed and "keywords" in parsed:
            data = parsed
except Exception as e:
    print("Menggunakan naskah default:", e)

# 2. Buat Voiceover + Rekam Detik Per Kata (100% Akurat seperti CapCut Pro)
word_timings = []
async def make_audio_and_subs():
    tts = edge_tts.Communicate(data["script"], "en-US-AndrewNeural", rate="+12%", pitch="-3Hz")
    with open("voice.mp3", "wb") as f:
        async for chunk in tts.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start_sec = chunk["offset"] / 10_000_000
                dur_sec = chunk["duration"] / 10_000_000
                word_timings.append({"word": chunk["text"], "start": start_sec, "end": start_sec + dur_sec})

asyncio.run(make_audio_and_subs())
voice_clip = AudioFileClip("voice.mp3")
total_dur = voice_clip.duration

# 3. Buat Dark Cinematic Ambient Backsound Otomatis (Tanpa Copyright)
sample_rate = 44100
t = np.linspace(0, total_dur, int(sample_rate * total_dur), endpoint=False)
# Paduan nada bass sinematik rendah (Dark Drone)
drone = 0.04 * (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 110 * t) + 0.25 * np.sin(2 * np.pi * 82.4 * t))
with wave.open("bgm.wav", "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    wf.writeframes((drone * 32767).astype(np.int16).tobytes())

bgm_clip = AudioFileClip("bgm.wav")
final_audio = CompositeAudioClip([bgm_clip, voice_clip])

# 4. Ambil 3 Video HD Asli dari Pixabay (Potong Cepat Tiap 3-4 Detik)
video_clips = []
if PIXABAY_KEY:
    for idx, kw in enumerate(data["keywords"][:3]):
        try:
            q = requests.utils.quote(kw)
            url = f"https://pixabay.com/api/videos/?key={PIXABAY_KEY}&q={q}&video_type=film&per_page=3"
            r = requests.get(url, timeout=15).json()
            if r.get("hits"):
                vid_url = r["hits"][0]["videos"]["medium"]["url"]
                vname = f"vid_{idx}.mp4"
                with open(vname, "wb") as vf:
                    vf.write(requests.get(vid_url, timeout=25).content)
                vc = VideoFileClip(vname).without_audio()
                # Ubah ke ukuran 9:16 Full HD
                vc = vc.resize(height=1920)
                if vc.w < 1080:
                    vc = vc.resize(width=1080)
                vc = vc.crop(x1=vc.w/2 - 540, y1=vc.h/2 - 960, width=1080, height=1920)
                video_clips.append(vc)
        except Exception as e:
            print("Gagal ambil video:", e)

if video_clips:
    bg_video = concatenate_videoclips(video_clips, method="compose").loop(duration=total_dur)
else:
    bg_video = ColorClip(size=(1080, 1920), color=(12, 12, 18), duration=total_dur)

# Gelapkan video latar 40% agar teks sangat menonjol & sinematik
dark_layer = ColorClip(size=(1080, 1920), color=(0, 0, 0), duration=total_dur).set_opacity(0.45)

# 5. Download Font Montserrat ExtraBold & Buat Subtitle Pop-Up Per 2 Kata
font_url = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Black.ttf"
with open("Montserrat-Black.ttf", "wb") as ff:
    ff.write(requests.get(font_url).content)
font = ImageFont.truetype("Montserrat-Black.ttf", 80)

# Gabungkan per 2 kata agar cepat & dinamis seperti kreator US
sub_clips = []
for i in range(0, len(word_timings), 2):
    group = word_timings[i:i+2]
    text_str = " ".join([w["word"].upper() for w in group])
    start_t = group[0]["start"]
    end_t = word_timings[i+2]["start"] if (i+2) < len(word_timings) else total_dur
    dur_t = max(0.15, end_t - start_t)

    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text_str, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x_pos = (1080 - tw) // 2
    y_pos = 900

    # Bayangan hitam tebal + warna bergantian Putih & Kuning Emas pada kata kunci
    color = (255, 215, 0, 255) if (i // 2) % 3 == 0 else (255, 255, 255, 255)
    draw.text((x_pos, y_pos), text_str, font=font, fill=color, stroke_width=10, stroke_fill=(0, 0, 0, 255))

    sc = ImageClip(np.array(img)).set_start(start_t).set_duration(dur_t)
    sub_clips.append(sc)

# 6. Render Final
final = CompositeVideoClip([bg_video, dark_layer] + sub_clips).set_audio(final_audio).set_duration(total_dur)
final.write_videofile("final_video.mp4", fps=30, codec="libx264", audio_codec="aac", bitrate="8000k")

with open("caption.txt", "w") as f:
    f.write(data["caption"])
