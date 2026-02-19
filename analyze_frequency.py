import os
import re
import glob
from collections import Counter
import xml.etree.ElementTree as ET
# from cltk.lemmatize.grc import GreekBackoffLemmatizer (Removed)
# from cltk.alphabet.grc import GrcNormalize (Removed)

# Constants
DATA_DIR = "data"
OUTPUT_FILE = "frequency_report.md"

# File mappings
FILES = {
    "Republic": "republic.xml",
    "Antigone": "antigone.xml",
    "Pelopennesian War": "peloponnesian_war.xml",
    "Anabasis": "anabasis.xml",
    "Iliad": "iliad.xml",
    "Odyssey": "odyssey.xml",
    "Herodotus": "herodotus.xml",
    "Demosthenes (Crown)": "demosthenes_on_crown.xml",
    "Isocrates (Panegyricus)": "isocrates_panegyricus.xml",
    "Lysias 1": "lysias_1.xml",
    "Lysias 12": "lysias_12.xml",
    "Lysias 24": "lysias_24.xml"
}

# New Testament files
NT_FILES = glob.glob(os.path.join(DATA_DIR, "*-morphgnt.txt"))

def parse_sblgnt(filepath):
    """
    Parses SBLGNT morphgnt files.
    Format is typically space separated.
    We need to check the format from view_file output.
    Assuming: code part_of_speech lemma word ? 
    """
    lemmas = []
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 6:
                # Based on standard morphgnt: 
                # 610101 N- -----sf-m Βίβλος βιβλος
                # Col 0: Ref
                # Col 1: POS
                # Col 2: Parse
                # Col 3: Lemma (sometimes col 6?)
                # 610101 A- NUI -----gsm Ἰησοῦ Ἰησοῦς
                # Let's look at the file content.
                # 610101 N- NSF       Βίβλος  βίβλος
                # ref pos parse word lemma
                lemma = parts[-1] 
                lemmas.append(lemma)
    return lemmas

def parse_xml_tei(filepath):
    """
    Parses TEI XML to extract text.
    """
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        # TEI namespace usually
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
        text_content = ""
        
        # Extract all text from 'body'
        body = root.find('.//tei:body', ns)
        if body is None:
            # Fallback for no namespace or different structure
            body = root.find('.//body')
        
        if body is not None:
            text_content = "".join(body.itertext())
        else:
            print(f"Warning: No body found in {filepath}")
            return []
            
        return text_content
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return []

def lemmatize_text(text, lemmatizer):
    """
    Lemmatizes Greek text using CLTK.
    """
    # Normalize ?
    # tokenizer is included in lemmatizer usually? 
    # BackoffLemmatizer.lemmatize expects a list of tokens usually.
    # We need to tokenize first.
    # Simple split might be enough for now or use cltk tokenizer (which needs download).
    # I'll use simple regex for speed and robustnes if tokenizer fails.
    
    tokens = re.findall(r'\w+', text.lower())
    # Filter non-greek ?
    greek_tokens = [t for t in tokens if any('\u0370' <= c <= '\u03FF' for c in t)] 
    
def lemmatize_text(text, nlp):
    """
    Lemmatizes Greek text using Stanza.
    Filters out Proper Nouns (PROPN) and non-Greek characters.
    """
    try:
        doc = nlp(text)
        lemmas = []
        for sent in doc.sentences:
            for word in sent.words:
                # Filter 1: Proper Nouns
                if word.upos == "PROPN":
                    continue
                
                # Filter 2: Non-Greek characters (e.g. Latin noise, numbers)
                # Keep only if ALL chars are Greek (or hyphen/apostrophe if needed, but strictly Greek is safer for frequency)
                if not all('\u0370' <= c <= '\u03FF' or c in ["'", "-"] for c in word.lemma):
                    continue
                    
                # Filter 3: Punctuation (usually handled by POS, but extra safety)
                if word.upos == "PUNCT":
                    continue

                lemmas.append(word.lemma)
        return lemmas
    except Exception as e:
        print(f"Error lemmatizing: {e}")
        return []

