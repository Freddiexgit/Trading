import os
import re
import glob
import yt_dlp

# Configuration
CHANNEL_URL = "https://www.youtube.com/@%E8%84%91%E6%80%BBMrBrain"
TARGET_LANGS = ['en', 'zh-Hans', 'zh-Hant']
OUTPUT_FOLDER = "MrBrain_Transcripts"


def clean_subtitle_text(file_path):
    """
    Parses a VTT/SRT file, cleans metadata/timestamps/tags,
    deduplicates lines, and returns a clean string.
    """
    # Regex to identify timestamp lines (e.g., 00:00:01.500 --> 00:00:03.000)
    timestamp_pattern = re.compile(r'\d{2}:\d{2}:\d{2}[\.,]\d{3}\s-->\s\d{2}:\d{2}:\d{2}[\.,]\d{3}')

    # Regex to remove HTML tags (e.g., <c>, <i>, <font>)
    tag_pattern = re.compile(r'<[^>]+>')

    cleaned_lines = []
    last_line = ""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by newlines
        lines = content.splitlines()

        for line in lines:
            line = line.strip()

            # 1. Skip empty lines
            if not line:
                continue

            # 2. Skip File Headers (WEBVTT) or Metadata keys
            if line == 'WEBVTT' or line.startswith('Kind:') or line.startswith('Language:') or line.startswith(
                    'Style:'):
                continue

            # 3. Skip pure Timestamp lines
            if timestamp_pattern.search(line):
                continue

            # 4. Skip SRT sequence numbers (lines that are just digits)
            if line.isdigit():
                continue

            # 5. Remove HTML tags
            text_content = tag_pattern.sub('', line).strip()

            if not text_content:
                continue

            # 6. Deduplicate consecutive identical lines
            # (Common in auto-generated captions where lines repeat during scrolling)
            if text_content != last_line:
                cleaned_lines.append(text_content)
                last_line = text_content

        return "\n".join(cleaned_lines)

    except Exception as e:
        print(f"[Error] processing {file_path}: {e}")
        return None


def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    print(f"[1/3] Fetching video list and subtitles for: {CHANNEL_URL}")

    ydl_opts = {
        'skip_download': True,  # Do not download the video file
        'writesubtitles': True,  # Download manual subtitles
        'writeautomaticsub': True,  # Download auto-generated if manual not available
        'subtitleslangs': TARGET_LANGS,  # Target languages
        'subtitlesformat': 'vtt',  # Download as VTT (web standard, easy to parse)
        'outtmpl': f'{OUTPUT_FOLDER}/%(upload_date)s_%(title)s [%(id)s].%(ext)s',
        'ignoreerrors': True,  # Continue if one video fails
        'quiet': False,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([CHANNEL_URL])

    print("\n[2/3] Processing and cleaning subtitle files...")

    # Find all downloaded .vtt files in the folder
    subtitle_files = glob.glob(os.path.join(OUTPUT_FOLDER, "*.vtt"))

    if not subtitle_files:
        print("No subtitles found. Check if the channel has captions in the requested languages.")
        return

    count = 0
    for vtt_path in subtitle_files:
        clean_text = clean_subtitle_text(vtt_path)

        if clean_text:
            # Define new filename (.txt)
            txt_path = vtt_path.rsplit('.', 1)[0] + ".txt"

            # Save the clean text
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(clean_text)

            # Remove the original VTT file to keep folder clean
            os.remove(vtt_path)
            count += 1
            print(f"Converted: {os.path.basename(txt_path)}")

    print(f"\n[3/3] Complete! {count} transcripts saved to '/{OUTPUT_FOLDER}'")


if __name__ == "__main__":
    main()