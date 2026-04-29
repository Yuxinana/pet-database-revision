from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
app = FastAPI()
app.mount('/', StaticFiles(directory='no_exist'), name='static')
