from textkit.core import slugify, word_count, truncate


def test_slugify():
    assert slugify("Hello World") == "hello-world"


def test_word_count():
    assert word_count("a b c") == 3


def test_truncate():
    assert truncate("hello world", 5) == "hello..."
