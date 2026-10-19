import math

from app.adapters.llm.fake_embedder import FakeEmbedder


def test_deterministic_unit_vectors_of_the_configured_size() -> None:
    embedder = FakeEmbedder(dimensions=16)

    first, other = embedder.embed(["same", "different"], "document")
    again = embedder.embed(["same"], "query")[0]

    assert first == again
    assert first != other
    assert len(first) == 16
    assert math.isclose(math.sqrt(sum(x * x for x in first)), 1)
