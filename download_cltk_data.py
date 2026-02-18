from cltk.corpus.utils.importer import CorpusImporter
import os

def main():
    try:
        c = CorpusImporter('greek')
        print("Available corpora:", c.list_corpora)
        
        # specific corpora
        corpora_to_download = ['greek_text_perseus', 'greek_treebank_perseus', 'tlg', 'greek_text_first1kgreek']
        
        for corpus in corpora_to_download:
            if corpus in c.list_corpora:
                print(f"Downloading {corpus}...")
                c.import_corpus(corpus)
                print(f"Downloaded {corpus}")
            else:
                print(f"Corpus {corpus} not found available.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
