"""
# requests 方案过快会触发安全验证
# 目前没有找到解决方法：https://github.com/BaiduSpider/BaiduSpider/issues
"""

import os
from PIL import Image
from io import BytesIO
import base64
from requests.adapters import HTTPAdapter
import requests
from template import AGENTS

import time
import random

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
}


import requests
from bs4 import BeautifulSoup
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class proxy_pool:
    def __init__(self, btn_callback=print, process_callback=print):
        global logger
        self.proxy_web = "https://www.zdaye.com/free"
        self.logger = logger
        self.proxies = None
        self.btn_callback = btn_callback
        self.process_callback = process_callback

    def get_random_user_agent(self):
        return random.choice(AGENTS)

    def get_random_proxy(self):
        if self.proxies:
            return random.choice(self.proxies)
        else:
            self.proxies = self._get_free_proxies(self.proxy_web, 2)
            return random.choice(self.proxies)

    def _get_free_proxies(self, base_url, num_pages=5):
        """
        Author: ZhangYuetao
        GitHub: https://github.com/VerySeriousMan/Crawler
        """

        all_proxies = []
        self.btn_callback("Updating proxies...")

        for page in range(1, num_pages + 1):
            url = f"{base_url}/{page}/"
            try:
                logger.info(f"Fetching proxies from {url}")
                response = requests.get(url, headers=HEADERS)
                response.raise_for_status()

                html_content = response.text
                soup = BeautifulSoup(html_content, "html.parser")

                # 根据网页结构，找到包含IP的表格
                proxy_table = soup.find("table", attrs={"id": "ipc"})
                if not proxy_table:
                    logger.error("Proxy table not found on page {page}.")
                    continue

                # 提取表格中的所有行
                rows = proxy_table.find_all("tr")

                # 跳过表头，从第二行开始
                proxies = []
                for row in rows[1:]:
                    cols = row.find_all("td")
                    if len(cols) > 1:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        proxies.append(f"{ip}:{port}")

                logger.info(f"Found proxies on page {page}: {proxies}")
                all_proxies.extend(proxies)
            except Exception as e:
                logger.error(f"Failed to fetch proxies from {url}: {e}")
                continue
            self.process_callback(page / num_pages * 100)

        return all_proxies


pool_instance = proxy_pool()


def update_pool_instance(new_instance):
    global pool_instance
    pool_instance = new_instance


def myrequests(url):
    global HEADERS, pool_instance

    HEADERS["User-Agent"] = pool_instance.get_random_user_agent()
    proxy = {"http": pool_instance.get_random_proxy()}

    # 素质睡眠
    time.sleep(random.uniform(1, 5))  # 随机延时，避免请求过于频繁

    s = requests.Session()
    s.headers = HEADERS
    s.proxies = proxy
    s.stream = True
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
