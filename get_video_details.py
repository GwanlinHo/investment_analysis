import yt_dlp
import sys
import re
import os
import json

def get_urls_from_md(file_path):
    urls = []
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return urls
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # Regex to find markdown links: - [Title](URL)
        matches = re.findall(r'-\s\[.*?\]\((https?://.*?)\)', content)
        urls = matches
    return urls

def main():
    md_file = 'videolist.md'
    urls = get_urls_from_md(md_file)
    
    if not urls:
        print("No URLs found in videolist.md")
        return

    print(f"Found {len(urls)} videos to process.")

    ydl_opts = {
        'quiet': True,
        'ignoreerrors': True,
        'skip_download': True,
        'no_warnings': True,
    }

    results = []

    for url in urls:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    video_data = {
                        "url": url,
                        "title": info.get('title', 'N/A'),
                        "uploader": info.get('uploader', 'N/A'),
                        "description": info.get('description', ''),
                        "chapters": []
                    }
                    
                    chapters = info.get('chapters')
                    if chapters:
                        for chapter in chapters:
                            video_data["chapters"].append({
                                "start_time": chapter.get('start_time'),
                                "title": chapter.get('title')
                            })
                    results.append(video_data)
                    print(f"Processed: {video_data['title']}")
        except Exception as e:
            print(f"Error processing {url}: {e}")
            
    with open('video_details.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Saved details to video_details.json")

if __name__ == "__main__":
    main()