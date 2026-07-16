
import os
import re
import pickle
from functools import lru_cache
from typing import List, Tuple

import bm25s
import pymorphy3

INDEX_DIR = os.path.join(os.path.dirname(__file__), "fts_index")
DOC_MAP_PATH = os.path.join(INDEX_DIR, "doc_ids.pkl")

UA_LEGAL_STOPWORDS_LEMMA = {
    "про", "для", "від", "або", "але", "весь", "цей", "бути",
    "щодо", "який", "такий", "той", "як", "чи", "не", "на", "у", "в", "з",
    "зі", "із", "до", "за", "при", "та", "й", "і", "а", "б", "би",
}

_TOKEN_RE = re.compile(r"[а-щьюяєіїґА-ЩЬЮЯЄІЇҐ0-9']{2,}")

_morph = None


def _get_morph() -> pymorphy3.MorphAnalyzer:
    global _morph
    if _morph is None:
        _morph = pymorphy3.MorphAnalyzer(lang="uk")
    return _morph


@lru_cache(maxsize=100_000)
def _lemma_cached(word: str) -> str:
    return _get_morph().parse(word)[0].normal_form


def tokenize_and_lemmatize(text: str, drop_stopwords: bool = True) -> List[str]:
    
    raw_tokens = _TOKEN_RE.findall(text.lower())
    lemmas = [_lemma_cached(t) for t in raw_tokens if len(t) > 1]
    if drop_stopwords:
        lemmas = [l for l in lemmas if l not in UA_LEGAL_STOPWORDS_LEMMA]
    return lemmas

def build_index(doc_chunks: List[Tuple[str, str]]) -> None:
    os.makedirs(INDEX_DIR, exist_ok=True)

    doc_ids = [str(doc_id) for doc_id, _ in doc_chunks]
    corpus_tokens = []
    for i, (_, text) in enumerate(doc_chunks):
        corpus_tokens.append(tokenize_and_lemmatize(text or ""))
        if (i + 1) % 500 == 0:
            print(f"  лемматизировано {i + 1}/{len(doc_chunks)} чанков...")

    print("Строим BM25-индекс...")
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)
    retriever.save(INDEX_DIR)

    with open(DOC_MAP_PATH, "wb") as f:
        pickle.dump(doc_ids, f)

    print(f"✅ Index saved to {INDEX_DIR} ({len(doc_ids)} чанков).")

_retriever = None
_doc_ids_cache = None


def _load_index():
    global _retriever, _doc_ids_cache
    if _retriever is None:
        if not os.path.exists(DOC_MAP_PATH):
            raise FileNotFoundError(
                f"FTS-индекс не найден в {INDEX_DIR}. "
                "Сначала запусти: python -m hybrid_search.build_fts_index"
            )
        _retriever = bm25s.BM25.load(INDEX_DIR, load_corpus=False)
        with open(DOC_MAP_PATH, "rb") as f:
            _doc_ids_cache = pickle.load(f)
    return _retriever, _doc_ids_cache


def search_fts(query_text: str, limit: int = 100) -> List[str]:
    
    retriever, doc_ids = _load_index()

    query_tokens = tokenize_and_lemmatize(query_text)
    if not query_tokens:
        return []

    raw_k = min(limit * 5, len(doc_ids))
    if raw_k == 0:
        return []

    results, scores = retriever.retrieve(
        bm25s.tokenize([" ".join(query_tokens)], return_ids=False),
        k=raw_k,
        show_progress=False,
    )

    best_score_per_doc = {}
    for chunk_idx, score in zip(results[0], scores[0]):
        doc_id = doc_ids[chunk_idx]
        if score <= 0:
            continue
        if doc_id not in best_score_per_doc or score > best_score_per_doc[doc_id]:
            best_score_per_doc[doc_id] = score

    sorted_docs = sorted(best_score_per_doc.items(), key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, _ in sorted_docs[:limit]]