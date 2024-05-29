from datetime import datetime
import requests
from bs4 import BeautifulSoup, Tag
import json
import re
import os
from PIL import Image
from io import BytesIO
import base64
import threading
from requests.adapters import HTTPAdapter


COMMENT_POOL = []
COOKIE = ""

TEMPLATE = {
    "louzhubiaoshi": """<div class=louzhubiaoshi_wrap><div class="louzhubiaoshi beMember_fl j_louzhubiaoshi"></div></div>""",
    "floor": """<div class="l_post l_post_bright j_l_post clearfix"> <div class=d_author> %louzhu% <ul class=p_author> <li class=icon> <div class="icon_relative j_user_card"> <a class=p_author_face><img src='%author_face%' class></a> </div> </li> <li class=d_name> <span class="pre_icon_wrap pre_icon_wrap_theme1 d_name_icon"></span> <a class="p_author_name sign_highlight j_user_card vip_red">%author_name%</a> </li> <li class=d_icons> </li> <li class=l_badge style=display:block> <div class=p_badge> <a class="user_badge d_badge_bright d_badge_icon3"> <div class=d_badge_title>%author_badge_title%</div> <div class=d_badge_lv>%author_badge_level%</div> </a> </div> </li> </ul> </div> <div class="d_post_content_main d_post_content_firstfloor" data-author=0> <div class=p_content> <div id=post_content_149757381011 class="d_post_content j_d_post_content"> %content% </div> <div class=user-hide-post-down style=display:none></div> </div> <div class=post-foot-send-gift-container> </div> <div class="core_reply j_lzl_wrapper"> <div class="core_reply_tail clearfix"> <div class=post-tail-wrap> <span class>%ip%</span> <span class=tail-info>%floor%</span> <span class=tail-info>%time%</span> </div> </div> %reply% </div> </div> </div>""",
    "reply_part0": """<div class="j_lzl_container core_reply_wrapper"> <div class="j_lzl_c_b_a core_reply_content"> <ul class=j_lzl_m_w> """,
    "reply_part1": """<li> <div class=lzl_cnt> <a class="at j_user_card vip_red">%username%</a>:&nbsp;<span class=lzl_content_main>%content%</span> <div class=lzl_content_reply><span class="lzl_op_list j_lzl_o_l"></span><span class=lzl_time>%time%</span></div> </div> </li> """,
    "reply_part2": """</ul> </div> </div> """,
}


def myrequests(url):
    global COOKIE

    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Cookie": COOKIE,
    }

    s = requests.Session()
    s.mount("http://", HTTPAdapter(max_retries=3))  # 超时重试3次
    s.mount("https://", HTTPAdapter(max_retries=3))
    res = s.get(url, timeout=(10, 27), headers=header)  # (connect超时, read超时)
    return res


def getFilename(url, ext=None):
    _, filename = os.path.split(url)
    if ext:
        return filename.split(".")[0] + "." + ext
    return filename.split("?")[0]


def saveFile(data, filename, ext=None):
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
    return " data:image/webp;base64," + webp_base64