def calculate_coverage(lemma_counts, threshold=0.98):
    total_words = sum(lemma_counts.values())
    sorted_lemmas = lemma_counts.most_common()
    
    running_sum = 0
    unique_lemmas_needed = 0
    target_count = total_words * threshold
    
    for lemma, count in sorted_lemmas:
        running_sum += count
        unique_lemmas_needed += 1
        if running_sum >= target_count:
            break
            
    return unique_lemmas_needed, total_words

def main():
    print("Initializing Stanza NLP...")
    import stanza
    try:
        # Check if dir exists or just try download
        stanza.download('grc', verbose=False) 
        # Added 'pos' to processors
        nlp = stanza.Pipeline('grc', processors='tokenize,pos,lemma', verbose=False)
    except Exception as e:
        print(f"Error initializing Stanza: {e}")
        return
    
    corpus_lemmas = Counter()
    work_stats = {}
    
    # Process XMLs
    xml_files = glob.glob(os.path.join(DATA_DIR, "*.xml"))
    print(f"Found {len(xml_files)} XML files to process.")
    
    for path in xml_files:
        filename = os.path.basename(path)
        name = filename.replace(".xml", "").replace("_", " ").title()
        
        print(f"Processing {name}...")
        text = parse_xml_tei(path)
        if text:
            # Chunking for Stanza
            chunk_size = 50000 # Increased chunk size for speed, Stanza handles it
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            lemmas = []
            for i, chunk in enumerate(chunks):
                 # visual progress
                 pass
            
            # actually we can just lemmatize the whole thing if it's not massive
            # but chunking is safer.
            for chunk in chunks:
                lemmas.extend(lemmatize_text(chunk, nlp))
            
            counts = Counter(lemmas)
            work_stats[name] = counts
            corpus_lemmas.update(counts)
        else:
            print(f"Warning: No text found in {filename}")
            
    # Process NT
    nt_lemmas = []
    print("Processing New Testament...")
    for nt_file in NT_FILES:
        # Assuming parse_sblgnt returns correct lemmas
        # I need to verify column index from view_file
        # Will assume last column is lemma for now, checking logic later
        lemmas = parse_sblgnt(nt_file)
        nt_lemmas.extend(lemmas)
        
    nt_counts = Counter(nt_lemmas)
    work_stats["New Testament"] = nt_counts
    corpus_lemmas.update(nt_counts)
    
    # Export Corpus Frequency List (Perseus Proxy)
    print("Exporting Perseus Frequency List...")
    with open("perseus_frequency.csv", "w") as f:
        f.write("Rank,Lemma,Count,RelativeFrequency\n")
        total_corpus_tokens = sum(corpus_lemmas.values())
        for rank, (lemma, count) in enumerate(corpus_lemmas.most_common(), 1):
            rel_freq = count / total_corpus_tokens
            f.write(f"{rank},{lemma},{count},{rel_freq:.6f}\n")
    
    # 98% Coverage Calculation
    results = []
    for name, counts in work_stats.items():
        needed, total = calculate_coverage(counts, 0.98)
        results.append({
            "name": name,
            "needed_98": needed,
            "total_tokens": total,
            "unique_lemmas": len(counts),
            "ratio": needed / len(counts) if len(counts) > 0 else 0
        })

    # --- NEW: Weighted Corpus Generation ---
    print("\n--- Generating Weighted Corpus based on Learnability Index (Core/Total) ---")
    weighted_corpus = {} # Use dict for float values
    
    # Sort texts by Index (Ratio) - "Ordonner les textes"
    # ratio = needed_98 / total_tokens (Wait, needed / unique? No, needed / total?)
    # User said: "indice d'apprenabilité (noyau/mots totaux)"
    # My previous code calculated ratio = needed / unique_lemmas. 
    # I should correct this to needed / total_tokens if that's what the user explicitly asked.
    # User: "noyau/mots totaux". 
    # My code line 208: "ratio": needed / len(counts) -> needed / unique.
    # I MUST FIX THIS to needed / total_tokens for the User's Index.
    
    # Re-calculating proper user index
    for r in results:
        r["learnability_index"] = r["needed_98"] / r["total_tokens"] if r["total_tokens"] > 0 else 0
        
    # Sort by this new index
    results.sort(key=lambda x: x["learnability_index"])
    
    print(f"{'Work':<30} | {'Index (Core/Total)':<20} | {'Weight Multiplier'}")
    print("-" * 70)
    
    for r in results: 
        name = r["name"]
        index = r["learnability_index"]
        counts = work_stats[name]
        
        print(f"{name:<30} | {index:.6f}             | x{index:.6f}")
        
        for lemma, count in counts.items():
            if lemma not in weighted_corpus:
                weighted_corpus[lemma] = 0.0
            weighted_corpus[lemma] += count * index

    # Export Weighted List
    print("Exporting Weighted Frequency List (perseus_weighted.csv)...")
    with open("perseus_weighted.csv", "w") as f:
        f.write("Rank,Lemma,WeightedCount,RawCount\n") 
        # We need to sort by WeightedCount
        sorted_weighted = sorted(weighted_corpus.items(), key=lambda item: item[1], reverse=True)
        
        for rank, (lemma, w_count) in enumerate(sorted_weighted, 1):
            raw_count = corpus_lemmas[lemma]
            f.write(f"{rank},{lemma},{w_count:.4f},{raw_count}\n")
            
    # --- END NEW ---

        
    # Compare with Corpus (Top 100, 500, 1000)
    corpus_top_100 = set([l for l, c in corpus_lemmas.most_common(100)])
    corpus_top_500 = set([l for l, c in corpus_lemmas.most_common(500)])
    corpus_top_1000 = set([l for l, c in corpus_lemmas.most_common(1000)])
    
    comparison_results = []
    for name, counts in work_stats.items():
        work_top_100 = set([l for l, c in counts.most_common(100)])
        work_top_500 = set([l for l, c in counts.most_common(500)])
        work_top_1000 = set([l for l, c in counts.most_common(1000)])
        
        comparison_results.append({
            "name": name,
            "overlap_100": len(work_top_100.intersection(corpus_top_100)),
            "overlap_500": len(work_top_500.intersection(corpus_top_500)),
            "overlap_1000": len(work_top_1000.intersection(corpus_top_1000))
        })
        
    # Write Report
    with open(OUTPUT_FILE, "w") as f:
        f.write("# Frequency Analysis Report\n\n")
        f.write("## 98% Coverage Requirements\n")
        f.write("| Work | Total Tokens | Unique Lemmas | Lemmas for 98% Coverage | % of Vocabulary |\n")
        f.write("|---|---|---|---|---|\n")
        
        # Sort by needed_98 ascending
        results.sort(key=lambda x: x["needed_98"])
        
        for r in results:
            f.write(f"| {r['name']} | {r['total_tokens']:,} | {r['unique_lemmas']:,} | {r['needed_98']:,} | {r['ratio']*100:.1f}% |\n")
            
        f.write("\n## Comparison with Generated 'Perseus' (Corpus) List\n")
        f.write("Intersection of Top N words. Determining how standard the vocabulary is.\n\n")
        f.write("| Work | Top 100 Overlap | Top 500 Overlap | Top 1000 Overlap |\n")
        f.write("|---|---|---|---|\n")
        
        comparison_results.sort(key=lambda x: x["overlap_1000"], reverse=True)
        
        for r in comparison_results:
            f.write(f"| {r['name']} | {r['overlap_100']} | {r['overlap_500']} | {r['overlap_1000']} |\n")

    print(f"Report generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

