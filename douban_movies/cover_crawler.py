import os
import time
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, ALL_COMPLETED

import requests
from lxml import etree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def download(src, img_name, query):
    """" 下载图片 """
    dir = './' + query + '/' + str(img_name) + '.jpg'
    try:
        pic = requests.get(src, timeout=10)
        fp = open(dir, 'wb')
        fp.write(pic.content)
        fp.close()
        return '开始下载:' + str(img_name)
    except requests.exceptions.ConnectionError:
        return 'ConnectionError:' + str(img_name) + '无法下载!'
    except OSError:
        return 'OSError:' + str(img_name) + '无法下载!'


def chrome_headless():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    # 使用headless模式：不打开浏览器
    chrome_options.add_argument('--headless')
    # 谷歌文档提到需要加上这个属性来规避bug
    chrome_options.add_argument('--disable-gpu')
    # 初始化实例
    driver = webdriver.Chrome(chrome_options=chrome_options)


def chrome_driver(url):
    driver = webdriver.Chrome()
    # 使用headless模式
    # chrome_headless()
    # 请求地址
    driver.get(url)
    # 对当前屏幕截图
    driver.get_screenshot_as_file("screenshot.png")
    # 打印源页面
    # print(driver.page_source)
    html = etree.HTML(driver.page_source)
    # 关闭浏览器
    driver.close()
    # 退出webdriver
    driver.quit()
    return html


def multi_threads_pool(num, func, lists):
    """线程池下载"""
    threads_pool = ThreadPoolExecutor(num)

    # 如果要运行的函数只有一个参数
    # threads = [pool.submit(download1, (src) ) for src in srcs]

    # 如果要运行的函数有多个参数，需要借助lambda函数
    # list_var1 = ['https://img3.doubanio.com/view/celebrity/s_ratio_celebrity/public/p751.webp', 'hello']
    # list_var2 = ['https://img3.doubanio.com/view/celebrity/s_ratio_celebrity/public/p2414157745.webp', 'world']
    # threads_pool.submit(lambda p: download(*p), list_var1)
    # threads_pool.submit(lambda p: download(*p), list_var2)

    threads = [threads_pool.submit(lambda p: func(*p), list) for list in lists]
    # for t in threads:
    #     print(t.done())

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
    # process_results = [task.result() for task in as_completed(processes)]
    # print(process_results)
    wait(processes, return_when=ALL_COMPLETED)


def single_thread(srcs, titles, query):
    '''单线程下载'''
    i = 1
    for src, title in zip(srcs, titles):
        print(f'正在下载第{i}张图片')
        download(src, title.text, query)
        i += 1


def crawling_cover(url, query):
    '''解析url, 获取元素'''
    values = url.split('?')[- 1]
    gets = {}
    for key_value in values.split('&'):
        list = key_value.split('=')
        gets[list[0]] = list[1]
    if (gets.__contains__('start')):
        page = int(gets['start']) // 15 + 1
        pages = '------------------------正在爬取第' + str(page) + '页----------------------------------'
    else:
        pages = '------------------------正在爬取第1页----------------------------------'

    # 获取html内容，方法1：
    # requests获取源网页，BeautifulSoup解析
    # response = requests.get(url)
    # html = BeautifulSoup(response.content, 'lxml')
    # srcs = html.find('.item-root .detail .cover src')
    # titles = html.find('.item-root .cover-link .title')

    # 获取html内容，方法2：Chrome Webdriver
    html = chrome_driver(url)

    # 解析html内容，方法2：Xpath
    src_xpath = "//div[@class='item-root']/a[@class='cover-link']/img[@class='cover']/@src"
    title_xpath = "//div[@class='item-root']/div[@class='detail']/div[@class='title']/a[@class='title-text']"
    srcs = html.xpath(src_xpath)
    titles = html.xpath(title_xpath)
    print(srcs)
    print(titles)

    lists = []
    for src, title, q in zip(srcs, titles, [query] * len(srcs)):
        lists.append([src, title.text, q])
    print(lists)

    start = time.time()
    print('启动下载进程，进程号[%d].' % os.getpid())

    # 线程池下载
    multi_threads_pool(8, download, lists)

    # 单线程下载
    # single_thread(srcs, titles, query)

    end = time.time()
    print('本次下载耗时%.2f秒.' % (end - start))
    return pages


def main():
    query = '林青霞'
    # 创建文件夹
    folder_name = query
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    urls = []
    for i in range(0, 15 * 6, 15):
        if i == 0:
            urls.append("https://movie.douban.com/subject_search?search_text=" + query + "&cat=1002")
        else:
            urls.append("https://movie.douban.com/subject_search?search_text=" + query + "&cat=1002&start=" + str(i))

    lists = []
    for url, q in zip(urls, [query] * len(urls)):
        lists.append([url, q])
    start = time.time()
    # 进程池
    multi_process_pool(2, crawling_cover, urls, query)

    # 单进程
    # for url in urls:
    #     spiders_cover(url, query)

    end = time.time()
    print(f'Download Finished! 耗时{end - start}秒')


if __name__ == '__main__':
    main()
