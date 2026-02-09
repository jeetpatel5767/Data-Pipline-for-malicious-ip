import requests


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
