import json

import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from scrapy.http import Request, Response
import re
import time
from bs4 import BeautifulSoup

'''
翻页API                                                                       二级目录
https://www.dar.gov.ph/articles/news/regions/car.json?p=2                ##https://www.dar.gov.ph/articles/news/regions/car
https://www.dar.gov.ph/articles/news/regions/ilocos.json?p=2             ##https://www.dar.gov.ph/articles/news/regions/ilocos
https://www.dar.gov.ph/articles/news/regions/central-luzon.json?p=2      ##https://www.dar.gov.ph/articles/news/regions/central-luzon
'''


# author:刘鼎谦
class DarSpider(scrapy.Spider):
    name = 'dar'
    allowed_domains = ['www.dar.gov.ph']
    start_urls = ['https://www.dar.gov.ph/articles/news/']

    website_id = 1273  # 还不清楚id具体是啥
    language_id = 2117  # 默认lan id是菲律宾语 ， 但这是双语网站，1866 英语
    sql = {  # my sql 配置
        'host': '121.36.242.178',
        'user': 'dg_ldq',
        'password': 'dg_ldq',
        'db': 'dg_test_source'
    }
    api_url = 'https://www.dar.gov.ph/articles/news/regions/{}.json?p={}'


    def __init__(self, time=None, *args, **kwargs):
        super(DarSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        uurl = 'https://www.dar.gov.ph/articles/news/index.json?p=1'
        yield Request(url=uurl,meta={'category2':'index','cur_page':'1'},callback=self.parse_page)
        for i in soup.select('#regions-list > li > a'):
            meta = {'category2':i.get('href').split('/')[-1], 'cur_page':'1'}
            url = self.api_url.format(meta['category2'], meta['cur_page'])
            # self.logger.info(url)
            yield Request(url, meta=meta, callback=self.parse_page)

    def parse_page(self, response):
        flag = True
        js = json.loads(response.text)['articles']
        pub_time = js[-1]['publishedOn']['timeStamp']['iso']
        if self.time is None or (Util.format_time3(pub_time)) >= int(self.time):
            for i in js:
                url = i['url']
                response.meta['pub_time'] = i['publishedOn']['timeStamp']['iso']
                response.meta['images'] = [i['metadata']['featured-image']]
                yield Request(url, meta=response.meta, callback=self.parse_item)
        else:
            flag=False
            self.logger.info('时间截止~')

        if flag:
            nextPage = int(response.meta['cur_page']) + 1
            response.meta['cur_page'] = str(nextPage)
            if nextPage < 500:  #
                yield Request(url=self.api_url.format(response.meta['category2'], response.meta['cur_page']),meta=response.meta, callback=self.parse_page)

    def parse_item(self,response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['pub_time']=response.meta['pub_time']
        item['category1'] = 'news'
        item['category2'] = 'religion_'+response.meta['category2']
        tgl = soup.select('#tgl')
        eng = soup.select('#eng')
        if tgl:
            item['images'] = [i.get('src') for i in soup.select('#tgl img')] if soup.select('#tgl img') else []
            item['title'] = soup.select_one('#tgl > header > h1').text
            item['body'] = ''.join(i.text.strip() + '\n' for i in soup.select('#tgl > .article-content> p'))
            item['abstract'] = soup.select_one('#tgl>div.article-content> p').text
            self.language_id = 2117
            yield item

        if eng:
            item['images'] = [i.get('src') for i in soup.select('#eng img')] if soup.select('#eng img') is not None else []
            item['title'] = soup.select_one('#eng>header>h1').text
            item['body'] = ''.join(i.text.strip() + '\n' for i in soup.select('#eng > .article-content> p'))
            item['abstract'] = soup.select_one('#eng > div.article-content> p').text
            self.language_id = 1866
            yield item

