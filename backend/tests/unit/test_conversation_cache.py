from unittest.mock import MagicMock

from src.conversation.conversation_cache import ConversationCache


def make_cache(redis_client: MagicMock) -> ConversationCache:
    return ConversationCache(redis_client=redis_client)


def test_conversation_key_uses_namespaced_redis_key():
    redis_client = MagicMock()
    redis_client.build_key.return_value = "edutrust:chat:conversation:conv-1"
    cache = make_cache(redis_client)

    result = cache._conversation_key("conv-1")

    assert result == "edutrust:chat:conversation:conv-1"
    redis_client.build_key.assert_called_once_with("chat", "conversation", "conv-1")


def test_cache_conversation_returns_false_when_redis_unhealthy():
    redis_client = MagicMock()
    redis_client.is_healthy.return_value = False
    cache = make_cache(redis_client)

    result = cache.cache_conversation({"_id": "conv-1"})

    assert result is False
    redis_client.set_json.assert_not_called()


def test_cache_conversation_returns_false_when_id_missing():
    redis_client = MagicMock()
    redis_client.is_healthy.return_value = True
    cache = make_cache(redis_client)

    result = cache.cache_conversation({"title": "missing id"})

    assert result is False
    redis_client._serialize.assert_not_called()


def test_cache_conversation_serializes_payload_and_sets_ttl():
    redis_client = MagicMock()
    redis_client.is_healthy.return_value = True
    redis_client.build_key.return_value = "chat:conversation:conv-1"
    redis_client._serialize.return_value = {"_id": "conv-1", "messages": []}
    redis_client._ttl_seconds.return_value = 900
    cache = make_cache(redis_client)

    result = cache.cache_conversation({"_id": "conv-1", "messages": []})

    assert result is True
    redis_client._serialize.assert_called_once_with({"_id": "conv-1", "messages": []})
    redis_client.set_json.assert_called_once_with(
        "chat:conversation:conv-1",
        {"_id": "conv-1", "messages": []},
        expiration=900,
    )


def test_cache_conversation_returns_false_on_exception():
    redis_client = MagicMock()
    redis_client.is_healthy.return_value = True
    redis_client._serialize.side_effect = RuntimeError("serialize failed")
    cache = make_cache(redis_client)

    result = cache.cache_conversation({"_id": "conv-1"})

    assert result is False


def test_get_conversation_returns_cached_document():
    redis_client = MagicMock()
    redis_client.is_healthy.return_value = True
    redis_client.build_key.return_value = "chat:conversation:conv-1"
    redis_client.get_json.return_value = {"_id": "conv-1"}
    cache = make_cache(redis_client)

    result = cache.get_conversation("conv-1")

    assert result == {"_id": "conv-1"}
    redis_client.get_json.assert_called_once_with("chat:conversation:conv-1")


def test_get_conversation_returns_none_on_exception():
    redis_client = MagicMock()
    redis_client.is_healthy.return_value = True
    redis_client.build_key.return_value = "chat:conversation:conv-1"
    redis_client.get_json.side_effect = RuntimeError("redis error")
    cache = make_cache(redis_client)

    result = cache.get_conversation("conv-1")

    assert result is None


def test_get_conversation_returns_none_when_redis_unhealthy():
    redis_client = MagicMock()
    redis_client.is_healthy.return_value = False
    cache = make_cache(redis_client)

    result = cache.get_conversation("conv-1")

    assert result is None
    redis_client.get_json.assert_not_called()


def test_invalidate_conversation_uses_delete_result():
    redis_client = MagicMock()
    redis_client.is_healthy.return_value = True
    redis_client.build_key.return_value = "chat:conversation:conv-1"
    redis_client.delete.return_value = True
    cache = make_cache(redis_client)

    result = cache.invalidate_conversation("conv-1")

    assert result is True
    redis_client.delete.assert_called_once_with("chat:conversation:conv-1")


def test_invalidate_conversation_returns_false_when_redis_unhealthy():
    redis_client = MagicMock()
    redis_client.is_healthy.return_value = False
    cache = make_cache(redis_client)

    result = cache.invalidate_conversation("conv-1")

    assert result is False
    redis_client.delete.assert_not_called()


def test_invalidate_conversation_returns_false_on_exception():
    redis_client = MagicMock()
    redis_client.is_healthy.return_value = True
    redis_client.build_key.return_value = "chat:conversation:conv-1"
    redis_client.delete.side_effect = RuntimeError("delete failed")
    cache = make_cache(redis_client)

    result = cache.invalidate_conversation("conv-1")

    assert result is False


def test_close_closes_underlying_redis_client():
    redis_client = MagicMock()
    cache = make_cache(redis_client)

    cache.close()

    redis_client.close.assert_called_once()
