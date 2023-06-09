import urllib.request
import zipfile
import os
from datasets import load_dataset, load_from_disk, Dataset
import pickle
import nltk
nltk.download('punkt')
import argparse
import logging
import json

from data import Vocabulary

def parse_option():
    parser = argparse.ArgumentParser(description="Downloading and preprocessing SNLI, downloading GloVe and creating vocabulary")

    parser.add_argument('--download_snli', action='store_true', default = False, help='Download and pre-process the SNLI dataset')
    parser.add_argument('--download_glove', action='store_true', default = False, help='Download the GloVe dataset')
    parser.add_argument('--create_vocab', action='store_true', default = False, help='Create the vocabulary')
    
    parser.add_argument('--path_to_vocab', type=str, default='store/vocab.pkl', help='Path to vocab')
    parser.add_argument('--path_to_vec', type=str, default='data/glove.840B.300d.txt', help='Path to GloVe dataset')

    args = parser.parse_args()

    return args


####### Download and pre-process the SNLI dataset #######

def tokenize(example):
    example['premise']    = [word.lower() for word in nltk.tokenize.word_tokenize(example['premise'])]
    example['hypothesis'] = [word.lower() for word in nltk.tokenize.word_tokenize(example['hypothesis'])]
    return example

def drop_missing_label(example):
    return example['label'] != -1

def preprocess_snli(dataset):
    for split in dataset:
        dataset[split] = dataset[split].map(tokenize)
        dataset[split] = dataset[split].filter(drop_missing_label)
    return dataset

def download_snli():
    print('Downloading SNLI dataset...')
    dataset_snli = load_dataset("snli")

    print('Adding examples to be predicted to SNLI dataset...')
    with open('data/examples_snli.json', 'r') as f:
        predict_data = json.load(f)
    dataset_snli['predict'] = Dataset.from_dict(predict_data)

    print('Pre-processing SNLI dataset...')
    dataset_snli = preprocess_snli(dataset_snli)

    print('Saving SNLI dataset to disk...')
    dataset_snli.save_to_disk("data/snli")

    print('Done!')

####### Download the GloVe dataset #######

def download_glove():
    print("Downloading GloVe dataset...")
    glove_url = "http://nlp.stanford.edu/data/glove.840B.300d.zip"
    zip_file_name = "data/glove.840B.300d.zip"

    urllib.request.urlretrieve(glove_url, zip_file_name)

    # Extract the GloVe dataset in the data directory and remove zip file
    print("Extracting GloVe dataset...")
    with zipfile.ZipFile(zip_file_name, 'r') as zip_ref:
        zip_ref.extractall("data")
    os.remove(zip_file_name)

    print("Done!")

####### Main #######

def main(args):
    os.makedirs('data', exist_ok=True)
    
    if args.download_snli:
        download_snli()

    if args.download_glove:
        download_glove()
    
    if args.create_vocab:
        logging.info('Loading SNLI...')
        dataset_snli = load_from_disk('data/snli')

        samples = dataset_snli['train']['premise'] + dataset_snli['train']['hypothesis'] + \
                    dataset_snli['validation']['premise'] + dataset_snli['validation']['hypothesis'] + \
                    dataset_snli['test']['premise'] + dataset_snli['test']['hypothesis']

        vocab = Vocabulary(samples, path_to_vec = args.path_to_vec)


        print(f'Saving vocab to {args.path_to_vocab}')
        os.makedirs(os.path.dirname(args.path_to_vocab), exist_ok=True)
        with open(args.path_to_vocab, 'wb') as f:
            pickle.dump(vocab, f)

if __name__ == '__main__':
    args = parse_option()
    print(args)
    main(args)