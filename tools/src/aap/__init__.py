import tiktoken
from tokenizers import Tokenizer

from aap.assets import load_dashboard
from aap.corpus import build_html, CHUNK_SIZE

HF_TOKENIZERS = ["gpt2", "bert-base-uncased", "google/gemma-3-1b-it"]
TT_ENCODINGS = ["o200k_base", "cl100k_base"]


def make_tokenizer(name: str):
    """Return (encode_fn, decode_fn) with uniform interface.

    encode_fn(text) -> list[int]
    decode_fn(ids)  -> str
    """
    if name in TT_ENCODINGS:
        enc = tiktoken.get_encoding(name)
        return enc.encode, enc.decode

    tok = Tokenizer.from_pretrained(name)
    return lambda text: tok.encode(text).ids, tok.decode


__all__ = [
    "build_html",
    "CHUNK_SIZE",
    "load_dashboard",
    "make_tokenizer",
    "HF_TOKENIZERS",
    "TT_ENCODINGS",
]
