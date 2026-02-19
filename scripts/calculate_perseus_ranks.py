import csv
import os
import stanza
from analyze_frequency import parse_xml_tei, parse_sblgnt

# Mapping of display name to filename pattern
WORKS = {
    "Lysias 24": "Lysias_24.xml",
    "Antiphon 01": "Antiphon_01.xml",
    "Isaeus 01": "Isaeus_01.xml",
    "Lysias 01": "Lysias_01.xml",
    "Hyperides 06": "Hyperides_06.xml",
    "Andocides 01": "Andocides_01.xml",
    "Lycurgus 01": "Lycurgus_01.xml",
    "Aeschines 03": "Aeschines_03.xml",
    "Demosthenes 18": "Demosthenes_18.xml",
    "Anabasis": "anabasis.xml",
    "Iliad": "iliad.xml",
    "Republic": "republic.xml",
    "Odyssey": "odyssey.xml",
    "Peloponnesian War": "peloponnesian_war.xml",
    "Herodotus": "herodotus.xml"
}

NT_FILES_DIR = "data" # They are *-morphgnt.txt

def get_nt_lemmas():
    lemmas = []
    # Assuming similar logic to analyze_frequency.py but simplified finding
    import glob
    files = glob.glob(os.path.join(NT_FILES_DIR, "*-morphgnt.txt"))
    for f in files:
        lemmas.extend(parse_sblgnt(f))
    return lemmas

def calculate_rank_for_coverage(text_lemmas, corpus_freq_list, thresholds=[0.95, 0.98]):
    # Filter out punctuation and numbers, keep only actual words
    text_lemmas = [l for l in text_lemmas if any(c.isalpha() for c in l)]
    
    total_tokens = len(text_lemmas)
    if total_tokens == 0: return {t: 0 for t in thresholds}
    
    target_counts = {t: total_tokens * t for t in thresholds}
    ranks = {t: -1 for t in thresholds}
    current_covered = 0
    
    # Pre-calculate counts of each lemma in the text
    from collections import Counter
    text_counts = Counter(text_lemmas)
    
    sorted_thresholds = sorted(thresholds)
    thresholds_met = 0
    
    for rank, corpus_lemma in enumerate(corpus_freq_list, 1):
        if corpus_lemma in text_counts:
            current_covered += text_counts[corpus_lemma]
        
        for t in sorted_thresholds:
            if ranks[t] == -1 and current_covered >= target_counts[t]:
                ranks[t] = rank
                thresholds_met += 1
        
        if thresholds_met == len(thresholds):
            break
            
    return ranks

def main():
    print("Loading Weighted Perseus Frequency List...")
    corpus_freq = []
    with open('perseus_weighted.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Lemma']:
                corpus_freq.append(row['Lemma'])
    
    print(f"Loaded {len(corpus_freq)} lemmas from corpus.")

    # Initialize with POS for filtering
    nlp = stanza.Pipeline('grc', processors='tokenize,pos,lemma', verbose=False)
    
    results = {}

    print(f"{'Work':<20} | {'Perseus Rank (98%)':<20}")
    print("-" * 45)

    # Process XML works
    for work_name, filename in WORKS.items():
        filepath = os.path.join("data", filename)
        if not os.path.exists(filepath):
            print(f"Skipping {work_name}: {filepath} not found")
            continue
            
        try:
            text = parse_xml_tei(filepath)
            lemmas = []
            
            # Helper function for consistent filtering
            def process_chunk_text(chunk_text):
                chunk_lemmas = []
                doc = nlp(chunk_text)
                for sent in doc.sentences:
                    for word in sent.words:
                        # Exact same filters as analyze_frequency.py
                        if word.upos in ["PROPN", "PUNCT"]:
                            continue
                        if not all('\u0370' <= c <= '\u03FF' or c in ["'", "-"] for c in word.lemma):
                            continue
                        chunk_lemmas.append(word.lemma)
                return chunk_lemmas

            chunk_size = 50000
            if len(text) > chunk_size:
                 chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                 for chunk in chunks:
                     lemmas.extend(process_chunk_text(chunk))
            else:
                lemmas.extend(process_chunk_text(text))
            
            # DEBUG: Check overlap
            corpus_set = set(corpus_freq)
            overlap = [l for l in lemmas if l in corpus_set]
            print(f"DEBUG {work_name}: {len(overlap)}/{len(lemmas)} lemmata found in corpus list.")
            if len(overlap) < len(lemmas):
                 missing = [l for l in lemmas if l not in corpus_set][:5]
                 print(f"DEBUG Missing examples: {missing}")

            ranks = calculate_rank_for_coverage(lemmas, corpus_freq)
            results[work_name] = ranks
            print(f"{work_name:<20} | 95%: {ranks[0.95]:<10} | 98%: {ranks[0.98]:<10}")
            
        except Exception as e:
            print(f"Error processing {work_name}: {e}")

    # Process New Testament
    print("Processing New Testament...")
    nt_lemmas = get_nt_lemmas()
    nt_ranks = calculate_rank_for_coverage(nt_lemmas, corpus_freq)
    results["Nouveau Testament"] = nt_ranks
    print(f"{'Nouveau Testament':<20} | 95%: {nt_ranks[0.95]:<10} | 98%: {nt_ranks[0.98]:<10}")

if __name__ == "__main__":
    main()
