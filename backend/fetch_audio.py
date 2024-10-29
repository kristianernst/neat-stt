import yt_dlp

video_url = "https://www.youtube.com/watch?v=nFj7pJNtjKU"

ydl_opts = {
  "format": "bestaudio/best",
  "outtmpl": "%(title)s.%(ext)s",
  "postprocessors": [
    {
      "key": "FFmpegExtractAudio",
      "preferredcodec": "mp3",  # Change to desired format
      "preferredquality": "192",
    }
  ],
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
  ydl.download([video_url])
