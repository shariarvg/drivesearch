import io
from googleapiclient.http import MediaIoBaseUpload
import pickle

def upload_pickle_to_drive(service, filename, pkl_io, parent_folder_id=None):
    # Step 1: Check if file already exists
    query = f"name = '{filename}' and trashed = false"
    if parent_folder_id:
        query += f" and '{parent_folder_id}' in parents"

    response = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)',
        pageSize=1
    ).execute()

    existing_files = response.get('files', [])
    file_metadata = {
        'name': filename,
        'mimeType': 'application/octet-stream'
    }
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]

    # Rewind the BytesIO before uploading
    pkl_io.seek(0)
    media = MediaIoBaseUpload(pkl_io, mimetype='application/octet-stream')

    if existing_files:
        file_id = existing_files[0]['id']
        print(f"Overwriting existing file: {filename} (ID: {file_id})")
        uploaded_file = service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
    else:
        print(f"Uploading new file: {filename}")
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()

    return uploaded_file

def database_to_pickle(database):

    # Serialize to in-memory bytes
    pkl_bytes = io.BytesIO()
    pickle.dump(database, pkl_bytes)
    pkl_bytes.seek(0)
    return pkl_bytes