from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import numpy as np
import pickle
from google.auth.transport.requests import Request
import os

def get_and_write_creds():
    # Scopes define what data you want access to
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'openid'
    ] 

    #if creds is not None:
    #    return creds

    client_config = {
        "installed": {
            "client_id": os.environ['client_id'],
            "project_id": os.environ['project_id'],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": os.environ['client_secret'],
            "redirect_uris": ["https://drivesearch.onrender.com"]
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    # This opens a browser window for the user to log in and approve
    creds = flow.run_local_server(port=8080, access_type = 'offline', prompt = 'consent')
    oauth = get_oauth2_api(creds)
    username = get_user_name(oauth)

    # Save token for later use
    TOKEN_FILE = 'token.pkl'
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as f:
            token_store = pickle.load(f)
    else:
        token_store = {}

    token_store[username] = creds

    with open(TOKEN_FILE, 'wb') as f:
        pickle.dump(token_store, f)

    return creds, username

def get_google_drive_api(creds):
    service = build('drive', 'v3', credentials=creds)
    return service

def get_oauth2_api(creds):
    service = build('oauth2', 'v2', credentials=creds)
    return service

def get_user_email(service):
    return service.userinfo().get().execute()['email']

def get_user_name(service):
    user_email = get_user_email(service)
    ind = user_email.index("@gmail.com")
    return user_email[:ind]

def store_database(database, fname):
    with open(fname+".pkl", 'wb') as dump_file:
        pickle.dump(database, dump_file)
'''
creds, username = get_and_write_creds()
'''
#drive = get_google_drive_api(creds)
#results, files = get_k_files_metadata(drive, 10)
#database = build_tuple_database(files, drive, embed_content)
#store_database(database, "database_"+username)

#query_embedding = 10

#print(execute_search(drive, find_closest_oN, database, query_embedding))


    
