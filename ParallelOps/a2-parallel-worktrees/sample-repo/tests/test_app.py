from app import VERSION, get_info


def test_version_is_string():
    assert isinstance(VERSION, str)


def test_get_info_shape():
    info = get_info()
    assert info["version"] == VERSION
    assert isinstance(info["features"], list)
