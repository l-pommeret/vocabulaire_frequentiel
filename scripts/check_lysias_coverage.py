import collections
import csv
from analyze_frequency import lemmatize_text, parse_xml_tei
import stanza
import os

# Load Corpus Frequency List
corpus_freq = []
with open('perseus_frequency.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Columns: Rank,Lemma,Count,RelativeFrequency
        if row['Lemma']:
            corpus_freq.append(row['Lemma'])

# Load Lysias 24
nlp = stanza.Pipeline('grc', processors='tokenize,lemma', verbose=False)
lysias_path = 'data/Lysias_24.xml'
text = parse_xml_tei(lysias_path)
doc = nlp(text)
lysias_lemmas = []
for sent in doc.sentences:
    for word in sent.words:
        lysias_lemmas.append(word.lemma)

total_tokens = len(lysias_lemmas)
print(f"Total tokens in Lysias 24: {total_tokens}")

# Calculate coverage by Top N corpus words
for n in [500, 1000, 2000, 3000, 5000]:
    top_n_corpus = set(corpus_freq[:n])
    covered = [l for l in lysias_lemmas if l in top_n_corpus]
    coverage = len(covered) / total_tokens * 100
    print(f"Coverage with Top {n} corpus words: {coverage:.2f}%")

# Calculate how many corpus words are needed for 98% coverage
covered_count = 0
needed_rank = 0
lysias_lemmas_set = set(lysias_lemmas)

for i, lemma in enumerate(corpus_freq):
    count_in_text = lysias_lemmas.count(lemma)
    if count_in_text > 0:
        covered_count += count_in_text
    
    current_coverage = covered_count / total_tokens
    if current_coverage >= 0.98:
        needed_rank = i + 1
        print(f"Rank needed for 98% coverage of Lysias 24: {needed_rank}")
        break  
