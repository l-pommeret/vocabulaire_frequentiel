import requests
import os

BASE_URL = "https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/data"

# TLG IDs mapping with potential filenames
TEXTS = {
    "iliad": {
        "path": "tlg0012/tlg001",
        "filenames": ["tlg0012.tlg001.perseus-grc2.xml", "tlg0012.tlg001.perseus-grc1.xml"]
    },
    "odyssey": {
        "path": "tlg0012/tlg002",
        "filenames": ["tlg0012.tlg002.perseus-grc2.xml", "tlg0012.tlg002.perseus-grc1.xml"]
    },
    "republic": {
        "path": "tlg0059/tlg030",
        "filenames": ["tlg0059.tlg030.perseus-grc2.xml", "tlg0059.tlg030.perseus-grc1.xml"]
    },
    "antigone": {
        "path": "tlg0011/tlg002",
        "filenames": ["tlg0011.tlg002.perseus-grc2.xml", "tlg0011.tlg002.perseus-grc1.xml"]
    },
    "peloponnesian_war": {
        "path": "tlg0003/tlg001",
        "filenames": ["tlg0003.tlg001.perseus-grc2.xml", "tlg0003.tlg001.perseus-grc1.xml"]
    },
    "anabasis": {
        "path": "tlg0032/tlg006",
        "filenames": ["tlg0032.tlg006.perseus-grc2.xml", "tlg0032.tlg006.perseus-grc1.xml"]
    },
    # For NT, we will try to find a specific edition or just download Revelation as a placeholder
    "new_testament_revelation": {
        "path": "tlg0031/tlg027",
        "filenames": ["tlg0031.tlg027.perseus-grc2.xml", "tlg0031.tlg027.perseus-grc1.xml"]
    }
}

DATA_DIR = "data"

def download_file(url, filename):
    print(f"Trying {url}...")
    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join(DATA_DIR, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename}")
        return True
    else:
        print(f"Failed: {response.status_code}")
        return False

def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    for name, info in TEXTS.items():
        success = False
        for fname in info["filenames"]:
            url = f"{BASE_URL}/{info['path']}/{fname}"
            if download_file(url, f"{name}.xml"):
                success = True
                break
        
        if not success:
            print(f"Could not download {name}")

if __name__ == "__main__":
    main()
