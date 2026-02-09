def detect_content_type(content_type_header: str, content: str):
    if not content_type_header:
        return "unknown"

    header = content_type_header.lower()

    if "application/json" in header:
        return "json"

    if "text/html" in header:
        return "html"

    if "text/plain" in header:
        return "text"

    # fallback based on content
    if content.strip().startswith("{") or content.strip().startswith("["):
        return "json"

    return "unknown"
