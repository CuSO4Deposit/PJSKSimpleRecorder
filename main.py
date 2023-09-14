from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
import modules.utils as pjsk
from pathlib import Path
from pydantic import BaseModel
from time import time as current_time
from typing import Annotated

app = FastAPI()
templates = Jinja2Templates(Path(__file__).parent / "templates")


@app.get("/")
def mainpage(request: Request):
    return templates.TemplateResponse("mainpage.html", {"request": request})


@app.post("/alias/")
def get_song(alias: Annotated[str, Form()]):
    _, musicId, _ = pjsk.get_song_id(alias)
    return RedirectResponse(f"/form/{musicId}/")


@logger.catch
@app.post("/form/{musicId}")
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


@app.post("/record/{musicId}")
def add_record(
    musicId: int,
    difficulty: Annotated[str, Form()],
    perfect: Annotated[int, Form()],
    great: Annotated[int, Form()],
    good: Annotated[int, Form()],
    bad: Annotated[int, Form()],
    miss: Annotated[int, Form()],
    user: Annotated[str, Form()],
    request: Request,
):
    info = pjsk.get_song_info(musicId, difficulty)
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
        user,
    )
    resp = {
        "info": info,
        "user": user,
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
