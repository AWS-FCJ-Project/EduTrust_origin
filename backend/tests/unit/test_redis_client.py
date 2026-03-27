from src.memory.redis_client import RedisClient


def test_build_key_without_prefix_does_not_crash():
    client = RedisClient()
    client.key_prefix = None

    assert client.build_key("chat", "conversation", "123") == "chat:conversation:123"


def test_build_key_with_prefix_includes_prefix():
    client = RedisClient()
    client.key_prefix = "edutrust"

    assert (
        client.build_key("chat", "conversation", "123")
        == "edutrust:chat:conversation:123"
    )
