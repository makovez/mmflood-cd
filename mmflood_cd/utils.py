from datetime import datetime, timedelta
from mmflood_cd.models import FloodEvent, ImageDate
from datetime import datetime

import pyproj, os, json


def generate_date_range(start_date_str, previous_days=30, max_range_before=7, max_range_after = 7):
    # Convert the input date string to a datetime object
    format_date = "%Y-%m-%dT%H:%M:%SZ" if 'Z' in start_date_str else "%Y-%m-%dT%H:%M:%S"
    start_date = datetime.strptime(start_date_str, format_date)

    # Position at 0 
    at_time = start_date - timedelta(days=previous_days)

    # Calculate the start and end dates within the specified range
    start_range = at_time - timedelta(days=max_range_before)
    end_range = at_time + timedelta(days=max_range_after)

    # Format the dates in the required format
    start_date_formatted = start_range.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date_formatted = end_range.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return ImageDate(start_date=start_date_formatted, end_date=end_date_formatted)


def today():
    # Get the current timestamp as a datetime object
    current_time = datetime.now()

    # Convert the datetime object to a string
    current_time_str = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    return current_time_str



def get_width_height(flood_data: FloodEvent, resolution = 10):

    #left=-1.0955564400233835, bottom=41.72942461192168, right=-1.0246875, top=41.800414224444346

    # Convert bounding box coordinates to UTM projection
    utm_zone = int((flood_data.left + flood_data.right) // 6) + 31  # UTM zone calculation for WGS 84
    utm_crs = f'+proj=utm +zone={utm_zone} +ellps=WGS84 +datum=WGS84 +units=m +no_defs'
    wgs84_crs = 'EPSG:4326'
    transformer = pyproj.Transformer.from_crs(wgs84_crs, utm_crs, always_xy=True)
    minx, miny = transformer.transform(flood_data.left, flood_data.bottom)
    maxx, maxy = transformer.transform(flood_data.right, flood_data.top)

    # Calculate width and height in pixels
    width = int((maxx - minx) / resolution)
    height = int((maxy - miny) / resolution)

    return width, height


def get_evalscript():
    with open('mmflood_cd/evalscript.js') as f:
        data = f.read()
    
    return data

def get_flood_events(root='emsr', preview_pathname='preview_image'):
    
    with open('flood_events.json', 'r') as f:
        data = json.loads(f.read())
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


    return [event for event in flood_events]
