import requests
import random
from pathlib import Path
import os
from dotenv import load_dotenv
from mastodon import Mastodon

load_dotenv()

#   Set up Mastodon
mastodon = Mastodon(
    access_token = os.getenv("TOKEN_SECRET"),
    api_base_url = 'https://wraggebots.net/',
    version_check_mode = "none"
)

def get_total_results(params):
    lparams = params.copy()
    lparams['rows'] = 0
    response = requests.get('https://api.prov.vic.gov.au/search/select', params=params)
    data = response.json()
    return data['response']['numFound']

def get_random_image():
    params = {
        "q": 'iiif-manifest:[* TO *] AND record_form:"Photograph or Image"',
        "rows": 1
    }
    total = get_total_results(params)
    params["start"] = random.randrange(0, total)
    response = requests.get('https://api.prov.vic.gov.au/search/select', params=params)
    return response.json()["response"]["docs"][0]

def download_image(image_data):
    url = image_data["iiif-thumbnail"].replace("!200,200", "!1000,1000")
    response = requests.get(url)
    image_file = f"{image_data['_id']}.jpg"
    Path(image_file).write_bytes(response.content)
    media = mastodon.media_post(image_file, description=f"Image from the collection of Public Record Office Victoria: {image_data.get('description.aggregate')}")
    Path(image_file).unlink()
    return media

def prepare_message(image_data):
    description = []
    parent = []
    for field in ["title", "description.aggregate"]:
        if value := image_data.get(field):
            description.append(value)
    for field in ["is_part_of_series.id", "is_part_of_series.title"]:
        if value := image_data.get(field):
            parent.append(value[0])
    url = f"https://prov.vic.gov.au/archive/{image_data['_id']}"
    return f"{' – '.join(description)} – part of {', '.join(parent)}. {url}"

def toot_random_image():
    image_data = get_random_image()
    message = prepare_message(image_data)
    media = download_image(image_data)
    print(message)
    mastodon.status_post(message, media_ids=media, visibility="public")

toot_random_image()