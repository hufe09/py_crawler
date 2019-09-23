# poster_parse.py
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed, wait, ALL_COMPLETED

import requests


def download(src, img_name, query):
    """" 下载图片 """
    # print('启动下载进程，进程号[%d].' % os.getpid())
    dir = './' + query + '/' + str(img_name) + '.jpg'
    try:
        pic = requests.get(src, timeout=10)
        fp = open(dir, 'wb')
        fp.write(pic.content)
        fp.close()
        return '开始下载:' + str(img_name), src
    except requests.exceptions.ConnectionError:
        return 'ConnectionError:' + str(img_name) + '无法下载!'
    except OSError:
        return 'OSError:' + str(img_name) + '无法下载!'


def multi_threads_pool(num, func, lists):
    """线程池下载"""
    threads_pool = ThreadPoolExecutor(num)
    threads = [threads_pool.submit(lambda p: func(*p), list) for list in lists]

    for future in as_completed(threads):
        # 使用as_completed方法一次取出所有任务的结果
        data = future.result()
        print(f"{data}")

    # wait方法可以让主线程阻塞，直到满足设定的要求
    wait(threads, return_when=ALL_COMPLETED)


def multi_process_pool(num, func, lists, query):
    '''进程池'''
    processes_pool = ProcessPoolExecutor(max_workers=num)
    # processes = [processes_pool.submit(lambda p: func(*p), list) for list in lists]
    processes = [processes_pool.submit(func, list, query) for list, query in zip(lists, [query] * len(lists))]
    for process in as_completed(processes):
        # 使用as_completed方法一次取出所有任务的结果
        data = process.result()
        print(f"{data}")

    # wait方法可以让主线程阻塞，直到满足设定的要求
    wait(processes, return_when=ALL_COMPLETED)


def crawling_poster(url, query):
    '''解析url, 获取元素'''
    html = requests.get(url).text
    response = json.loads(html, encoding='utf-8')
    srcs = []
    ids = []
    for image in response['images']:
        srcs.append(image['src'])
        ids.append(image['id'])
    lists = []
    for src, id, q in zip(srcs, ids, [query] * len(srcs)):
        lists.append([src, id, q])
    print('启动下载进程，进程号[%d].' % os.getpid())
    start = time.time()
    #线程池下载图片
    multi_threads_pool(8, download, lists)

    #单线程下载图片
    for src, id in zip(srcs, ids):
        download(src, id, query)
    end = time.time()
    print(f'本页图片下载耗费{end - start}秒')
    return url

def main():
    query = '王祖贤'

    # 创建文件夹
    folder_name = query
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    urls = []
    for i in range(0, 500, 20):
        urls.append('https://www.douban.com/j/search_photo?q=' + query + '&limit20&start=' + str(i))


    start = time.time()

    # 进程池
    multi_process_pool(2, crawling_poster, urls, query)

    # 单进程
    # for url in urls:
    #     print(parse_poster(url, query))

    end = time.time()
    print(f'全程耗费{end - start}秒')

if __name__ == '__main__':
    main()