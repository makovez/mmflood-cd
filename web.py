import os, json
from mmflood_cd.models import FloodEvent

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Mount the "emsr" folder as a static folder
app.mount("/emsr", StaticFiles(directory="emsr"), name="emsr")

with open('flood_events-2.json', 'r') as f:
    data = json.loads(f.read())


def get_flood_events(root='emsr', preview_pathname='preview_image'):
    events_saved = os.listdir(root)
    flood_events = [FloodEvent(**event) for event in data if event['name'] in events_saved]

    for i, flood_event in enumerate(flood_events.copy()):
        mmflood_path = os.path.join(root, flood_event.name, preview_pathname, flood_event.name + '.jpg')
        mmflood_mask =  os.path.join(root, flood_event.name, preview_pathname, 'mask.jpg')

        preview_images_files = [image for image in os.listdir(os.path.join(root, flood_event.name, preview_pathname)) if image.startswith('s1')]
        preview_images_path = [os.path.join(root, flood_event.name, preview_pathname, image) for image in preview_images_files]

        flood_events[i].preview_image = mmflood_path
        flood_events[i].preview_mask = mmflood_mask

        img_ids = [img.id for img in flood_events[i].images]
        for v, image_path in enumerate(preview_images_files):
            img_id = image_path.replace('.jpg', '').upper()
            if img_id in img_ids:
                idx = img_ids.index(img_id)
                flood_events[i].images[idx].preview_image = preview_images_path[v]


    return [event.model_dump() for event in flood_events]

flood_events = get_flood_events()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/data", response_class=JSONResponse)
async def get_data():
    return flood_events
