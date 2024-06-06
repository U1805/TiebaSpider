from bs4 import BeautifulSoup
import json
from utils import myrequests


BASE_URL = "https://tieba.baidu.com/p/"
COMMENT_POOL = []


def fetchPage(tid, pn=1):
    global COMMENT_POOL
    page_title = None
    page_num = None

    res = myrequests(BASE_URL + f"{tid}?pn={pn}")
    soup = BeautifulSoup(res.text, "html.parser")

    if pn == 1:
        page_title = soup.title.text
        page_num = int(soup.select(".l_reply_num .red")[1].text)
        print("title: " + page_title)
        print("page num: " + str(page_num))

    main_page = soup.select("#pb_content .left_section")[0]

    return main_page, page_title, page_num


def fetchJsonReply(tid, total, progress_callback=None):
    global COMMENT_POOL
    pn = 1
    while pn <= total:
        try:
            res = myrequests(BASE_URL + f"totalComment?tid={tid}&pn={pn}&see_lz=0")
            comments = json.loads(res.text)
            COMMENT_POOL = dict(COMMENT_POOL, **comments["data"]["comment_list"])
            progress_callback(pn / total * 100)
            pn += 1
        except:
            # 评论页数比显示页数少
            break
    print(f"get replies {pn} pages")


def fetchHtmlReply(tid, pid, pn):
    res = myrequests(BASE_URL + f"comment?tid={tid}&pid={pid}&pn={pn}")
    soup = BeautifulSoup(res.text, "html.parser")
    return soup.select("li")[:-1]
