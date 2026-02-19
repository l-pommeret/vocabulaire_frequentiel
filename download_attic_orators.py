import requests
import os
import time

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Base URL for Perseus Canonical Greek Lit
BASE_URL = "https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/data"

# Mapping of Author to TLG ID and approximate number of works to probe
AUTHORS = {
    "Antiphon": {"id": "tlg0028", "range": 6},       # Speeches 1-6
    "Andocides": {"id": "tlg0027", "range": 4},      # Speeches 1-4
    "Isaeus": {"id": "tlg0017", "range": 12},        # Speeches 1-12
    "Dinarchus": {"id": "tlg0029", "range": 3},      # Speeches 1-3
    "Lycurgus": {"id": "tlg0034", "range": 1},       # Speech 1
    "Aeschines": {"id": "tlg0026", "range": 3},      # Speeches 1-3
    "Hyperides": {"id": "tlg0030", "range": 6},      # Fragmentary speeches, try 1-6
    "Demosthenes": {"id": "tlg0014", "range": 61},   # Many speeches
    "Isocrates": {"id": "tlg0010", "range": 21},     # Many speeches
    "Lysias": {"id": "tlg0540", "range": 35}         # Many speeches
}

def download_file(url, filename):
    print(f"Checking {url}...")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {filename}")
            return True
        else:
            # Try alternate filename format (sometimes -grc2)
            if "grc1" in url:
                alt_url = url.replace("grc1", "grc2")
                print(f"  > Trying alternate: {alt_url}")
                alt_response = requests.get(alt_url)
                if alt_response.status_code == 200:
                    with open(filename, 'wb') as f:
                        f.write(alt_response.content)
                    print(f"Downloaded: {filename} (grc2)")
                    return True
            return False
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def main():
    for author, info in AUTHORS.items():
        tlg_id = info["id"]
        limit = info["range"]
        print(f"\n--- Downloading {author} ({tlg_id}) ---")
        
        found_count = 0
        for i in range(1, limit + 1):
            # Format work ID: tlg001, tlg002, etc.
            work_id = f"tlg{i:03d}"
            
            # Construct URL
            # Path: data/tlg0028/tlg001/tlg0028.tlg001.perseus-grc1.xml
            url = f"{BASE_URL}/{tlg_id}/{work_id}/{tlg_id}.{work_id}.perseus-grc1.xml"
            filename = os.path.join(DATA_DIR, f"{author}_{i:02d}.xml")
            
            if os.path.exists(filename):
                print(f"Skipping {filename} (already exists)")
                found_count += 1
                continue
                
            if download_file(url, filename):
                found_count += 1
            
            # Be nice to the server
            time.sleep(0.2)
            
        if found_count == 0:
            print(f"WARNING: No files found for {author}. Check TLG ID.")

if __name__ == "__main__":
    main()
