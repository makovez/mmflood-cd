from mmflood_cd import Shub
from mmflood_cd.models import GeoData
import json, os

with open('metadata.json', 'r') as file:
    images = json.load(file)

shub = Shub('config.yaml', root_path='data')

lgeodata = []
days_image = [(30, 7), (60, 7), (120, 7), (240, 7)]
# Now 'data' is a list of dictionaries, and you can access the values as needed
for entry in images[:10]:
    geodata = GeoData.parse_obj(entry)
    #for i in days_image:
    data = shub.get_image(geodata, previous_days=60, max_range=30)
    print(geodata.checksum)
    shub.download_image(geodata.checksum, data)
    lgeodata.append(geodata)


file_path = 'metadata.json'
with open(os.path.join(shub.directory_path, file_path), 'w') as file:
    json.dump([geodata.dict() for geodata in lgeodata], file, indent=2)
