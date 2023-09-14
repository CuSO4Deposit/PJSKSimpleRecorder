from contextlib import closing
import httpx
import json
from loguru import logger
from pathlib import Path
import sqlite3


def insert_into_db(
    song_id: int,
    song_name: str,
    difficulty: str,
    perfect: int,
    great: int,
    good: int,
    bad: int,
    miss: int,
    time: int,
    user: str,
):
    db_path = Path(__file__).parent.parent / "database" / "pjsk.db"
    if not db_path.exists():
        db_path.parent.mkdir(exist_ok=True)
        with closing(sqlite3.connect(db_path)) as con:
            with con:
                con.execute(
                    """\
                    CREATE TABLE record(
                        [song_id] INT NOT NULL,
                        [song_name] TEXT NOT NULL,
                        [difficulty] TEXT NOT NULL,
                        [perfect] INT NOT NULL,
                        [great] INT NOT NULL,
                        [good] INT NOT NULL,
                        [bad] INT NOT NULL,
                        [miss] INT NOT NULL,
                        [time] INT NOT NULL,
                        [user] TEXT NOT NULL,
                        PRIMARY KEY([time], [user])
                    );"""
                )
    with closing(sqlite3.connect(db_path)) as con:
        with con:
            con.execute(
                """
                INSERT INTO record ([song_id], [song_name], [difficulty], [perfect], [great], [good], [bad], [miss], [time], [user])
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    song_id,
                    song_name,
                    difficulty,
                    perfect,
                    great,
                    good,
                    bad,
                    miss,
                    time,
                    user,
                ),
            )


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


def get_song_info(song_id: int, difficulty: str | None = None):
    musicsjson = Path(__file__).parent.parent / "database" / "musics.json"
    musicDifficultiesjson = (
        Path(__file__).parent.parent / "database" / "musicDifficulties.json"
    )
    info = {}

    with open(musicsjson) as f:
        result = json.load(f)
        for i in result:
            if i["id"] != song_id:
                continue
            info["title"] = i["title"]
            break
    info["musicId"] = song_id

    if difficulty is None:
        return info


    with open(musicDifficultiesjson) as f:
        result = json.load(f)
        for i in result:
            if i["musicId"] == song_id and i["musicDifficulty"] == difficulty:
                info["playLevel"] = i["playLevel"]
                info["totalNoteCount"] = i["totalNoteCount"]

    info["musicDifficulty"] = difficulty

    return info
