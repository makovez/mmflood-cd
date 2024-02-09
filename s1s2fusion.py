from mmflood_cd import Shub, Catalog
from mmflood_cd.models import FloodEvent
import json, os, sys
from datetime import datetime
from typing import List
from mmflood_cd.models import SARImage, ImageDate, S1S2Fusion
from tqdm import tqdm

from datetime import datetime, timedelta
from collections import defaultdict


with open('metadata.json', 'r') as file:
    images = json.load(file)

catalog = Catalog('config/config.yaml')
shub = Shub('config/config.yaml', fixed_path='s12_fusion')
json_file_name = "flood_events.json"
json_file_path = os.path.join(shub.directory_path, json_file_name)
s12_fusion_images = []
dates_image = [(0, 120, 0)]
first_date_shub =  datetime(2016, 11, 1)  # Using the first day of October 2016 for comparison


if os.path.exists(json_file_path):
    with open(json_file_path, 'r+') as json_file:
        s12_fusion_images = [S1S2Fusion(**event) for event in json.load(json_file)] # Load flood events if exists

def get_days_before_availability(flood_event: FloodEvent, range_days=120):
    # Convert the date string to a datetime object
    date = datetime.fromisoformat(flood_event.event_date)

    # Check if the date is after October 2016
    if date <= first_date_shub:
        delta = first_date_shub - date

        # Return the number of days
        return -abs(delta.days), 0, range_days
    return 0, range_days, 0


def filter_and_sort_dates(s1_images: List[SARImage], s2_images: List[ImageDate]):
    pairs = []
    dates_pairs = defaultdict(list)

    # Iterate over each pair of dates from the two lists
    for s1 in s1_images:
        for s2 in s2_images:
            # Convert date strings to datetime objects
            dt1 = datetime.strptime(s1.acquisition_date, "%Y-%m-%dT%H:%M:%SZ")
            dt2 = datetime.strptime(s2.start_date, "%Y-%m-%dT%H:%M:%SZ")

            # Calculate the difference in days between the two dates
            diff = abs((dt2 - dt1).days)

            # If the difference is at most 3 days, add the pair to the list
            if diff <= 3:
                pairs.append((s1, s2))
                dates_pairs[diff].append((dt1, dt2))

    # Sort the pairs based on the smallest difference in dates
    sorted_pairs = sorted(pairs, key=lambda x: abs((datetime.strptime(x[1].start_date, "%Y-%m-%dT%H:%M:%SZ") - datetime.strptime(x[0].acquisition_date, "%Y-%m-%dT%H:%M:%SZ")).days))

    return sorted_pairs


if not shub.is_processing_units_ok():
    print('Units finished')
    sys.exit(0)


for entry in tqdm(images):
    s12_fusion = S1S2Fusion.model_validate(entry)
    if any(s12_fusion.name == event.name for event in s12_fusion_images):
        continue
    
    previous_days, max_range_before, max_range_after = get_days_before_availability(s12_fusion)
    
    s2_stats = shub.get_stats_l2a(s12_fusion, previous_days=previous_days, max_range_before=max_range_before, max_range_after=max_range_after)

    if not s2_stats: # Skip if not s2 images with enough water and without clouds
        continue
    
    images_s1 = catalog.search(s12_fusion, previous_days=previous_days, max_range_before=max_range_before, max_range_after=max_range_after, all_prods=True)

    s1s2_pairs = filter_and_sort_dates(images_s1, s2_stats) 
    for s1_image, s2_date in s1s2_pairs:
        # Search and download s2 image
        s2_image = catalog.search(s12_fusion, image_date=s2_date, prod_type='sentinel-2-l2a')
        if not s2_image:
            continue
        data = shub.get_image(s12_fusion, s2_image, prod_type='sentinel-2-l2a')
        shub.download_image(s12_fusion, s2_image, data, prod_type='sentinel-2-l2a')
        s12_fusion.s2_image = s2_image
        
        # Download s1 image
        data = shub.get_image(s12_fusion, s1_image)
        shub.download_image(s12_fusion, s1_image, data)
        s12_fusion.s1_image = s1_image
        break

    if not shub.is_processing_units_ok():
        break

    s12_fusion_images.append(s12_fusion)
    with open(json_file_path, 'w') as json_file:
        json.dump([event.model_dump() for event in s12_fusion_images], json_file, indent=4)


# file_path = 'metadata.json'
# with open(os.path.join(shub.directory_path, file_path), 'w') as file:
#     json.dump([geodata.dict() for geodata in lgeodata], file, indent=2)
