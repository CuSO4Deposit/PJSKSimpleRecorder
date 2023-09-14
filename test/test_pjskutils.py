from modules import utils as pjsk


def test_get_song_id():
    r = pjsk.get_song_id("消失")
    assert r[0] == "初音ミクの消失"
    assert r[1] == 49
    assert r[2] == 1
