from search_tools import sentence_embedding, search_against_faiss, establish_faiss, chunk_embedding
import argparse
from googleapiclient.discovery import build
from user_data import load_token_store, load_user_specific_database_from_drive
from file_tools import get_specific_files_metadata, get_all_filenames_database

FILENAME_USER_DATABASE = 'drivesearch_metadatabase_chunk.pkl'

embedding_fn = chunk_embedding
'''
parser = argparse.ArgumentParser()
parser.add_argument("--username", type = str, required = True)
parser.add_argument("--query", type = str, required = True)
parser.add_argument('--k', type = int, required = True)
args = parser.parse_args()
'''
def return_file_ids(username, query, k):
    query_embedding = embedding_fn(query)

    token_store = load_token_store()

    creds = token_store[args.username]
    service = build('drive', 'v3', credentials=creds)
    database = load_user_specific_database_from_drive(service, FILENAME_USER_DATABASE)
    file_ids = search_against_faiss(query_embedding, database, args.k)

    return get_specific_files_metadata(service, file_ids)
