import requests
import os

PERSEUS_BASE = "https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/data"
SBLGNT_BASE = "https://raw.githubusercontent.com/morphgnt/sblgnt/master"

# Perseus text mapping
# Lysias (tlg0540) speeches 1, 12, 24 are famous. Download a few.
# Demosthenes (tlg0014) 18 (Crown), 1 (Olynthiac), 9 (Philippic 3).
# Isocrates (tlg0010) 4 (Panegyricus).
# Herodotus (tlg0016) 1 (Histories).

ADDITIONAL_TEXTS = {
    "herodotus": {"path": "tlg0016/tlg001", "files": ["tlg0016.tlg001.perseus-grc2.xml", "tlg0016.tlg001.perseus-grc1.xml"]},
    "demosthenes_on_crown": {"path": "tlg0014/tlg018", "files": ["tlg0014.tlg018.perseus-grc2.xml", "tlg0014.tlg018.perseus-grc1.xml"]},
    "isocrates_panegyricus": {"path": "tlg0010/tlg011", "files": ["tlg0010.tlg011.perseus-grc2.xml", "tlg0010.tlg011.perseus-grc1.xml"]}, # Panegyricus is tlg011? Checking... usually tlg004. I'll rely on script fallback or download multiple.
    # Lysias
    "lysias_1": {"path": "tlg0540/tlg001", "files": ["tlg0540.tlg001.perseus-grc2.xml", "tlg0540.tlg001.perseus-grc1.xml"]},
    "lysias_12": {"path": "tlg0540/tlg012", "files": ["tlg0540.tlg012.perseus-grc2.xml", "tlg0540.tlg012.perseus-grc1.xml"]},
    "lysias_24": {"path": "tlg0540/tlg024", "files": ["tlg0540.tlg024.perseus-grc2.xml", "tlg0540.tlg024.perseus-grc1.xml"]},
}

# New Testament Names
NT_BOOKS = [
    "61-Mt", "62-Mk", "63-Lk", "64-Jn", "65-Ac", "66-Ro", "67-1Co", "68-2Co", "69-Ga", "70-Eph",
    "71-Php", "72-Col", "73-1Th", "74-2Th", "75-1Ti", "76-2Ti", "77-Tit", "78-Phm", "79-Heb", "80-Ja",
    "81-1Pe", "82-2Pe", "83-1Jn", "84-2Jn", "85-3Jn", "86-Ju", "87-Re"
]

DATA_DIR = "data"

def download_perseus(url, filename):
    print(f"Trying {url}...")
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join(DATA_DIR, filename), 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename}")
        return True
    return False

def download_sblgnt(book_code):
    filename = f"{book_code}-morphgnt.txt"
    url = f"{SBLGNT_BASE}/{filename}"
    print(f"Trying {url}...")
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join(DATA_DIR, filename), 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename}")
        return True
    else:
        print(f"Failed {filename}: {response.status_code}")
        return False

def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    # Download additional Perseus texts
    for name, info in ADDITIONAL_TEXTS.items():
        success = False
        for fname in info["files"]:
            url = f"{PERSEUS_BASE}/{info['path']}/{fname}"
            if download_perseus(url, f"{name}.xml"):
                success = True
                break
        if not success:
            print(f"Could not download {name}")
            
    # Download NT
    for book in NT_BOOKS:
        download_sblgnt(book)

if __name__ == "__main__":
    main()
