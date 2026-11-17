import re
import urllib.request

# Add your public M3U URLs here
M3U_URLS = [
    "https://www.apsattv.com/inlg.m3u",
    "https://www.apsattv.com/uslg.m3u",
    "https://www.apsattv.com/gblg.m3u",
    "https://www.apsattv.com/calg.m3u",
    "https://www.apsattv.com/whaletvplus_us.m3u",
    "https://www.apsattv.com/whaletvplus_in.m3u",
    "https://www.apsattv.com/whaletvplus_gb.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/refs/heads/main/samsungtvplus/in.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/refs/heads/main/samsungtvplus/us.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/refs/heads/main/samsungtvplus/gb.m3u",
     "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/roku_all.m3u", 
    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/plutotv_us.m3u", 
    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/plex_us.m3u" ,
    "https://raw.githubusercontent.com/amazeyourself/m3u/refs/heads/main/yupptvfast.m3u",
]

OUTPUT_FILE = "combined.m3u"


def fetch_m3u(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def process_playlists():
    seen_channels = set()
    output_lines = ["#EXTM3U"]

    for url in M3U_URLS:
        try:
            content = fetch_m3u(url)
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            continue

        lines = [line.strip() for line in content.splitlines() if line.strip()]
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("#EXTINF"):
                # Split the #EXTINF line into attributes and the channel title at the last comma
                if "," in line:
                    meta, raw_title = line.rsplit(",", 1)

                    # Remove leading channel number and whitespace (e.g., "100 LG Channels..." -> "LG Channels...")
                    clean_title = re.sub(r"^\d+\s+", "", raw_title.strip())

                    # Deduplicate based on cleaned channel name (case-insensitive)
                    channel_key = clean_title.lower()

                    # Grab the stream URL (usually the next non-comment line)
                    stream_url = ""
                    j = i + 1
                    while j < len(lines) and lines[j].startswith("#"):
                        j += 1
                    if j < len(lines):
                        stream_url = lines[j]

                    if stream_url and channel_key not in seen_channels:
                        seen_channels.add(channel_key)
                        output_lines.append(f"{meta},{clean_title}")
                        output_lines.append(stream_url)

                    i = j + 1
                    continue
            i += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")
    print(f"Saved {len(seen_channels)} unique channels to {OUTPUT_FILE}")


if __name__ == "__main__":
    process_playlists()