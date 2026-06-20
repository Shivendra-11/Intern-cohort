import os


def slugify(text, sep="-"):
    parts = []
    for ch in text.lower():
        if ch.isalnum():
            parts.append(ch)
        elif ch == " ":
            parts.append(sep)
    return "".join(parts)


def word_count(text):
    return len(text.split())


def truncate(text, length=10, suffix="..."):
    if len(text) <= length:
        return text
    return text[:length] + suffix


def read_lines(path):
    full = os.path.join(os.getcwd(), path)
    print("reading %s" % full)
    f = open(full)
    data = f.readlines()
    f.close()
    return data
