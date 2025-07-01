import numpy as np
import pickle
from file_tools import extract_file, get_specific_files_metadata
import random
from transformers import AutoModel, AutoTokenizer
from sentence_transformers import SentenceTransformer
import faiss
import torch

MODEL = SentenceTransformer('all-MiniLM-L6-v2')



'''
METRICS
'''

def norm2(a,b):
    return (a-b)**2


'''
EMBEDDINGS
'''

def random_embedding(content):
    return random.randint(0,1000)

def sentence_embedding(text):
    embedding = MODEL.encode(text)
    return embedding

'''
DATABASE
'''
def build_user_specific_tuple_database(files, service, embedding_method):
    database = []

    for file in files[:-1]:

        file_id, file_name, mime_type, content = extract_file(file, service, verbose = True)

        if content is not None:
            database.append((file['id'], embedding_method(content)))

    return database

def update_user_specific_tuple_database(new_files, service, database, embedding_method):
    existing_ids = [a[0] for a in database]
    for file in new_files:
        file_id, file_name, mime_type, content = extract_file(file, service, verbose = True)
        if file_id in existing_ids:
            database[existing_ids.index(file_id)] = (file_id, embedding_method(content))
        else:
            database.append((file_id, embedding_method(content)))

    return database

'''
SEARCHES
'''

def find_closest_oN(database, query_embedding):
    closest = float('inf')
    id_closest = None
    for (file_id, val) in database:
        dist = metric(val, query_embedding)
        if dist < closest:
            closest = dist
            id_closest = file_id

    return [id_closest]

def execute_search(service, find_method, database, query_embedding):
    file_ids = find_method(database, query_embedding)
    return get_specific_files_metadata(service, file_ids)

def get_embeddings_from_database(database):
    def access_numpy(tensor_or_np_vec):
        if isinstance(tensor_or_np_vec, torch.Tensor):
            return tensor_or_np_vec.cpu().numpy()
        return tensor_or_np_vec

    return np.vstack([access_numpy(a[1]) for a in database])

def establish_faiss(database):
    ids = [a[0] for a in database]
    embeddings = get_embeddings_from_database(database)
    print(embeddings.shape)
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return ids, index

def search_against_faiss(query_embedding, database, k = 1):
    '''
    query_embedding: torch tensor of shape (D,)
    database: list of (file_id, torch tensor)
    '''
    ids, index = establish_faiss(database)
    D, I = index.search(query_embedding[np.newaxis, :], k)
    return [ids[i] for i in I[0]]