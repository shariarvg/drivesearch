from search_tools import sentence_embedding, search_against_faiss, establish_faiss
import argparse
from googleapiclient.discovery import build
from user_data import load_token_store, load_user_specific_database_from_drive
from file_tools import get_specific_files_metadata, get_all_filenames_database

parser = argparse.ArgumentParser()
parser.add_argument("--username", type = str, required = True)
parser.add_argument("--query", type = str, required = True)
parser.add_argument('--k', type = int, required = True)
args = parser.parse_args()

query_embedding = sentence_embedding(args.query)

token_store = load_token_store()

creds = token_store[args.username]
service = build('drive', 'v3', credentials=creds)
database = load_user_specific_database_from_drive(service)

print(get_all_filenames_database(service, database))

file_ids = search_against_faiss(query_embedding, database, args.k)

print(get_specific_files_metadata(service, file_ids))
