
import pickle
import os
import io
from datetime import datetime, timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from datetime import datetime, timezone
from googleapiclient.http import MediaIoBaseDownload

TOKEN_PATH = '../token.pkl'
UPDATES_PATH = '../updates.pkl'
DATABASE_PATH = '../databases.pkl'
FILENAME_USER_DATABASE = 'drivesearch_metadatabase_transformer.pkl'


def load_user_specific_database_from_drive(service):
    

    # Step 1: Find the file by name
    response = service.files().list(
        q=f"name = '{FILENAME_USER_DATABASE}' and trashed = false",
        spaces='drive',
        fields='files(id, name, mimeType)',
        pageSize=1
    ).execute()

    files = response.get('files', [])
    if not files:
        return None  # File not found

    file_id = files[0]['id']

    # Step 2: Download the file as a byte stream
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    fh.seek(0)

    # Step 3: De-pickle the content
    try:
        database = pickle.load(fh)
        return database
    except Exception as e:
        print(f"Failed to unpickle {FILENAME_USER_DATABASE}: {e}")
        return None

def save_update_store(update_store):
    with open(UPDATES_PATH, 'wb') as f:
        pickle.dump(update_store, f)

def save_databases(databases):
    with open(DATABASE_PATH, 'wb') as f:
        pickle.dump(databases, f)

def get_recent_files(service, since_time):
    query = f"modifiedTime > '{since_time}' and trashed = false and name != '{FILENAME_USER_DATABASE}'"
    all_files = []
    page_token = None
    while True:
        try:
            response = service.files().list(
                q=query,
                fields='nextPageToken, files(id, name, mimeType, modifiedTime)',
                orderBy='modifiedTime desc',
                pageSize=1000,
                pageToken=page_token
            ).execute()
            files = response.get('files', [])
        except HttpError as e:
            print("Error fetching files:", e)
            break

        all_files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

    return files

def load_user_creds(username, token_path='token.pkl'):
    with open(token_path, 'rb') as f:
        token_store = pickle.load(f)
    creds = token_store.get(username)
    if creds is None:
        raise ValueError(f"No credentials found for user {username}")
    return refresh_if_needed(creds)

def load_token_store():
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError("token.pkl not found.")
    with open(TOKEN_PATH, 'rb') as f:
        return pickle.load(f)

def load_update_store():
    if os.path.exists(UPDATES_PATH):
        with open(UPDATES_PATH, 'rb') as f:
            return pickle.load(f)
    else:
        return {}