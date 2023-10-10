from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import modules.utils as pjsk
from pathlib import Path
from time import gmtime, strftime
from time import time as current_time
from typing import Annotated

app = FastAPI()
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
templates = Jinja2Templates(Path(__file__).parent / "templates")


async def download_master_db():
    url_base = (
        "https://raw.githubusercontent.com/Sekai-World/sekai-master-db-diff/main/"
    )
    file_name = ["musics.json", "musicDifficulties.json"]
    db_path = Path(__file__).parent / "database"
    for i in file_name:
        file_path = db_path / i
        await pjsk.stream_binary(url=url_base + i, path=file_path)
    await pjsk.stream_binary(
        url="https://raw.githubusercontent.com/watagashi-uni/Unibot/main/masterdata/realtime/musicDifficulties.json",
        path=db_path / "musicRatings.json",
    )


@app.on_event("startup")
async def startup():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        download_master_db, CronTrigger.from_crontab("0 1 * * *"), jitter=120
    )
    scheduler.start()


@app.get("/")
def mainpage(request: Request):
    return templates.TemplateResponse("mainpage.html", {"request": request})


@app.get("/redirect/alias/")
def get_song(alias: str, request: Request):
    try:
        _, musicId, _ = pjsk.get_song_id(alias)
        return RedirectResponse(
            f"/form/{musicId}", status_code=status.HTTP_308_PERMANENT_REDIRECT
        )
    except:
        resp = {
            "message": "No record matches your query, try another name?",
            "request": request,
        }
        return templates.TemplateResponse("error.html", resp)


def fill_form(musicId: int, request: Request, default: dict = {}):
    info = pjsk.get_song_info(musicId)
    title = info["title"]
    difficulties = info["difficulties"]
    resp = {
        "id": musicId,
        "title": title,
        "difficulties": difficulties,
        "request": request,
        "default": default,
    }
    return templates.TemplateResponse("fill_form.html", resp)


@app.get("/form/{musicId}")
def form_insert(musicId: int, request: Request):
    return fill_form(musicId, request)


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
    return RedirectResponse(
        f"/record/{user}/{musicId}/{difficulty}/{great}/{good}/{bad}/{miss}",
        status_code=status.HTTP_308_PERMANENT_REDIRECT,
    )


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
    cols = [
        "song_name",
        "difficulty",
        "perfect",
        "great",
        "good",
        "bad",
        "miss",
        "time",
    ]
    dataset = []
    for idx, tup in enumerate(recent):
        recent[idx] = list(tup)
        recent[idx] = recent[idx][1:-1]
        time = recent[idx][7]
        recent[idx][7] = strftime("%d %b %Y %H:%M:%S UTC", gmtime(recent[idx][7]))
        dataset.append({"data": recent[idx], "key": f"{time}/{user}"})
    resp = {"cols": cols, "recent": dataset, "request": request}
    return templates.TemplateResponse("recent.html", resp)


@app.get("/record_update/{origin_time}/{origin_user}")
def form_update(origin_time: int, origin_user: str, request: Request):
    info = pjsk.get_record(origin_time, origin_user)
    info["origin_time"] = origin_time
    info["origin_user"] = origin_user
    return fill_form(info["song_id"], request, default=info)


@app.post("/redirect/record_update/{origin_time}/{origin_user}")
def update_record_redirect(
    origin_time: int,
    origin_user: str,
    difficulty: Annotated[str, Form()],
    great: Annotated[int, Form()],
    good: Annotated[int, Form()],
    bad: Annotated[int, Form()],
    miss: Annotated[int, Form()],
    user: Annotated[str, Form()],
):
    return RedirectResponse(
        f"/record/{origin_time}/{origin_user}/{user}/{difficulty}/{great}/{good}/{bad}/{miss}",
        status_code=status.HTTP_308_PERMANENT_REDIRECT,
    )


@app.post(
    "/record/{origin_time}/{origin_user}/{user}/{difficulty}/{great}/{good}/{bad}/{miss}"
)  # temporary solution
@app.put(
    "/record/{origin_time}/{origin_user}/{user}/{difficulty}/{great}/{good}/{bad}/{miss}"
)
def update_record(
    origin_time: int,
    origin_user: str,
    difficulty: str,
    great: int,
    good: int,
    bad: int,
    miss: int,
    user: str,
    request: Request,
):
    song_id = pjsk.get_record(origin_time, origin_user)["song_id"]
    info = pjsk.get_song_info(song_id=song_id, difficulty=difficulty)
    perfect = info["totalNoteCount"] - great - good - bad - miss
    pjsk.update_record(
        difficulty,
        perfect,
        great,
        good,
        bad,
        miss,
        user,
        origin_time,
        origin_user,
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
