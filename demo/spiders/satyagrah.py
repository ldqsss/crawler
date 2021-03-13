import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
from bs4 import BeautifulSoup


# author:刘鼎谦
class SatyagrahSpider(scrapy.Spider):
    name = 'satyagrah'
    allowed_domains = ['satyagrah.scroll.in']
    start_urls = ['https://satyagrah.scroll.in/']   # 这个网站翻页，要手动url后加/page/d+, 一级目录重定向categories 要改成category
    website_id = 916  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # my sql 配置
        'host': '121.36.242.178',
        'user': 'dg_ldq',
        'password': 'dg_ldq',
        'db': 'dg_test_source'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(SatyagrahSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('.is-active ~ li>a')[:-2]:
            url = 'https:' + i.get('href').replace('categories', 'category')
            meta = {'category1':i.text, 'url': url, 'page':'1'}   # 如果以整型保存page，就翻不了页...？
            yield Request(url=url, meta= meta,callback=self.parse_page)

    def parse_page(self,response):
        soup = BeautifulSoup(response.text, 'html.parser')
        essays = soup.select('.row-story  a')
        flag = True
        pt= essays[-1].select_one('time').get('datetime').replace('T', ' ')[:-6]
        if self.time is None or Util.format_time3(pt) >= int(self.time):
            for i in essays:
                url = i.get('href')
                response.meta['title'] = i.select_one('h1').text.strip()
                pub_time = i.select_one('time').get('datetime').replace('T',' ')[:-6]  # 形如'2021-03-08T09:07:00+05:30'
                response.meta['pub_time'] = pub_time
                response.meta['images'] = [i.select_one('img').get('src')]
                yield Request(url=url, meta=response.meta, callback=self.parse_item)

        else:
            flag = False
            self.logger.info('时间截止')

        if flag:
            curr_page = int(response.meta['page']) + 1
            nextPage = response.meta['url'] + '/page/' + str(curr_page)
            response.meta['page'] = str(curr_page)
            yield Request(url=nextPage, meta=response.meta,callback=self.parse_page)

    def parse_item(self,response):
        soup = BeautifulSoup(response.text,'html.parser')
        images = response.meta['images']
        try:
            images.append(soup.select_one('picture img').get('src'))
        except:
            pass
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['title'] = response.meta['title']
        item['abstract'] = soup.select_one('.orange-tag ~ h2').text.strip()
        item['images'] = images
        item['pub_time'] = response.meta['pub_time']
        item['category2'] = None
        body = ''.join(i.text+'\n' for i in soup.select('#article-contents p'))
        item['body'] = body
        return item