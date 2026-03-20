# =============================================================================
# OLD S3 VECTORS CODE (COMMENTED OUT FOR RESTORATION)
# =============================================================================
# import uuid
# from typing import Any, Dict, List
# import boto3
# import numpy as np
# from src.app_config import app_config
#
# class VectorStore:
#     def __init__(self):
#         self.bucket_name = app_config.VECTOR_SEARCH_BUCKET
#         self.index_name = app_config.VECTOR_SEARCH_INDEX_NAME
#         self.region = app_config.AWS_REGION or "ap-southeast-1"
#         self.s3v_client = boto3.client(
#             "s3vectors",
#             aws_access_key_id=app_config.AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=app_config.AWS_SECRET_ACCESS_KEY,
#             region_name=self.region,
#         )
#         self.dimension = 384
#
#         print(f"VectorStore (S3 Vectors) initialized with Bucket: {self.bucket_name}, Index: {self.index_name}")
#         self._ensure_index_exists()
#
#     def _ensure_index_exists(self):
#         try:
#             indices = self.s3v_client.list_indexes(vectorBucketName=self.bucket_name)["indexes"]
#             if not any(idx["indexName"] == self.index_name for idx in indices):
#                 print(f"Creating S3 Vector Index: {self.index_name}...")
#                 self.s3v_client.create_index(
#                     vectorBucketName=self.bucket_name,
#                     indexName=self.index_name,
#                     dataType="float32",
#                     dimension=self.dimension,
#                     distanceMetric="euclidean"
#                 )
#                 print("Successfully created S3 Vector Index.")
#             else:
#                 print(f"S3 Vector Index '{self.index_name}' already exists.")
#         except Exception as e:
#             print(f"Error ensuring S3 Vector Index exists: {str(e)}")
#
#     def add_embeddings(self, embeddings: np.ndarray, metadata_list: List[Dict[str, Any]]):
#         try:
#             vectors_to_put = []
#             for i, emb in enumerate(embeddings):
#                 vector_data = emb.astype("float32").tolist()
#                 vector_key = str(uuid.uuid4())
#                 metadata = metadata_list[i] if i < len(metadata_list) else {}
#                 vectors_to_put.append({
#                     "key": vector_key,
#                     "data": {"float32": vector_data},
#                     "metadata": metadata
#                 })
#             self.s3v_client.put_vectors(
#                 vectorBucketName=self.bucket_name,
#                 indexName=self.index_name,
#                 vectors=vectors_to_put
#             )
#             print(f"Successfully added {len(vectors_to_put)} vectors to S3 Vectors.")
#         except Exception as e:
#             print(f"ERROR: Could not add vectors to S3 Vectors: {str(e)}")
#
#     def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
#         try:
#             query_data = query_embedding.astype("float32").flatten().tolist()
#             response = self.s3v_client.query_vectors(
#                 vectorBucketName=self.bucket_name,
#                 indexName=self.index_name,
#                 queryVector={"float32": query_data},
#                 topK=top_k,
#                 returnMetadata=True,
#                 returnDistance=True
#             )
#             results = []
#             for item in response.get("vectors", []):
#                 res = item.get("metadata", {}).copy()
#                 res["score"] = float(item.get("distance", 0))
#                 results.append(res)
#             return sorted(results, key=lambda x: x["score"], reverse=False)
#         except Exception as e:
#             print(f"ERROR: Could not search S3 Vectors: {str(e)}")
#             return []
# =============================================================================

import os
import pickle
from typing import Any, Dict, List

import boto3
from rank_bm25 import BM25Okapi
from src.app_config import app_config


class BM25Store:
    def __init__(self):
        self.bucket_name = app_config.S3_BUCKET_NAME  # Use regular S3 bucket
        self.prefix = "bm25_index/"
        self.corpus_path = f"{self.prefix}corpus.pkl"
        self.metadata_path = f"{self.prefix}metadata.pkl"
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=app_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=app_config.AWS_SECRET_ACCESS_KEY,
            region_name=app_config.AWS_REGION,
        )
        self.corpus: List[List[str]] = []
        self.metadata: List[Dict[str, Any]] = []
        self.bm25: BM25Okapi = None

        print(
            f"BM25Store initialized with Bucket: {self.bucket_name}, Prefix: {self.prefix}"
        )
        self.load_from_s3()

    def tokenize(self, text: str) -> List[str]:
        return text.lower().split()

    def load_from_s3(self):
        try:
            # Load Corpus
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=self.corpus_path
            )
            self.corpus = pickle.loads(response["Body"].read())

            # Load Metadata
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=self.metadata_path
            )
            self.metadata = pickle.loads(response["Body"].read())

            if self.corpus:
                self.bm25 = BM25Okapi(self.corpus)
            print(
                f"Successfully loaded BM25 index from S3: {self.bucket_name}/{self.prefix}"
            )
        except Exception as e:
            print(f"Could not load BM25 from S3 (maybe it doesn't exist yet): {str(e)}")

    def save_to_s3(self):
        try:
            # Save Corpus
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self.corpus_path,
                Body=pickle.dumps(self.corpus),
            )

            # Save Metadata
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self.metadata_path,
                Body=pickle.dumps(self.metadata),
            )
            print(
                f"Successfully saved BM25 index to S3: {self.bucket_name}/{self.prefix}"
            )
        except Exception as e:
            print(f"ERROR: Could not save BM25 to S3: {str(e)}")

    def add_document(self, text: str, metadata: Dict[str, Any]):
        tokens = self.tokenize(text)
        self.corpus.append(tokens)
        self.metadata.append(metadata)
        self.bm25 = BM25Okapi(self.corpus)
        self.save_to_s3()

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.bm25 or not self.corpus:
            return []

        tokenized_query = self.tokenize(query)
        # Get scores
        scores = self.bm25.get_scores(tokenized_query)

        # Get top indices
        top_n = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[
            :top_k
        ]

        results = []
        for i in top_n:
            if scores[i] > 0:  # Only return relevant results
                res = self.metadata[i].copy()
                res["score"] = float(scores[i])
                results.append(res)

        return results
