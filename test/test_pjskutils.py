from modules import utils as pjsk


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
