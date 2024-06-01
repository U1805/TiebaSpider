import os
from PIL import Image
from io import BytesIO
import base64
from requests.adapters import HTTPAdapter
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
}


def myrequests(url):
    global HEADERS

    s = requests.Session()
    s.headers = HEADERS
    s.mount("http://", HTTPAdapter(max_retries=3))  # 超时重试3次
    s.mount("https://", HTTPAdapter(max_retries=3))
    res = s.get(url, timeout=(10, 27))  # (connect超时, read超时)
    return res


def getFilename(url, ext=None):
    _, filename = os.path.split(url)
    if ext:
        return filename.split(".")[0] + "." + ext
    return filename.split("?")[0]


def saveImage(data, filename, ext=None):
    if ext:
        with Image.open(BytesIO(data)) as im:
            im.save(filename, "webp", quality=40)
    else:
        with open(filename, "wb") as f:
            f.write(data)


def img2base64(url, quality=40):
    res = myrequests(url)
    with Image.open(BytesIO(res.content)) as im:
        webp_data = BytesIO()
        im.save(webp_data, "webp", quality=quality)
        webp_base64 = base64.b64encode(webp_data.getvalue()).decode("utf-8")
    return "data:image/webp;base64," + webp_base64
