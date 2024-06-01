from bs4 import Tag
from utils import img2base64
from extractor import Extractor
from template import TEMPLATE


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


def formatPage(tid, page, local=True):
    extractor = Extractor(page, local)
    authors = extractor.getAuthors()
    contents = extractor.getContent()
    tails = extractor.getTails()
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

        template = template.replace("%content%", formatContent(content, local))

        template = template.replace("%ip%", tail["ip"])
        template = template.replace("%floor%", tail["floor"])
        template = template.replace("%time%", tail["time"])

        comments = extractor.getComment(tid, pid)
        if comments:
            comments = [
                (
                    TEMPLATE["reply_part1"]
                    .replace("%avatar%", comment["avatar"])
                    .replace("%username%", comment["username"])
                    .replace(
                        "%content%",
                        formatContent(comment["content"], local),
                    )
                    .replace("%time%", comment["time"])
                )
                for comment in comments
            ]
            template = template.replace(
                "%reply%",
                TEMPLATE["reply_part0"] + "".join(comments) + TEMPLATE["reply_part2"],
            )
        else:
            template = template.replace("%reply%", "")

        res += template
    return res
