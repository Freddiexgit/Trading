from yt_dlp import YoutubeDL

ydl_opts = {
    "skip_download": True,
    "writesubtitles": True,
    "writeautomaticsub": True,
    "subtitleslangs": ["en", "zh-Hans", "zh-Hant"],
    "subtitlesformat": "vtt",  # or "srt"
}

with YoutubeDL(ydl_opts) as ydl:
    ydl.download(["https://www.youtube.com/watch?v=cOxXsKLXbAw"])
