import os, json, asyncio, requests, urllib.parse
import google.generativeai as genai
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeVideoClip

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# 1. Buat Ide, Naskah US, dan Prompt Gambar AI
model = genai.GenerativeModel("gemini-1.5-flash")
prompt = """
Act as a viral US Shorts creator. Niche: Dark Psychology & Stoic Facts.
Create a 30-second script in casual American English with a strong 3-second hook.
Return ONLY valid JSON with this exact format, no markdown:
{"image_prompt": "dark cinematic moody illustration of a stoic statue in the rain, vertical wallpaper", "script": "spoken voiceover text only", "caption": "Catchy US title #shorts #psychology #facts"}
"""
res = model.generate_content(prompt).text.strip()
res = res.replace("```json", "").replace("```", "").strip()
data = json.loads(res)

# 2. Buat Voiceover US
async def make_audio():
    tts = edge_tts.Communicate(data["script"], "en-US-ChristopherNeural", rate="+10%")
    await tts.save("voice.mp3")
asyncio.run(make_audio())

# 3. Buat Visual Otomatis via Pollinations AI (Tanpa API Key)
encoded_prompt = urllib.parse.quote(data["image_prompt"])
img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true"

with open("bg.jpg", "wb") as f:
    f.write(requests.get(img_url).content)

# 4. Gabungkan Audio & Gambar jadi Video MP4
audio = AudioFileClip("voice.mp3")
bg_clip = ImageClip("bg.jpg").set_duration(audio.duration)

dark_overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).set_opacity(0.25).set_duration(audio.duration)

final = CompositeVideoClip([bg_clip, dark_overlay]).set_audio(audio)
final.write_videofile("final_video.mp4", fps=24, codec="libx264", audio_codec="aac")

with open("caption.txt", "w") as f:
    f.write(data["caption"])
