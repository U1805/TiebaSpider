import math
from utils import img2base64
from fetcher import fetchHtmlReply
from fetcher import COMMENT_POOL


class Extractor:
    def __init__(self, page, local=True) -> None:
        self.page = page
        self.local = local

    def getAuthors(self) -> list:
        authors = self.page.select(".d_author")
        authors_res = []
        for author in authors:
            is_louzhu = len(author.select(".louzhubiaoshi_wrap"))
            author_face = author.select(".p_author .p_author_face img")[0]
            # print(author_face["username"]) # 注册名

            if self.local:
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
                    "author_badge_title": author.select(".p_author .d_badge_title")[
                        0
                    ].text,
                    "author_badge_level": author.select(".p_author .d_badge_lv")[
                        0
                    ].text,
                }
            )
        return authors_res

    def getContent(self) -> dict:
        post_res = {}
        for post in self.page.select(".d_post_content.j_d_post_content"):
            post_id = post["id"].replace("post_content_", "")
            post_res[post_id] = post.contents
        return post_res

    def getTails(self) -> list:
        info_res = []
        for tail_info in self.page.select(".post-tail-wrap"):
            info_res.append(
                {
                    "ip": tail_info.findChild().text,
                    "floor": tail_info.select(".tail-info")[1].text,
                    "time": tail_info.select(".tail-info")[2].text,
                }
            )
        return info_res

    def getComment(self, tid, post_id) -> list:
        result = []

        if post_id not in COMMENT_POOL:
            return result

        total_page = math.ceil(
            COMMENT_POOL[post_id]["comment_num"]
            / COMMENT_POOL[post_id]["comment_list_num"]
        )
        for pn in range(1, total_page + 1):
            replies = fetchHtmlReply(tid, post_id, pn)
            for reply in replies:
                avatar = reply.select(".j_user_card.lzl_p_p img")[0]["src"]
                result.append(
                    {
                        "avatar": (img2base64(avatar) if self.local else avatar),
                        "username": reply.select(".at.j_user_card")[0].text,
                        "content": reply.select(".lzl_content_main")[0].contents,
                        "time": reply.select(".lzl_time")[0].text,
                    }
                )

        return result
