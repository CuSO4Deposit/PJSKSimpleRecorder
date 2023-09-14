import httpx
from loguru import logger
import sqlite3


def get_response(url: str, headers=None):
    if headers == None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0"
        }
    with httpx.Client() as client:
        response = client.get(url, headers=headers)
        if not response.is_success:
            logger.warning(f"status code: {response.status_code}")
            return
        try:
            response_json = response.json()
            return response_json
        except:
            logger.error("Error when decoding response as json.")


def get_song_id(alias: str):
    """return (title, musicId, match)"""
    url = f"https://api.unipjsk.com/getsongid/{alias}"
    response = get_response(url)
    if response["status"] == "success":
        return response["title"], response["musicId"], response["match"]
    else:
        return False
