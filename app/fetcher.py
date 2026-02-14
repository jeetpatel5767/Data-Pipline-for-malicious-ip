import requests
from pathlib import Path


def fetch_url(url: str):
    try:
        response = requests.get(url, timeout=10)

        return {
            "success": True,
            "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type"),
            "content": response.text
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def read_file(filepath: str):
    """Read a local .txt file and return the same format as fetch_url."""
    try:
        path = Path(filepath)

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {filepath}"
            }

        if not path.suffix.lower() == ".txt":
            return {
                "success": False,
                "error": f"Unsupported file type: {path.suffix} (only .txt is supported)"
            }

        content = path.read_text(encoding="utf-8")

        return {
            "success": True,
            "status_code": 200,
            "content_type": "text/plain",
            "content": content
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
