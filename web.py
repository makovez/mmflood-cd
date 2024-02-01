import os, json
from mmflood_cd.models import FloodEvent

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import rasterio 
from datetime import datetime
from tqdm import tqdm
import numpy as np
from scipy.stats import pearsonr


app = FastAPI()
templates = Jinja2Templates(directory="templates")
base_path = 'emsr'
# Mount the "emsr" folder as a static folder

with open('emsr/flood_events.json', 'r') as f:
    data = json.loads(f.read())

def temporal_correlation_pearson(series1, series2):
    # Ensure the input arrays have the same length
    assert len(series1) == len(series2), "Input arrays must have the same length"
    
    # Calculate the Pearson correlation coefficient
    correlation_coefficient = np.corrcoef (series1, series2)
    
    return correlation_coefficient

def get_image(path):
    with rasterio.open(path) as src:
        res = src.read(1)
    return res
    


def get_flood_events(root='emsr', preview_pathname='preview_image'):
    events_saved = os.listdir(root)
    flood_events = [FloodEvent(**event) for event in data if event['name'] in events_saved]
    for i, flood_event in tqdm(enumerate(flood_events.copy()), desc="Processing Flood Events", total=len(flood_events.copy())):
        flood_folder = os.path.join(root, flood_event.name)
        mmflood_path = os.path.join(root, flood_event.name, preview_pathname, flood_event.name + '.jpg')
        mmflood_mask =  os.path.join(root, flood_event.name, preview_pathname, 'mask.jpg')


        preview_images_files = [image for image in os.listdir(os.path.join(root, flood_event.name, preview_pathname)) if image.startswith('S1')]
        preview_images_files = sorted(preview_images_files, key=lambda x: datetime.strptime(x.split('_')[4], '%Y%m%dT%H%M%S'), reverse=True) 
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

flood_events = get_flood_events(root=base_path)

print(len(flood_events))
app.mount(f"/emsr", StaticFiles(directory=base_path), name=base_path)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/data", response_class=JSONResponse)
async def get_data():
    return flood_events
