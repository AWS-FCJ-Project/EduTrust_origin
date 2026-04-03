import importlib


def test_db_engine_created():
    import src.db

    importlib.reload(src.db)
    engine = src.db.get_engine()
    assert engine is not None
