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
                    )"""
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
    """return difficulties dict if difficulty is None, else return exact info"""

    musicsjson = Path(__file__).parent.parent / "database" / "musics.json"
    musicDifficultiesjson = (
        Path(__file__).parent.parent / "database" / "musicDifficulties.json"
    )
    musicRatingsjson = Path(__file__).parent.parent / "database" / "musicRatings.json"
    info = {}

    with open(musicsjson) as f:
        result = json.load(f)
        for i in result:
            if i["id"] != song_id:
                continue
            info["title"] = i["title"]
            break
    info["musicId"] = song_id

    with open(musicDifficultiesjson) as f:
        result = json.load(f)

        if difficulty is None:
            difficulties = {}
            for i in result:
                if i["musicId"] == song_id:
                    difficulties[i["musicDifficulty"]] = i["playLevel"]
                if len(difficulties) == 5:
                    break
            info["difficulties"] = difficulties
            return info

        for i in result:
            if i["musicId"] == song_id and i["musicDifficulty"] == difficulty:
                info["playLevel"] = i["playLevel"]
                info["totalNoteCount"] = i["totalNoteCount"]
                break

    with open(musicRatingsjson) as f:
        result = json.load(f)
        for i in result:
            if i["musicId"] == song_id and i["musicDifficulty"] == difficulty:
                if "fullComboAdjust" in i and "fullPerfectAdjust" in i:
                    info["fullComboAdjust"] = i["fullComboAdjust"]
                    info["fullPerfectAdjust"] = i["fullPerfectAdjust"]

    info["musicDifficulty"] = difficulty

    return info


def recent50(user: str) -> list[tuple]:
    db_path = Path(__file__).parent.parent / "database" / "pjsk.db"
    with closing(sqlite3.connect(db_path)) as con:
        with con:
            cur = con.cursor()
            cur.execute(
                """\
                SELECT * FROM record
                WHERE [user] = ?
                ORDER BY [time] DESC
                LIMIT 50;""",
                user,
            )
            result = cur.fetchall()
    return result


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def get_record(time: int, user: str):
    db_path = Path(__file__).parent.parent / "database" / "pjsk.db"
    with closing(sqlite3.connect(db_path)) as con:
        with con:
            con.row_factory = dict_factory
            cur = con.cursor()
            cur.execute(
                """\
                SELECT * FROM record
                WHERE [time] = ? AND [user] = ?
                    """,
                (
                    time,
                    user,
                ),
            )
            res = cur.fetchone()
            return res


def update_record(
    difficulty: str,
    perfect: int,
    great: int,
    good: int,
    bad: int,
    miss: int,
    user: str,
    origin_time: int,
    origin_user: str,
):
    db_path = Path(__file__).parent.parent / "database" / "pjsk.db"
    with closing(sqlite3.connect(db_path)) as con:
        with con:
            con.execute(
                """
                UPDATE record SET
                [difficulty] = ?, 
                [perfect] = ?,
                [great] = ?,
                [good] = ?,
                [bad] = ?,
                [miss] = ?,
                [user] = ?
                WHERE [time] = ? AND [user] = ?""",
                (
                    difficulty,
                    perfect,
                    great,
                    good,
                    bad,
                    miss,
                    user,
                    origin_time,
                    origin_user,
                ),
            )


async def stream_binary(url: str, path: Path):
    async with httpx.AsyncClient(timeout=10.0).stream("GET", url) as resp:
        if resp.status_code != 200:
            logger.warning(f"{resp.status_code} when GET {url}")
            return None
        with path.open("wb") as f:
            async for byte in resp.aiter_bytes():
                f.write(byte)


def get_acc(song_id: int, difficulty: str, great: int, good: int, bad: int, miss: int):
    info = get_song_info(song_id, difficulty)
    note_count = info["totalNoteCount"]
    return 1 - (great + good * 2 + bad * 3 + miss * 3) / (note_count * 3)


def get_play_rating(
    song_id: int, difficulty: str, great: int, good: int, bad: int, miss: int
):
    info = get_song_info(song_id, difficulty)
    fc_flag = (good == 0) and (bad == 0) and (miss == 0)
    ap_flag = (great == 0) and fc_flag
    exist_flag = ("fullComboAdjust" in info) and ("fullPerfectAdjust" in info)
    rating = info["playLevel"]
    if not exist_flag:
        pass
    else:
        if ap_flag:
            rating += info["fullPerfectAdjust"]
        else:
            rating += min(info["fullPerfectAdjust"], info["fullComboAdjust"])
    return rating * get_acc(song_id, difficulty, great, good, bad, miss)
