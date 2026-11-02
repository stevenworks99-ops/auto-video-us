import os, json, re, asyncio, requests, urllib.parse
import google.generativeai as genai
import edge_tts
from PIL import Image
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeVideoClip

# 1. Buat Ide & Naskah US (Pakai model terbaru + pelindung anti-error)
api_key = os.environ.get("GEMINI_API_KEY", "").strip()
genai.configure(api_key=api_key)

data = {
    "image_prompt": "dark cinematic moody illustration of a stoic statue in the rain, vertical wallpaper",
    "script": "Here is a dark psychology fact most people never notice. When someone is lying to you, they will often maintain unbroken eye contact to see if you actually believe their story. Watch their blinking rate, not just their words.",
    "caption": "Dark Psychology Trick You Need To Know #shorts #psychology #facts #usa"
}

try:
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = """
    Act as a viral US Shorts creator. Niche: Dark Psychology & Stoic Facts.
    Create a 25-second script in casual American English with a strong 3-second hook.
    Return ONLY valid JSON with this exact format, no markdown:
    {"image_prompt": "dark cinematic vertical wallpaper of a stoic figure", "script": "spoken voiceover text only", "caption": "Catchy US title #shorts #psychology #facts"}
    """
    res = model.generate_content(prompt).text
    match = re.search(r'\{.*\}', res, re.DOTALL)
    if match:
        data = json.loads(match.group(0))
except Exception as e:
    print("Menggunakan naskah cadangan karena API:", e)

print("Judul Video:", data["caption"])

# 2. Buat Voiceover US
async def make_audio():
    tts = edge_tts.Communicate(data["script"], "en-US-ChristopherNeural", rate="+10%")
    await tts.save("voice.mp3")
asyncio.run(make_audio())

# 3. Buat Gambar Background Vertikal (Anti-Error)
img_created = False
try:
    encoded = urllib.parse.quote(data["image_prompt"])
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true"
    r = requests.get(url, timeout=30)
    if r.status_code == 200 and len(r.content) > 1000:
        with open("bg.jpg", "wb") as f:
            f.write(r.content)
        # Pastikan file gambar valid
        Image.open("bg.jpg").convert("RGB").save("bg.jpg")
        img_created = True
except Exception as e:
    print("Gagal unduh gambar, membuat latar gelap estetik:", e)

if not img_created:
    Image.new("RGB", (1080, 1920), color=(18, 18, 24)).save("bg.jpg")

# 4. Gabungkan Audio & Gambar jadi Video MP4
audio = AudioFileClip("voice.mp3")
bg_clip = ImageClip("bg.jpg").set_duration(audio.duration)
dark_overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).set_opacity(0.25).set_duration(audio.duration)

final = CompositeVideoClip([bg_clip, dark_overlay]).set_audio(audio)
final.write_videofile("final_video.mp4", fps=24, codec="libx264", audio_codec="aac")

with open("caption.txt", "w") as f:
    f.write(data["caption"])
