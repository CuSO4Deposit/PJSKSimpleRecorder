from modules import utils as pjsk

from contextlib import closing
from pathlib import Path
import sqlite3
from time import time as current_time


def test_insert():
    args = (163, "the EmopErroR", "master", 1593, 0, 0, 0, 0, int(current_time()), "temp")
    pjsk.insert_into_db(*args)

    db_path = Path(__file__).parent.parent / "database" / "pjsk.db"
    with closing(sqlite3.connect(db_path)) as con:
        with con:
            cur = con.cursor()
            cur.execute("SELECT * FROM record;")
            assert cur.fetchone() == args

    db_path.unlink()


def test_get_song_id():
    r = pjsk.get_song_id("皇帝")
    assert r[0] == "the EmpErroR"
    assert r[1] == 163
    assert r[2] == 1


def test_get_song_info():
    info = pjsk.get_song_info(163, "master")
    assert info["title"] == "the EmpErroR"
    assert info["playLevel"] == 36
    assert info["totalNoteCount"] == 1593
    assert info["musicId"] == 163
    assert info["musicDifficulty"] == "master"
