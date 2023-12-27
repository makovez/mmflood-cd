from mmflood_cd import Shub, Catalog
from mmflood_cd.models import FloodEvent
import json, os

with open('metadata.json', 'r') as file:
    images = json.load(file)

catalog = Catalog('config.yaml')
shub = Shub('config.yaml', root_path='data')

flood_events = []
dates_image = [(7, 7), (30, 7), (60, 7), (90, 7), (120, 7), (340, 7)]

# Now 'data' is a list of dictionaries, and you can access the values as needed
for entry in images:
    flood_event = FloodEvent.model_validate(entry)
    images = catalog.search_all(flood_event, dates_image)
    flood_event.images += images

    for image in images:
        data = shub.get_image(flood_event, image)
        shub.download_image(flood_event, image, data)
    
    flood_events.append(flood_event)
    #for i in days_image:
    # data = shub.get_image(flood_event, previous_days=60, max_range=30)
    # print(geodata.checksum)
    # shub.download_image(geodata.checksum, data)
    # lgeodata.append(geodata)


json_file_path = "flood_events.json"
with open(os.path.join(shub.directory_path, json_file_path), 'w') as json_file:
    json.dump([event.dict() for event in flood_events], json_file)

# file_path = 'metadata.json'
# with open(os.path.join(shub.directory_path, file_path), 'w') as file:
#     json.dump([geodata.dict() for geodata in lgeodata], file, indent=2)
