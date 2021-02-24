import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
class HanuraonewsSpider(scrapy.Spider):
    name = 'hanuraonews'  # 类名要和爬虫文件名相同
    website_id = 949  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://hanuraonews.com/']
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_wky',
        'password': 'dg_wky',
        'db': 'dg_test_source'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(HanuraonewsSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        html = BeautifulSoup(response.text, 'lxml')
        for i in html.select('#menu-primary-menu-1 > li')[1:-1]:
            meta = {'category1': i.select_one('a').text, 'category2': None}
            category_2 = i.select('ul>li>a')
            yield Request(i.select_one("a").attrs['href'], callback=self.parse_essay, meta=meta)
            for e in category_2:
                meta['category2']= e.text
                yield Request(e.attrs['href'], callback=self.parse_essay, meta=meta)

    def parse_essay(self, response):
        html = BeautifulSoup(response.text, 'lxml')
        flag = True
        last = html.find_all(class_='td-module-meta-info')[-1].select_one('.td-post-date').text
        last_timestamp = Util.format_time3(Util.format_time2(last))
        if self.time is None or last_timestamp >= int(self.time):
            for i in html.find_all(class_='td_module_10 td_module_wrap td-animation-stack'):
                response.meta['title'] = i.select_one('a').get('title')
                response.meta['pub_time'] = Util.format_time2(i.select_one('.td-post-date').text)
                response.meta['images'] = [i.select_one('.td-module-thumb > a > img').get('data-img-url')]
                response.meta['abstract'] = i.select_one('.item-details > .td-excerpt').text.strip()
                yield Request(i.select_one('a').attrs['href'], callback=self.parse_item, meta=response.meta)
        else:
            flag = False
            self.logger.info('时间截止。')
        if flag:
            try:
                nextPage = html.select("span.current ~ a")[0].attrs['href']
                yield Request(url=nextPage, callback=self.parse_essay, meta=response.meta)
            except:
                self.logger.info('Next Page No More!')

    def parse_item(self, response):
        item = DemoItem()
        html = BeautifulSoup(response.text, 'lxml')
        item['category1'] = response.meta['category1']
        item['title'] = response.meta['title']
        content = ''
        for i in html.select('.td-post-featured-image ~ p'):
            content += i.text + '\n'
        item['body'] = content
        item['abstract'] = response.meta['abstract']
        item['pub_time'] = response.meta['pub_time']
        item['images'] = response.meta['images']
        item['category2'] = response.meta['category2']
        return item