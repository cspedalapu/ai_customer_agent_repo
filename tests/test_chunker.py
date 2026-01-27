from core.chunker import chunk_text

def test_chunk_text_basic():
    text = "a" * 2000
    chunks = chunk_text(text, chunk_size=900, overlap=100)
    assert len(chunks) >= 2
    assert all(len(c) <= 900 for c in chunks)
