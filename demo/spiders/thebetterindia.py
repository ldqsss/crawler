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
class ThebetterindiaSpider(scrapy.Spider):
    name = 'thebetterindia'
    allowed_domains = ['hindi.thebetterindia.com']
    start_urls = ['https://hindi.thebetterindia.com/']
    website_id = 917  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # my sql 配置
        'host': '121.36.242.178',
        'user': 'dg_ldq',
        'password': 'dg_ldq',
        'db': 'dg_test_source'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(ThebetterindiaSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('#bs-example-navbar-collapse-1  li>a'):
            if re.findall('category', i.get('href')):
                url = i.get('href')
                meta = {'category1': i.text.strip()}  # 如果以整型保存page，就翻不了页...？
                yield Request(url=url, meta=meta, callback=self.parse_page)
            else:
                continue

    def get_pubtime(self,url):
        soup = BeautifulSoup(requests.get(url,
                            headers ={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/86.0.4240.75 Safari/537.36'}
                    ).text,'html.parser')
        ss = soup.select_one('.meta-date').text.split(':')[1].strip()
        self.logger.info(ss)
        pub_time = Util.format_time3(Util.format_time2(ss))
        return pub_time

    def parse_page(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        essays = soup.select('article')
        flag = True
        url = essays[-1].select_one('a').get('href')
        if self.time is None or (self.get_pubtime(url)) >= int(self.time):
            for i in essays:
                url = i.select_one('a').get('href')
                response.meta['images'] = [i.select_one('img').get('data-gmsrc')]
                yield Request(url=url, meta=response.meta, callback=self.parse_item)
        else:
            flag = False
            self.logger.info('时间截止')

        if flag:
            for i in range(2,30):   # 最多30 页
                nextPage = response.url + 'page/' + str(i) + '/'
                self.logger.info(nextPage)
                self.logger.info('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
                try:
                    yield Request(url=nextPage, meta=response.meta, callback=self.parse_page)
                except:
                    self.logger.info('next page no more')
                    break

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.select_one('#content > article')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['title'] = content.find(class_='single-post-title entry-title').text.strip()
        item['abstract'] = soup.select_one('.subtitle').text.strip()
        item['images'] = response.meta['images']
        ss = content.select_one('.meta-date').text.split(':')[1].strip()
        pub_time = Util.format_time2(ss)  # (ss.lower()[0].upper() + ss.lower()[1:])
        item['pub_time'] = pub_time
        item['category2'] = None
        item['body'] = ''.join(i.text.strip()+'\n' for i in soup.select('.tbi-inner-entry-content > p'))
        return item
