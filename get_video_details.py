import yt_dlp
import sys

# Set encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

urls = [
    "https://www.youtube.com/watch?v=QVlUUZMmJcQ",
    "https://www.youtube.com/watch?v=OrqAYoAKd8M",
    "https://www.youtube.com/watch?v=BFWQsIpPKxc",
    "https://www.youtube.com/watch?v=0OQ2W-_6LMY",
    "https://www.youtube.com/watch?v=L9CvG5f_TAA",
    "https://www.youtube.com/watch?v=-FKQu1RRLv8",
    "https://www.youtube.com/watch?v=fTzwCB5g8Dc"
]

ydl_opts = {
    'quiet': True,
    'ignoreerrors': True,
    'skip_download': True,
    'no_warnings': True,
}

for url in urls:
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                print(f"---START DATA---")
                print(f"URL: {url}")
                print(f"Title: {info.get('title', 'N/A')}")
                print(f"Uploader: {info.get('uploader', 'N/A')}")
                
                desc = info.get('description', '')
                # Ensure description is printed cleanly
                print(f"Description: {desc}")
                
                chapters = info.get('chapters')
                if chapters:
                    print("Chapters_List:")
                    for chapter in chapters:
                        print(f"{chapter.get('start_time')} - {chapter.get('title')}")
                print(f"---END DATA---")
    except Exception as e:
        print(f"Error processing {url}: {e}")