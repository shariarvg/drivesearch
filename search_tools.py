import numpy as np
import pickle
from file_tools import extract_file, get_specific_files_metadata
import random
from transformers import AutoModel, AutoTokenizer
from sentence_transformers import SentenceTransformer
import faiss
import torch
import nltk

MODEL = SentenceTransformer('all-MiniLM-L6-v2')
#nltk.download('punkt')  # only needed once
#from nltk.tokenize import sent_tokenize

def naive_sentence_split(text):
    return [s.strip() for s in text.split('.') if s.strip()]

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

def chunk_embedding(text, max_chunks=None):
    sentences = naive_sentence_split(text)
    embeddings = MODEL.encode(sentences)  # shape: (S, D)
    embeddings = np.array(embeddings)     # ensure it's a NumPy array

    if max_chunks is None or embeddings.shape[0] <= max_chunks:
        return embeddings

    # Otherwise, group and average
    S, D = embeddings.shape
    chunk_size = int(np.ceil(S / max_chunks))
    reduced_embeddings = []

    for i in range(0, S, chunk_size):
        group = embeddings[i:i+chunk_size]
        avg = group.mean(axis=0)
        reduced_embeddings.append(avg)

    return np.stack(reduced_embeddings)  # shape: (max_chunks, D)


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
    all_embeddings = []
    index_to_doc = []

    for doc_id, mat in database:
        mat_np = mat.cpu().numpy() if isinstance(mat, torch.Tensor) else mat
        all_embeddings.append(mat_np)

        for i in range(mat_np.shape[0]):
            index_to_doc.append((doc_id, i))

    stacked_embeddings = np.vstack(all_embeddings)
    return stacked_embeddings, index_to_doc


def establish_faiss(database):
    """
    Input:
        database: List of (doc_id, embedding_matrix), where embedding_matrix has shape (S_i, D)
    Returns:
        stacked_embeddings: np.ndarray of shape (total_sentences, D)
        index_to_doc: list of (doc_id, sentence_index) for each row in stacked_embeddings
    """
    ids = [a[0] for a in database]
    embeddings, index_to_doc = get_embeddings_from_database(database)
    print(embeddings.shape)
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index_to_doc, index

def search_against_faiss(query_embedding, database, k=1):
    """
    query_embedding: np.ndarray or torch.Tensor of shape (D,)
    database: list of (doc_id, embedding_matrix)
    Returns: list of top-k unique doc_ids based on closest chunks
    """
    index_to_doc, index = establish_faiss(database)

    if isinstance(query_embedding, torch.Tensor):
        query_embedding = query_embedding.cpu().numpy()
    query_embedding = query_embedding.reshape(1, -1)

    faiss.normalize_L2(query_embedding)
    D, I = index.search(query_embedding, 10 * k)  # search more to ensure uniqueness

    seen = set()
    top_k_docs = []

    for i in I[0]:
        doc_id = index_to_doc[i][0]
        if doc_id not in seen:
            seen.add(doc_id)
            top_k_docs.append(doc_id)
        if len(top_k_docs) == k:
            break

    return top_k_docs
