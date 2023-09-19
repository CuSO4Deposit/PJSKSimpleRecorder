from modules import utils as pjsk

from contextlib import closing
from pathlib import Path
import pytest
import sqlite3
from time import time as current_time


def test_insert_and_recent():
    args = (163, "the EmpErroR", "master", 1593, 0, 0, 0, 0, int(current_time()), "0")
    pjsk.insert_into_db(*args)

    db_path = Path(__file__).parent.parent / "database" / "pjsk.db"
    with closing(sqlite3.connect(db_path)) as con:
        with con:
            cur = con.cursor()
            cur.execute("SELECT * FROM record;")
            assert cur.fetchone() == args

    args = (
        163,
        "the EmpErroR",
        "master",
        1593,
        0,
        0,
        0,
        0,
        int(current_time()) + 1,
        "1",
    )
    pjsk.insert_into_db(*args)
    recent = pjsk.recent50("1")
    assert isinstance(recent, list)
    assert isinstance(recent[0], tuple)
    assert recent[0][0] == 163

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


@pytest.mark.asyncio
async def test_stream_file(tmp_path: Path):
    url = "https://raw.githubusercontent.com/Sekai-World/sekai-master-db-diff/main/musics.json"
    file_path = tmp_path / "musics.json"
    await pjsk.stream_binary(url, file_path)
    assert tmp_path.stat().st_size
