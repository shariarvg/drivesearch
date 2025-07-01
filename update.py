'''
asynchronous backend code ofr updating a user's database with any new changes
'''

import pickle
import os
import io
from datetime import datetime, timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from datetime import datetime, timezone

from search_tools import build_user_specific_tuple_database, random_embedding, sentence_embedding, update_user_specific_tuple_database
from database_pickle_tools import upload_pickle_to_drive, database_to_pickle

from user_data import *

TOKEN_PATH = 'token.pkl'
UPDATES_PATH = 'updates.pkl'
DATABASE_PATH = 'databases.pkl'
FILENAME_USER_DATABASE = 'drivesearch_metadatabase_transformer.pkl'

def refresh_if_needed(creds):
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("Credentials are invalid and cannot be refreshed.")
    return creds

def update_database_new_files(username, files, service, embedding_method, database, build_method, update_method):
    if database is None:
        return build_method(files, service, embedding_method)

    else:
        return update_method(files, service, database, embedding_method)

def main():
    token_store = load_token_store()
    update_store = load_update_store()
    #databases = load_databases()
    #print(databases)
    embedding_method = sentence_embedding
    build_method = build_user_specific_tuple_database
    update_method = update_user_specific_tuple_database

    results = {}

    for username, creds in token_store.items():
        print(f"Processing user: {username}")
        creds = refresh_if_needed(creds)
        service = build('drive', 'v3', credentials=creds)
        database = load_user_specific_database_from_drive(service)



        # Use last update time or default to epoch start
        since_time = update_store.get(username, "2025-06-29T00:00:00Z")
        update_store[username] = datetime.now(timezone.utc).isoformat()
        print(f"Last update time: {since_time}")

        files = get_recent_files(service, since_time)
        database = update_database_new_files(username, files, service, embedding_method, database, build_method, update_method)
        pickle_bytes = database_to_pickle(database)
        upload_pickle_to_drive(service, FILENAME_USER_DATABASE, pickle_bytes, parent_folder_id = None)
        
    # Save updated timestamps
    save_update_store(update_store)
    #save_databases(databases)

    return results

if __name__ == "__main__":
    updated_files = main()
    for user, files in updated_files.items():
        print(f"\nUser: {user}\nUpdated File IDs: {files}")
