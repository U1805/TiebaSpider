import re
import threading
from fetcher import fetchPage, fetchJsonReply
from format import formatPage
from template import TEMPLATE
from utils import update_pool_instance, proxy_pool


def run(tid, local, max_connections, progress_callback, button_callback):
    update_pool_instance(proxy_pool(button_callback, progress_callback))

    page, html_title, page_num = fetchPage(tid)
    button_callback("Downloading replies...")
    fetchJsonReply(tid, page_num, progress_callback)

    button_callback("Downloading pages...")
    progress_callback(0)

    template_page = (
        TEMPLATE["main"]
        .replace("%html_title%", html_title)
        .replace("%post_title%", re.sub(r"_.+_百度贴吧$", "", html_title))
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