def getComment(post_id: str) -> list:
    if post_id not in COMMENT_POOL:
        return ""

    res = TEMPLATE["reply_part0"]
    post_comment = COMMENT_POOL[post_id]
    # comment_num = post_comment["comment_list_num"]
    for comment in post_comment["comment_info"]:
        # print(comment["username"]) #注册名字
        res += (
            TEMPLATE["reply_part1"]
            .replace("%username%", comment["show_nickname"])
            .replace(
                "%content%", re.sub(r"<a[^>]*>(.*?)</a>", r"\1", comment["content"])
            )
            .replace(
                "%time%",
                datetime.fromtimestamp(comment["now_time"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            )
        )
    res += TEMPLATE["reply_part2"]
    return res


def getTitle(page) -> str:
    return page.select(".core_title_txt")[0]["title"]


def getAuthors(page, local=True) -> list:
    authors = page.select(".d_author")
    authors_res = []
    for author in authors:
        is_louzhu = len(author.select(".louzhubiaoshi_wrap"))
        author_face = author.select(".p_author .p_author_face img")[0]
        # print(author_face["username"]) # 注册名

        if local:
            author_face = (
                img2base64(author_face["data-tb-lazyload"])
                if author_face.has_attr("data-tb-lazyload")
                else img2base64(author_face["src"])
            )
        else:
            author_face = (
                author_face["data-tb-lazyload"]
                if author_face.has_attr("data-tb-lazyload")
                else author_face["src"]
            )

        authors_res.append(
            {
                "is_louzhu": is_louzhu == 1,
                "author_face": author_face,
                "author_name": author.select(".p_author .p_author_name")[0].text,
                "author_badge_title": author.select(".p_author .d_badge_title")[0].text,
                "author_badge_level": author.select(".p_author .d_badge_lv")[0].text,
            }
        )
    return authors_res


def getTails(page) -> list:
    info_res = []
    for tail_info in page.select(".post-tail-wrap"):
        info_res.append(
            {
                "ip": tail_info.findChild().text,
                "floor": tail_info.select(".tail-info")[1].text,
                "time": tail_info.select(".tail-info")[2].text,
            }
        )
    return info_res


def getContent(page, local=True) -> dict:
    post_res = {}
    for post in page.select(".d_post_content.j_d_post_content"):
        post_id = post["id"].replace("post_content_", "")
        post_res[post_id] = ""
        for element in post.contents:
            if isinstance(element, str):
                post_res[post_id] += element.strip()
            elif isinstance(element, Tag):
                if element.name == "br":
                    post_res[post_id] += "<br>"
                elif element.name == "img":
                    post_res[post_id] += (
                        f'<img class=BDE_Image src="{img2base64(element["src"])}">'
                        if local
                        else f'<img class=BDE_Image src="{element["src"]}">'
                    )
    return post_res


def fetchPage(tid, pn=1):
    global COMMENT_POOL
    page_title = None
    page_num = None

    res = myrequests(f"https://tieba.baidu.com/p/{tid}?pn={pn}")
    soup = BeautifulSoup(res.text, "html.parser")

    if pn == 1:
        page_title = soup.title.text
        try:
            page_num = int(soup.select(".l_reply_num .red")[1].text)
        except:
            raise (Exception("❌ Cookie 失效"))
        print("title: " + page_title)
        print("page num: " + str(page_num))

    # print(f"crawling page {pn}...")
    main_page = soup.select("#pb_content .left_section")[0]

    return main_page, page_title, page_num


def fetchReply(tid, total, progress_callback):
    global COMMENT_POOL
    pn = 1
    while True:
        try:
            res = myrequests(
                f"https://tieba.baidu.com/p/totalComment?tid={tid}&pn={pn}&see_lz=0"
            )
            comments = json.loads(res.text)
            COMMENT_POOL = dict(COMMENT_POOL, **comments["data"]["comment_list"])
            progress_callback(pn / total * 100)
            pn += 1
        except:
            # 评论页数比显示页数少
            break
    print(f"get replies {pn} pages")


def formatPage(page, local=True):
    authors = getAuthors(page, local)
    contents = getContent(page, local)
    tails = getTails(page)
    res = ""
    for author, pid, content, tail in zip(
        authors, contents.keys(), contents.values(), tails
    ):
        template = TEMPLATE["floor"]
        if author["is_louzhu"]:
            template = template.replace("%louzhu%", TEMPLATE["louzhubiaoshi"])
        else:
            template = template.replace("%louzhu%", "")
        template = template.replace("%author_face%", author["author_face"])
        template = template.replace("%author_name%", author["author_name"])
        template = template.replace(
            "%author_badge_title%", author["author_badge_title"]
        )
        template = template.replace(
            "%author_badge_level%", author["author_badge_level"]
        )

        template = template.replace("%content%", content)

        template = template.replace("%ip%", tail["ip"])
        template = template.replace("%floor%", tail["floor"])
        template = template.replace("%time%", tail["time"])
        template = template.replace("%reply%", getComment(pid))

        res += template
    return res


def run(tid, cookie1, local, max_connections, progress_callback, button_callback):
    global COOKIE

    if tid == "" or cookie1 == "":
        return

    COOKIE = cookie1

    page, html_title, page_num = fetchPage(tid)
    button_callback("Downloading replies...")
    fetchReply(tid, page_num, progress_callback)

    button_callback("Downloading pages...")
    with open("script/template.html", "r", encoding="utf-8") as f:
        template_page = f.read()

    template_page = template_page.replace("%html_title%", html_title)
    template_page = template_page.replace(
        "%post_title%", re.sub(r"_.+_百度贴吧$", "", html_title)
    )

    content_res = [None for _ in range(page_num)]
    content_res[0] = formatPage(page, local)

    # 信号量，用来限制线程数
    pool_sema = threading.BoundedSemaphore(max_connections)
    current_done = 1

    def f(i):
        nonlocal current_done
        page, _, _ = fetchPage(tid, i)
        content_res[i - 1] = formatPage(page, local)
        current_done += 1
        progress_callback(current_done / page_num * 100)
        pool_sema.release()

    thread_list = []
    for i in range(2, page_num + 1):
        pool_sema.acquire()
        thread = threading.Thread(target=f, args=(i,))
        thread.start()
        thread_list.append(thread)

    for t in thread_list:
        t.join()

    t = template_page.replace("%content%", "\n".join(content_res))
    with open(f"{tid} - {html_title}.html", "w", encoding="utf-8") as f:
        f.write(t)

    button_callback("🚀Start!")


# run(
#     "8892250740",
#     'XFI=0c84e0b0-1dac-11ef-9290-195f5c0b14c9; XFCS=5C18AA3D0F7CBB04CF07AB2E045E29E842DE3B2F0B5D1C0F24E9B903DFA00BDD; XFT=hHBK/DFjirFlN3Kzxs4ZyJ7qQ37GVMqYowTYkg+cr/o=; BAIDUID=A157A8003C389B8FFB60F697794B3274:FG=1; BAIDUID_BFESS=A157A8003C389B8FFB60F697794B3274:FG=1; wise_device=0; BAIDU_WISE_UID=wapp_1716980638876_966; USER_JUMP=-1; Hm_lvt_98b9d8c2fd6608d564bf2ac2ae642948=1716980645; ZFY=b874xSaw8FCfFNzZI7UPNLW1HgaHknudjSnsEGLIvp8:C; st_key_id=17; tb_as_data=9aa838e3a099b5cd74d4e173b5f7303dfad7aea5c35885bdd53dff47402efb884f96664e6d50efbf621ab1f6083acc2cdae610cd9cf0e9cad5b162a16fad8d912a9e2adb3e6d3bc823f83a186339b52ab38a5f679fc8880bfc2be70604ce715b538e100c86de26d0856b3435be720a66; Hm_lpvt_98b9d8c2fd6608d564bf2ac2ae642948=1716981025; BA_HECTOR=2l8k80a004840h80ag0gag057tf3va1j5e3911u; ab_sr=1.0.1_Y2JhYzIzNmI0NDcyMzJiYzI2OTA0YTUwZjhiNjNmMmYxOWE5ZWViMzU4NWYyY2MxMzAwODVmMGMyODU2MThkODhhNmZmMzQwOWQ3MTM4YTZiOGJjNmRlYmIyZTY5MTZjYTA4NjM0NjZlNmUzNzk5ZTg3YTZjNjhmN2JkOWQ1YjNmYTY4ZGUwYzEwODk3ZWJmMTFjM2NmNzVjNjM3MTcwNDgwOGVjNjkxYjY3MDg4YjgwOTNmZjMzZjM3MGY4MWQ0NmQ3Njg5MWYyYzU2YWNlODQ3YTczNzcyOWE4ZGUxMWY=; st_data=818240818db3b08d63fea0b54d5ccc59a3bb7c27ceb2e17b8235ade834d1c8be8f5c955f52270a0266c962c1d04f4fd7078f1994b92758323b0672d98fba3f4fc13cc0032e02b59ab0443a4f9a9700033185934658d8ff543f7749a58fdd153c4216e3c064a555b20235ec19ae12bd6e2deae6e338eb109f6544eb0344620b315515f3bb0d80d5b2f5fccab0f97955357d354285af3d319bcbd57bea110bcd40; st_sign=1693e512; RT="z=1&dm=baidu.com&si=04b4184f-f239-4c7c-b97b-73596d97f3f1&ss=lwrpfwce&sl=4&tt=34k&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&r=comu8z989&ul=racw"',
#     False,
#     10,
#     None,
# )
