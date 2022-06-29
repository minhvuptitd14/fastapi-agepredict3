from fastapi import FastAPI, File, UploadFile, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from starlette.responses import StreamingResponse, HTMLResponse
import io
import cv2
import numpy as np
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocket

import use_model_class as model
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates/")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def welcome(request: Request):
    return templates.TemplateResponse('appear.html', context={'request': request})

@app.get("/image")
async def image(request: Request):
    return templates.TemplateResponse('image.html', context={'request': request})

@app.post("/upload")
async def upload_and_predict(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.fromstring(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    global im_jpg
    im_jpg = model.response(frame)
    return StreamingResponse(io.BytesIO(im_jpg.tobytes()), media_type="image/jpg")


camera = cv2.VideoCapture(0)
@app.get("/camera") #post
async def request_cam():
    global camera
    async def generate():
        while (True):
            success, frame = camera.read()
            if not success:
                camera.release()
                cv2.destroyAllWindows()
                break
            else:
                buffer = model.response(frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace;boundary=frame",)


