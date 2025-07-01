from googleapiclient.http import MediaIoBaseDownload
import io

def extract_file(file, service, verbose = False):
    file_id = file['id']
    file_name = file['name']
    mime_type = file['mimeType']

    if verbose:
        print(f"Downloading: {file_name} ({mime_type})")

    # 2. Skip folders or non-downloadable files
    if mime_type != 'application/vnd.google-apps.document':  # or 'text/plain', etc.
        return None, None, None, None

    # 3. Download file content
    request = service.files().export_media(
        fileId=file_id,
        mimeType='text/plain'
    ) if mime_type.startswith('application/vnd.google-apps') else service.files().get_media(fileId=file_id)

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    fh.seek(0)
    content = fh.read().decode('utf-8')  # or 'utf-16' depending on encoding

    return file_id, file_name, mime_type, content

def get_k_files_metadata(service, k = 10):
    results = service.files().list(pageSize=10, fields="files(id, name, mimeType)").execute()
    files = results.get('files', [])
    return results, files

def get_specific_files_metadata(service, file_ids, mimeType = True):
    file_metadata = []
    for fid in file_ids:
        try:
            if mimeType:
                f = service.files().get(fileId=fid, fields='id, name, mimeType').execute()
            else:
                f = service.files().get(fileId=fid, fields='id, name').execute()
            file_metadata.append(f)
        except Exception as e:
            print(f"Failed to get file {fid}: {e}")

    return file_metadata

def get_all_filenames_database(service, database):
    file_ids = [a[0] for a in database]
    return [a['name'] for a in get_specific_files_metadata(service, file_ids, False)]