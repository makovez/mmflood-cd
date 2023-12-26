from datetime import datetime, timedelta
from mmflood_cd.models import FloodEvent, ImageDate
from datetime import datetime

import pyproj


def generate_date_range(start_date_str, previous_days=30, max_range=7):
    # Convert the input date string to a datetime object
    format_date = "%Y-%m-%dT%H:%M:%SZ" if 'Z' in start_date_str else "%Y-%m-%dT%H:%M:%S"
    start_date = datetime.strptime(start_date_str, format_date)

    # Subtract 1 month from the start date
    one_month_ago = start_date - timedelta(days=previous_days)

    # Calculate the start and end dates within the specified range
    start_range = one_month_ago - timedelta(days=max_range)
    end_range = one_month_ago + timedelta(days=max_range)

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


