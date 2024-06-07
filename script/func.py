from template import TEMPLATE
from datetime import datetime

import aiotieba
from aiotieba.api._classdef.contents import *
from aiotieba.api.get_posts._classdef import *

from PIL import Image
from io import BytesIO
import base64


async def img2base64(url, local=True, client=None, quality=40):
    if not local:
        return url

    res = await client.get_image_bytes(url)
    with Image.open(BytesIO(res)) as im:
        webp_data = BytesIO()
        im.save(webp_data, "webp", quality=quality)
        webp_base64 = base64.b64encode(webp_data.getvalue()).decode("utf-8")
    return "data:image/webp;base64," + webp_base64


async def formatContent(contents, local, client):
    res = ""
    for element in contents:
        if isinstance(element, FragText):
            res += element.text.replace("\n", "<br>").strip()
        elif isinstance(element, FragEmoji):
            if element.id == "image_emoticon":
                element.id = "image_emoticon1"
            emoji = f"https://tb2.bdstatic.com/tb/editor/images/client/{element.id}.png"
            res += f'<img class=BDE_Image src="{await img2base64(emoji, local, client)}">'
        elif isinstance(element, FragImage_p):
            res += f'<img class=BDE_Image src="{await img2base64(element.src, local, client)}">'
        elif isinstance(element, FragAt_p):
            at = await client.get_user_info(element.user_id)
            res += f'<a class="at" href="http://tb.himg.baidu.com/sys/portraith/item/{at.portrait}"> {element.text} </a>'
        else:
            res += element.text
    return res


async def parsePost(post, local, client):
    author = {
        "author_name": post.user.show_name,
        "author_face": await img2base64(
            "http://tb.himg.baidu.com/sys/portraith/item/" + post.user.portrait,
            local, client
        ),
        "author_page": "https://tieba.baidu.com/home/main?id=" + post.user.portrait,
        "author_level": str(post.user.level),
        "content": await formatContent(post.contents, local, client),
        "ip": "IP属地:" + post.user.ip if hasattr(post.user, "ip") else "",
        "floor": str(post.floor) + " 楼",
        "time": datetime.strftime(
            datetime.fromtimestamp(post.create_time), "%Y-%m-%d %H:%M:%S"
        ),
    }
    return author


async def run(tid, local, progress_callback, button_callback):
    button_callback("Downloading pages...")
    progress_callback(0)

    async with aiotieba.Client() as client:
        posts = await client.get_posts(tid, 1)
        thread_name = posts.thread.fname
        thread_title = posts.thread.title
        total_page = posts.page.total_page

        result = ""

        for pn in range(1, total_page + 1):
            button_callback(f"Download page {pn} / {total_page}")

            if pn != 1:
                posts = await client.get_posts(tid, pn)

            for i in range(len(posts)):
                post = posts[i]

                template = TEMPLATE["floor"]
                if post.is_thread_author:
                    template = template.replace("%louzhu%", TEMPLATE["louzhubiaoshi"])
                else:
                    template = template.replace("%louzhu%", "")

                author = await parsePost(post, local, client)

                template = template.replace("%author_face%", author["author_face"])
                template = template.replace("%author_name%", author["author_name"])
                template = template.replace("%author_page%", author["author_page"])
                template = template.replace("%badge_level%", author["author_level"])
                template = template.replace("%content%", author["content"])
                template = template.replace("%ip%", author["ip"])
                template = template.replace("%floor%", author["floor"])
                template = template.replace("%time%", author["time"])

                comments = await client.get_comments(tid, post.pid)
                if comments:
                    comments_result = TEMPLATE["reply_part0"]
                    for comment in comments:
                        author = await parsePost(comment, local, client)

                        template2 = TEMPLATE["reply_part1"]
                        template2 = template2.replace("%avatar%", author["author_face"])
                        template2 = template2.replace("%name%", author["author_name"])
                        template2 = template2.replace("%page%", author["author_page"])
                        template2 = template2.replace("%content%", author["content"])
                        template2 = template2.replace("%time%", author["time"])
                        comments_result += template2
                    comments_result += TEMPLATE["reply_part2"]
                    template = template.replace("%reply%", comments_result)
                else:
                    template = template.replace("%reply%", "")

                result += template + "\n"

                progress_callback((i + 1) / len(posts) * 100)

        template_page = (
            TEMPLATE["main"]
            .replace("%html_title%", f"{thread_title}_{thread_name}吧_{tid}")
            .replace("%post_title%", thread_title)
            .replace("%content%", result)
        )

        with open(
            f"{thread_name}吧_{thread_title}_{tid}.html", "w", encoding="utf-8"
        ) as f:
            f.write(template_page)

        button_callback("🚀Start!")
