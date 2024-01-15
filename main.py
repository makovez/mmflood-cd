from mmflood_cd import Shub, Catalog
from mmflood_cd.models import FloodEvent
import json, os, sys

with open('metadata.json', 'r') as file:
    images = json.load(file)

catalog = Catalog('config.yaml')
shub = Shub('config.yaml', fixed_path='EMSR-2')
json_file_name = "flood_events.json"
json_file_path = os.path.join(shub.directory_path, json_file_name)
flood_events = []
dates_image = [(0, 0, 7), (30, 7), (60, 7), (90, 7), (120, 7), (340, 7)]

if os.path.exists(json_file_path):
    with open(json_file_path, 'r+') as json_file:
        flood_events = [FloodEvent(**event) for event in json.load(json_file)] # Load flood events if exists

if not shub.is_processing_units_ok():
    print('Units finished')
    sys.exit(0)

# Now 'data' is a list of dictionaries, and you can access the values as needed
for entry in images:
    flood_event = FloodEvent.model_validate(entry)
    if any(flood_event.name == event.name for event in flood_events):
        print(f'Skip flood event: {flood_event.name}')
        continue

    images = catalog.search_all(flood_event, dates_image)
    # flood_event.images += images

    for image in images:
        data = shub.get_image(flood_event, image)
        if data:
            shub.download_image(flood_event, image, data)
            flood_event.images.append(image)

    if not shub.is_processing_units_ok():
        print('Units finished')
        break
    flood_events.append(flood_event)
    #for i in days_image:
    # data = shub.get_image(flood_event, previous_days=60, max_range=30)
    # print(geodata.checksum)
    # shub.download_image(geodata.checksum, data)
    # lgeodata.append(geodata)
    
    with open(json_file_path, 'w') as json_file:
        json.dump([event.model_dump() for event in flood_events], json_file, indent=4)

    print(f"Processed -> {flood_event.name}")

# file_path = 'metadata.json'
# with open(os.path.join(shub.directory_path, file_path), 'w') as file:
#     json.dump([geodata.dict() for geodata in lgeodata], file, indent=2)
