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
    """
    try:
        doc = nlp(text)
        lemmas = []
        for sent in doc.sentences:
            for word in sent.words:
                lemmas.append(word.lemma)
        return lemmas
    except Exception as e:
        print(f"Error lemmatizing: {e}")
        return re.findall(r'\w+', text.lower())

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
        nlp = stanza.Pipeline('grc', processors='tokenize,lemma', verbose=False)
    except Exception as e:
        print(f"Error initializing Stanza: {e}")
        return
    
    corpus_lemmas = Counter()
    work_stats = {}
    
    # Process XMLs
    for name, filename in FILES.items():
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            print(f"Processing {name}...")
            text = parse_xml_tei(path)
            if text:
                # Chunking for Stanza
                # Stanza can be memory intensive.
                chunk_size = 5000
                chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                lemmas = []
                for i, chunk in enumerate(chunks):
                    # Simple progress
                    if i % 10 == 0: print(f"  Chunk {i}/{len(chunks)}")
                    lemmas.extend(lemmatize_text(chunk, nlp))
                
                counts = Counter(lemmas)
                work_stats[name] = counts
                corpus_lemmas.update(counts)


        else:
            print(f"File not found: {filename}")
            
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

