from typing import Optional
import requests
import re

import logging
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class UserInfo(BaseModel):
    name: str
    bio: Optional[str]
    link_fb: Optional[str]
    link_insta: Optional[str]
    link_linkedin: Optional[str]
    id_fb: Optional[str]


class createResponse(BaseModel):
    return_message: str


class UserExists(BaseModel):
    exists: bool


users: dict[str, UserInfo] = dict()

logging.basicConfig(level=logging.INFO)
app = FastAPI()

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logging.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
    ],  # React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/user/create/")
async def create_user(id: str, request: UserInfo) -> createResponse:
    global users
    if not request.name:
        if id in users:
            del users[id]
            logging.info(f"Deleting user {id}")
            return createResponse(return_message=f"User {id} deleted successfully")
        logging.info(f"Id {id} not created")
        return createResponse(return_message=f"User {id} did not create")

    logging.info(f"Creating id: {id}")
    users[id] = request
    return createResponse(return_message=f"User {id} created successfully")


@app.get("/api/user/info/")
async def get_user(id: str) -> UserInfo:
    global users
    id = str(id)
    logging.info(f"Get id: {id}")
    if id not in users:
        raise HTTPException(status_code=404, detail=f"User {id} does not exist")
    user = users[id].model_copy()
    if user.link_fb:
        fb_response = requests.get(user.link_fb, timeout=2)  # 5 seconds timeout
        if fb_response.status_code == 200:
            match = re.search(r'content="fb://profile/(\d+)"', fb_response.text)
            if match:
                user.id_fb = match.group(1)
    return user


@app.get("/api/user/exist/")
async def user_exists(id: str) -> UserExists:
    global users
    id = str(id)
    logging.info(f"User_exists: {id}")
    return UserExists(exists=id in users)


@app.get("/")
def read_root():
    return {"message": "API is working"}
