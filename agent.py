import os, json, re, asyncio, requests, wave, textwrap
import numpy as np
import google.generativeai as genai
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    CompositeAudioClip, concatenate_videoclips, ImageClip, ColorClip
)

api_key = os.environ.get("GEMINI_API_KEY", "").strip()
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY", "").strip()
if api_key:
    genai.configure(api_key=api_key)

# 1. Naskah Viral US + Keyword Video
data = {
    "keywords": ["storm", "city night", "ocean waves"],
    "script": "Never ignore this dark psychology rule. When someone tries to rush your decision, they are almost always hiding a bad deal. Slow down, go silent, and watch them panic.",
    "caption": "Never Ignore This Psychology Rule #shorts #psychology #mindset #facts"
}

try:
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = """
    Act as a viral US YouTube Shorts creator. Niche: Dark Psychology & Stoic Mindset.
    Write a punchy 22-second script (55-65 words) in casual American English.
    Start with a strong 3-second hook.
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
    print("Pakai naskah cadangan:", e)

# 2. Buat Voiceover US
async def make_audio():
    tts = edge_tts.Communicate(data["script"], "en-US-ChristopherNeural", rate="+10%")
    await tts.save("voice.mp3")

asyncio.run(make_audio())
voice_clip = AudioFileClip("voice.mp3")
total_dur = voice_clip.duration

# 3. Buat Dark Cinematic Backsound (Bebas Copyright & Anti-Error)
sample_rate = 44100
t = np.linspace(0, total_dur, int(sample_rate * total_dur), endpoint=False)
drone = 0.035 * (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 110 * t))
with wave.open("bgm.wav", "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    wf.writeframes((drone * 32767).astype(np.int16).tobytes())

bgm_clip = AudioFileClip("bgm.wav")
final_audio = CompositeAudioClip([bgm_clip, voice_clip])

# 4. Ambil Video HD Asli dari Pixabay (Otomatis Potong Vertikal 9:16)
video_clips = []
if PIXABAY_KEY:
    for idx, kw in enumerate(data["keywords"][:3]):
        try:
            q = requests.utils.quote(str(kw))
            url = f"https://pixabay.com/api/videos/?key={PIXABAY_KEY}&q={q}&per_page=3"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                if hits:
                    vid_url = hits[0]["videos"]["medium"]["url"]
                    vname = f"vid_{idx}.mp4"
                    with open(vname, "wb") as vf:
                        vf.write(requests.get(vid_url, timeout=25).content)
                    vc = VideoFileClip(vname).without_audio()
                    vc = vc.resize(height=1920)
                    if vc.w < 1080:
                        vc = vc.resize(width=1080)
                    x_center = int((vc.w - 1080) // 2)
                    vc = vc.crop(x1=x_center, y1=0, width=1080, height=1920)
                    # Batasi tiap adegan maksimal 4 detik agar dinamis
                    vc = vc.subclip(0, min(4.0, vc.duration))
                    video_clips.append(vc)
        except Exception as e:
            print(f"Video {idx} dilewati:", e)

if video_clips:
    bg_video = concatenate_videoclips(video_clips, method="compose").loop(duration=total_dur)
else:
    # Cadangan jika belum isi PIXABAY_API_KEY: buat video bergerak dari Pollinations
    bg_video = ColorClip(size=(1080, 1920), color=(15, 15, 22), duration=total_dur)

dark_layer = ColorClip(size=(1080, 1920), color=(0, 0, 0), duration=total_dur).set_opacity(0.4)

# 5. Buat Teks Pop-Up Cepat (Per 2 Kata) Presisi Sesuai Jumlah Huruf
font_paths = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
]
font = ImageFont.load_default()
for fp in font_paths:
    if os.path.exists(fp):
        font = ImageFont.truetype(fp, 85)
        break

words = data["script"].split()
groups = [" ".join(words[i:i+2]).upper() for i in range(0, len(words), 2)]
total_chars = sum(len(g) for g in groups) or 1

sub_clips = []
curr_t = 0.0
for idx, text_str in enumerate(groups):
    # Durasi tampil dihitung proporsional sesuai panjang kata agar pas dengan suara
    dur_t = (len(text_str) / total_chars) * (total_dur - 0.2)
    dur_t = max(0.2, dur_t)

    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    lines = textwrap.wrap(text_str, width=14)
    y_pos = 880 - (len(lines) * 45)

    # Warna bergantian Kuning Emas & Putih Bersih
    color = (255, 215, 0, 255) if idx % 2 == 0 else (255, 255, 255, 255)

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x_pos = (1080 - tw) // 2
        draw.text((x_pos, y_pos), line, font=font, fill=color, stroke_width=10, stroke_fill=(0, 0, 0, 255))
        y_pos += 95

    sc = ImageClip(np.array(img)).set_start(curr_t).set_duration(dur_t)
    sub_clips.append(sc)
    curr_t += dur_t

# 6. Render Final HD
final = CompositeVideoClip([bg_video, dark_layer] + sub_clips).set_audio(final_audio).set_duration(total_dur)
final.write_videofile("final_video.mp4", fps=30, codec="libx264", audio_codec="aac", bitrate="8000k")

with open("caption.txt", "w") as f:
    f.write(data["caption"])
