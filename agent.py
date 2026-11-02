import os, json, re, asyncio, requests, urllib.parse, textwrap
import numpy as np
import google.generativeai as genai
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips

api_key = os.environ.get("GEMINI_API_KEY", "").strip()
genai.configure(api_key=api_key)

# 1. Buat Ide, Naskah US, & 3 Adegan Visual Berbeda
data = {
    "prompts": [
        "dark cinematic moody portrait of a mysterious man in shadows, 8k, photorealistic, unreal engine 5",
        "ancient marble stoic statue in heavy rain with lightning, dark aesthetic, 8k resolution, cinematic lighting",
        "silhouette of a person standing on a skyscraper edge looking at neon city night, 8k, hyper detailed"
    ],
    "script": "Here is a dark psychology trick you need to know. If someone insults you in public, pause and look at them silently for three seconds, then calmly ask: are you okay? This instantly flips the power dynamic and makes them feel deeply insecure.",
    "caption": "Dark Psychology Power Move You Should Know #shorts #psychology #stoicism #facts #usa"
}

try:
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = """
    Act as a viral US Shorts creator. Niche: Dark Psychology & Human Behavior Facts.
    Create a punchy 25-second script in casual American English with a shocking 3-second hook.
    Return ONLY valid JSON with this exact format, no markdown:
    {
      "prompts": [
        "detailed 8k dark cinematic vertical scene 1 description",
        "detailed 8k dark cinematic vertical scene 2 description",
        "detailed 8k dark cinematic vertical scene 3 description"
      ],
      "script": "spoken voiceover text only",
      "caption": "Catchy US viral title #shorts #psychology #facts"
    }
    """
    res = model.generate_content(prompt).text
    match = re.search(r'\{.*\}', res, re.DOTALL)
    if match:
        parsed = json.loads(match.group(0))
        if "prompts" in parsed and len(parsed["prompts"]) >= 3:
            data = parsed
except Exception as e:
    print("Menggunakan naskah cadangan:", e)

# 2. Buat Voiceover US yang Tegas & Jernih
async def make_audio():
    tts = edge_tts.Communicate(data["script"], "en-US-ChristopherNeural", rate="+8%", pitch="-2Hz")
    await tts.save("voice.mp3")
asyncio.run(make_audio())

audio = AudioFileClip("voice.mp3")
total_dur = audio.duration
scene_dur = total_dur / 3.0

# 3. Download 3 Gambar AI Kualitas Tinggi (Flux Model) & Beri Efek Kamera Zoom
scene_clips = []
for i, p in enumerate(data["prompts"][:3]):
    fname = f"bg_{i}.jpg"
    img_ok = False
    try:
        full_p = f"{p}, vertical 9:16, 8k resolution, photorealistic, cinematic lighting, dark moody aesthetic"
        encoded = urllib.parse.quote(full_p)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=flux&nologo=true&seed={i+42}"
        r = requests.get(url, timeout=35)
        if r.status_code == 200 and len(r.content) > 5000:
            with open(fname, "wb") as f:
                f.write(r.content)
            img = Image.open(fname).convert("RGB").resize((1080, 1920), Image.LANCZOS)
            # Gelapkan sedikit agar teks subtitle kuning/putih sangat kontras & terbaca jelas
            img = Image.eval(img, lambda x: int(x * 0.65))
            img.save(fname, quality=95)
            img_ok = True
    except Exception as e:
        print(f"Scene {i} gagal diunduh:", e)

    if not img_ok:
        Image.new("RGB", (1080, 1920), color=(15, 15, 22)).save(fname)

    # Efek Slow Zoom-In (Ken Burns) agar visual selalu hidup & bergerak
    base_img = Image.open(fname)
    def make_zoom(t, dur=scene_dur, im=base_img):
        scale = 1.0 + 0.12 * (t / dur)
        w, h = int(1080 * scale), int(1920 * scale)
        resized = im.resize((w, h), Image.BILINEAR)
        left = (w - 1080) // 2
        top = (h - 1920) // 2
        cropped = resized.crop((left, top, left + 1080, top + 1920))
        return np.array(cropped)

    clip = ImageClip(fname).set_duration(scene_dur).fl(lambda gf, t, d=scene_dur, im=base_img: make_zoom(t, d, im))
    scene_clips.append(clip)

bg_video = concatenate_videoclips(scene_clips, method="compose").set_duration(total_dur)

# 4. Buat Teks Subtitle Bergaya Kreator US di Tengah Layar
words = data["script"].split()
chunks = [" ".join(words[i:i+4]) for i in range(0, len(words), 4)]
chunk_dur = total_dur / max(len(chunks), 1)

font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
try:
    font = ImageFont.truetype(font_path, 72)
except:
    font = ImageFont.load_default()

txt_clips = []
for idx, text_chunk in enumerate(chunks):
    txt_img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_img)
    lines = textwrap.wrap(text_chunk.upper(), width=16)
    y_pos = 880 - (len(lines) * 45)

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x_pos = (1080 - tw) // 2
        # Garis tepi hitam tebal (Stroke) & Teks Kuning/Putih Tajam
        draw.text((x_pos, y_pos), line, font=font, fill=(255, 235, 59, 255), stroke_width=8, stroke_fill=(0, 0, 0, 255))
        y_pos += 90

    t_clip = ImageClip(np.array(txt_img)).set_start(idx * chunk_dur).set_duration(chunk_dur)
    txt_clips.append(t_clip)

# 5. Render Kualitas Tinggi (Full HD 1080p, 30 FPS, Bitrate 8000k Tajam)
final = CompositeVideoClip([bg_video] + txt_clips).set_audio(audio)
final.write_videofile(
    "final_video.mp4",
    fps=30,
    codec="libx264",
    audio_codec="aac",
    bitrate="8000k",
    preset="medium"
)

with open("caption.txt", "w") as f:
    f.write(data["caption"])
