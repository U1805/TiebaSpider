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
import math


COMMENT_POOL = []
COOKIE = ""

TEMPLATE = {
    "louzhubiaoshi": """<div class=louzhubiaoshi_wrap><div class="louzhubiaoshi beMember_fl j_louzhubiaoshi"></div></div>""",
    "floor": """<div class="l_post l_post_bright j_l_post clearfix"> <div class=d_author> %louzhu% <ul class=p_author> <li class=icon> <div class="icon_relative j_user_card"> <a class=p_author_face><img src='%author_face%' class></a> </div> </li> <li class=d_name> <span class="pre_icon_wrap pre_icon_wrap_theme1 d_name_icon"></span> <a class="p_author_name sign_highlight j_user_card vip_red">%author_name%</a> </li> <li class=d_icons> </li> <li class=l_badge style=display:block> <div class=p_badge> <a class="user_badge d_badge_bright d_badge_icon3"> <div class=d_badge_title>%author_badge_title%</div> <div class=d_badge_lv>%author_badge_level%</div> </a> </div> </li> </ul> </div> <div class="d_post_content_main d_post_content_firstfloor" data-author=0> <div class=p_content> <div id=post_content_149757381011 class="d_post_content j_d_post_content"> %content% </div> <div class=user-hide-post-down style=display:none></div> </div> <div class=post-foot-send-gift-container> </div> <div class="core_reply j_lzl_wrapper"> <div class="core_reply_tail clearfix"> <div class=post-tail-wrap> <span class>%ip%</span> <span class=tail-info>%floor%</span> <span class=tail-info>%time%</span> </div> </div> %reply% </div> </div> </div>""",
    "reply_part0": """<div class="j_lzl_container core_reply_wrapper"> <div class="j_lzl_c_b_a core_reply_content"> <ul class=j_lzl_m_w> """,
    "reply_part1": """<li> <a class="j_user_card lzl_p_p"><img src="%avatar%"></a> <div class=lzl_cnt> <a class="at j_user_card vip_red">%username%</a>:&nbsp;<span class=lzl_content_main>%content%</span> <div class=lzl_content_reply><span class="lzl_op_list j_lzl_o_l"></span><span class=lzl_time>%time%</span></div> </div> </li> """,
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


def formatContent(contents, local):
    res = ""
    for element in contents:
        if isinstance(element, str):
            res += element.strip()
        elif isinstance(element, Tag):
            if element.name == "br":
                res += "<br>"
            elif element.name == "img":
                res += (
                    f'<img class=BDE_Image src="{img2base64(element["src"])}">'
                    if local
                    else f'<img class=BDE_Image src="{element["src"]}">'
                )
            elif element.name == "a":
                res += f'<a class="at"> {element.text} </a>'
            else:
                res += element.text
    return res


def getComment(tid, post_id, local) -> list:
    if post_id not in COMMENT_POOL:
        return ""

    result = TEMPLATE["reply_part0"]
    total_page = math.ceil(
        COMMENT_POOL[post_id]["comment_num"] / COMMENT_POOL[post_id]["comment_list_num"]
    )
    for pn in range(1, total_page + 1):
        res = myrequests(
            f"https://tieba.baidu.com/p/comment?tid={tid}&pid={post_id}&pn={pn}"
        )
        soup = BeautifulSoup(res.text, "html.parser")
        for reply in soup.select("li")[:-1]:
            avatar = reply.select(".j_user_card.lzl_p_p img")[0]["src"]
            result += (
                TEMPLATE["reply_part1"]
                .replace("%avatar%", (img2base64(avatar) if local else avatar))
                .replace("%username%", reply.select(".at.j_user_card")[0].text)
                .replace(
                    "%content%",
                    formatContent(reply.select(".lzl_content_main")[0].contents, local),
                )
                .replace("%time%", reply.select(".lzl_time")[0].text)
            )
    result += TEMPLATE["reply_part2"]

    return result


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
        post_res[post_id] = formatContent(post.contents, local)
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

    main_page = soup.select("#pb_content .left_section")[0]

    return main_page, page_title, page_num


def fetchReply(tid, total, progress_callback=None):
    global COMMENT_POOL
    pn = 1
    while pn <= total:
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


def formatPage(tid, page, local=True):
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
        template = template.replace("%reply%", getComment(tid, pid, local))

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
    progress_callback(0)
    with open("script/template.html", "r", encoding="utf-8") as f:
        template_page = f.read()

    template_page = template_page.replace("%html_title%", html_title)
    template_page = template_page.replace(
        "%post_title%", re.sub(r"_.+_百度贴吧$", "", html_title)
    )

    content_res = [None for _ in range(page_num)]
    content_res[0] = formatPage(tid, page, local)

    # 信号量，用来限制线程数
    pool_sema = threading.BoundedSemaphore(max_connections)
    current_done = 1
    progress_callback(current_done / page_num * 100)

    def f(i):
        nonlocal current_done
        page, _, _ = fetchPage(tid, i)
        content_res[i - 1] = formatPage(tid, page, local)
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


tid = "9031871179"
cookie = 'XFI=59b581f0-1e4c-11ef-9f81-51eca6c68761; XFCS=170681D66D53D28732C04DE4B30D564193D7A9331896D54F1B12DAF595309BD8; XFT=IbA70aWizXryT+JYpJDP7xCyiYcwKyzRx78AWTYt1J8=; BAIDUID=0E63814A00E7DB51A30C2558895E04CA:FG=1; BAIDUID_BFESS=0E63814A00E7DB51A30C2558895E04CA:FG=1; wise_device=0; BAIDU_WISE_UID=wapp_1717049868602_474; USER_JUMP=-1; Hm_lvt_98b9d8c2fd6608d564bf2ac2ae642948=1717049870; ZFY=Y7qprCUlMAODanPvxS9CJnem:BvizX8EHibBqvrM3:BAQ:C; arialoadData=false; st_key_id=17; tb_as_data=bce5498df1d99b5469c29f963b4069d48fa7fc59ec85833ff918ae9d60af43791465cfa5137dfc5452d6e371d54272a3105a24b18e81526c2c28d4b4f7842be7bbd1733bcecf2a34020a062adb1f2fe05a296c9ea033d3a6bc53dd3f9fffa67703aa2dbb4b4c8b7a4fce397ae3b52de1; Hm_lpvt_98b9d8c2fd6608d564bf2ac2ae642948=1717049874; BA_HECTOR=250l24012185250g2lah81a1egcuj41j5g6gi1u; ab_sr=1.0.1_NTBiZjdhYTk5YWVlZTY5MjFhZWM5ZmNlOTU5ZDYwMzk2MjBlNmQ0NmIxNzFlYmU0NTEzMDBiZmU4OWQ4OTJhNWY3MWJlYTAyYzI5NDgwNzNiNTQ2Mzk4ODczMDYzOTNhM2VjZmQ1NDIyOWIyOGIwNzU1M2E5MjI1OTE4ZDg2ZTIxNGRhNGEzNTczNGZmNDkzMzVmNzQzM2JjNjRmZWFlNTU3OWVkNjY0ZTY0NWU2MmFkZTM5MmJjYTVkMmNlMmU5NDg2ZWNmODU5Y2JmNWQzODVhZDdkMzc3MTM3NmZlYzM=; st_data=818240818db3b08d63fea0b54d5ccc59a3bb7c27ceb2e17b8235ade834d1c8be8f5c955f52270a0266c962c1d04f4fd726e3df8e03a6a3018d1dd2ddb22d3e0dc41ba445ad2094d276e6c68bac8da8f12de8d4f0228d9f9a5461a9526ef9543654f0bf39b2c931dbb88e640be7548116165e422753e5a420e0a2573729f859ef681fe861991a527accc1d3c6a6301acc708eaae793fc311d79212feaca488d3d; st_sign=efe47fc4; RT="z=1&dm=baidu.com&si=04b4184f-f239-4c7c-b97b-73596d97f3f1&ss=lwsrsfwy&sl=5&tt=enx9&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&r=8za4cxbqh&ul=3dog0"'
run(tid, cookie, True, 10, print, print)
