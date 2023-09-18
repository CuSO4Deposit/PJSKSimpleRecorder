from fastapi import FastAPI, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
import modules.utils as pjsk
from pathlib import Path
from time import gmtime, strftime
from time import time as current_time
from typing import Annotated

app = FastAPI()
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
templates = Jinja2Templates(Path(__file__).parent / "templates")


@app.get("/")
def mainpage(request: Request):
    return templates.TemplateResponse("mainpage.html", {"request": request})


@app.get("/redirect/alias/")
def get_song(alias: str, request: Request):
    try:
        _, musicId, _ = pjsk.get_song_id(alias)
        return RedirectResponse(f"/form/{musicId}", status_code=status.HTTP_308_PERMANENT_REDIRECT)
    except:
        resp = {"message": "No record matches your query, try another name?", "request": request}
        return templates.TemplateResponse("error.html", resp)


@app.get("/form/{musicId}")
def fill_form(musicId: int, request: Request):
    info = pjsk.get_song_info(musicId)
    title = info["title"]
    difficulties = info["difficulties"]
    resp = {
        "id": musicId,
        "title": title,
        "difficulties": difficulties,
        "request": request,
    }
    return templates.TemplateResponse("fill_form.html", resp)


@app.post("/redirect/record/{musicId}")
def add_record_redirect(
    musicId: int,
    difficulty: Annotated[str, Form()],
    great: Annotated[int, Form()],
    good: Annotated[int, Form()],
    bad: Annotated[int, Form()],
    miss: Annotated[int, Form()],
    user: Annotated[str, Form()],
):
    return RedirectResponse(f"/record/{user}/{musicId}/{difficulty}/{great}/{good}/{bad}/{miss}", status_code=status.HTTP_308_PERMANENT_REDIRECT)


@app.post("/record/{userId}/{musicId}/{difficulty}/{great}/{good}/{bad}/{miss}")
def add_record(
    musicId: int,
    difficulty: str,
    great: int,
    good: int,
    bad: int,
    miss: int,
    userId: str,
    request: Request,
):
    info = pjsk.get_song_info(musicId, difficulty)
    perfect = info["totalNoteCount"] - great - good - bad - miss
    pjsk.insert_into_db(
        musicId,
        info["title"],
        difficulty,
        perfect,
        great,
        good,
        bad,
        miss,
        int(current_time()),
        userId,
    )
    resp = {
        "info": info,
        "user": userId,
        "data": {
            "perfect": perfect,
            "great": great,
            "good": good,
            "bad": bad,
            "miss": miss,
        },
        "request": request,
    }
    return templates.TemplateResponse("success.html", resp)


@app.get("/recent/{user}")
def recent_record(user: str, request: Request):
    recent = pjsk.recent50(user)
    cols = ["song_name", "difficulty", "perfect", "great", "good", "bad", "miss", "time"]
    for idx, tup in enumerate(recent):
        recent[idx] = list(tup)
        recent[idx] = recent[idx][1:-1]
        recent[idx][7] = strftime("%d %b %Y %H:%M:%S UTC", gmtime(recent[idx][7]))
    resp = {"cols": cols, "recent": recent, "request": request} 
    return templates.TemplateResponse("recent.html", resp)
