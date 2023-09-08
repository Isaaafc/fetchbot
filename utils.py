from urllib.parse import urlparse

def is_url(text: str) -> bool:
    try:
        urlparse(text)
        return True
    except:
        return False
