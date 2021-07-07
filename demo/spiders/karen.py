import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from scrapy.http import Request, Response
import re
import time
from bs4 import BeautifulSoup


# author:刘鼎谦  finished_time:'2021-07-07 04:46:23' 静态网站
class KarenSpider(scrapy.Spider):
    name = 'karen'
    allowed_domains = ['karen.kicnews.org']
    start_urls = ['http://karen.kicnews.org/']

    website_id = 1489  # 网站的id(必填)
    language_id = 2065  # 缅甸语言
    sql = {  # my sql 配置
        'host': '121.36.242.178',
        'user': 'dg_ldq',
        'password': 'dg_ldq',
        'db': 'dg_test_source'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(KarenSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('#menu-main-menu-1 li a')[:-5]:
            category1 = i.text.strip()
            url = i.get('href')
            if url is not None:
                yield Request(url=url, meta={'category1': category1}, callback=self.parse_page)  # 一级目录

    def parse_page(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        try:
            lpt = soup.select('.td-post-date > time')[-2].get('datetime').replace('T', ' ')[:-6]
            last_pub_time = Util.format_time3(lpt)
        except:
            last_pub_time = Util.format_time3(Util.format_time())
        if self.time is None or last_pub_time >= int(self.time):
            for i in soup.select('.item-details > h3> a'):
                url = i.get('href')
                yield Request(url, callback=self.parse_item, meta=response.meta)
        else:
            flag = False
            self.logger.info('时间截止')
        if flag:
            try:  # 翻页
                nextPage = soup.select_one('a.last ~a').get('href')
                yield Request(url=nextPage, callback=self.parse_page, meta=response.meta)
            except:
                print('Next Page NO more')

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['title'] = soup.select_one('header h1').text
        item['images'] = [soup.select_one('.td-post-featured-image img').get('src')]
        item['pub_time'] = soup.select_one('.td-post-date time').get('datetime').replace('T', ' ')[:-6]
        item['category2'] = None
        item['body'] = ''.join(i.text.strip() + '\n' for i in soup.find(class_='td-post-content td-pb-padding-side').select('p'))  # p 标签共7个，都是正文内容
        item['abstract'] = soup.select('p')[0].text.strip()
        return item
