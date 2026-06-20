def test_hello():
    from app.main import hello
    assert hello() == {"message": "hello from devops-eval ci app"}


def test_health():
    from app.main import health
    assert health() == {"status": "ok"}
