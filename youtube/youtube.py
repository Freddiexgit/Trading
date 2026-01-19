from pytube import YouTube

video_url = "https://www.youtube.com/watch?v=DTTy2MsTLCc"
yt = YouTube( video_url)
# Auto‑generated English subtitles usually use "a.en"
caption = yt.captions.get("a.en")
if caption:
    srt = caption.generate_srt_captions()
    with open("auto_subtitles.srt", "w", encoding="utf-8") as f:
        f.write(srt)
        print("Auto‑generated subtitles downloaded.")
else:
    print("Auto‑generated subtitles not found.")
