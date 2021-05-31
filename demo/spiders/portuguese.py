import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from scrapy.http import Request, Response
import re
import time
from bs4 import BeautifulSoup


# author:刘鼎谦
class PortugueseSpider(scrapy.Spider):
    name = 'portuguese'
    allowed_domains = ['portuguese.cri.cn']
    start_urls = [
                  'http://portuguese.cri.cn/news/chinaandlusophoneworld/index.html',
                  'http://portuguese.cri.cn/news/currentevents/index.html',
                  'http://portuguese.cri.cn/news/world/index.html',
                  'http://portuguese.cri.cn/news/china/index.html'
                  ]
    # 说明： 本网站只有四个子站点有新闻，每个最多10页。每页最多20篇
    website_id = 1278  # 网站的id(必填)
    language_id = 2122  # 葡萄语id
    sql = {  # my sql 配置
        'host': '121.36.242.178',
        'user': 'dg_ldq',
        'password': 'dg_ldq',
        'db': 'dg_test_source'
    }

    nextPage = 'http://portuguese.cri.cn/news/{0}/index_{1}.html'

    def __init__(self, time=None, *args, **kwargs):
        super(PortugueseSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        MaxPage = int(soup.select_one('cite').text) - 1
        CurrentPage = int(re.search('\d+', response.url).group()) if re.search('\d+', response.url) else 0
        category1 = response.url.split('/')[-2]
        tt = soup.select('.news-item-text a')[-1].get('href').split('/')[-2]
        ttt = tt[:4] + '-' + tt[4:6] + '-' + tt[6:] + ' 00:00:00'
        lastPub_time = Util.format_time3(ttt)  # 转换为时间戳
        if self.time is None or lastPub_time >= int(self.time):
            meta={'category1': category1}
            for i in soup.select('.news-item-text a'):
                news_url = i.get('href')
                meta['abstract']= i.text   # 如果以整型保存page，就翻不了页...？
                yield Request(url=news_url, meta=meta, callback=self.parse_item)
            if CurrentPage < MaxPage:  # 翻页，回调给自己
                yield Request(url=self.nextPage.format(category1, str(CurrentPage + 1)))
        else:
            self.logger.info('时间截止')
    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['title'] = soup.select_one('.article-title').text.strip()
        item['abstract'] = response.meta['abstract']
        item['images'] = [i.get('src') for i in soup.select('.article-con img')]
        item['pub_time'] = soup.find(class_='article-type-item article-type-item-time').text[11:]
        item['category2'] = None
        item['body'] = ''.join(i.text.strip() + '\n' for i in soup.select('.article-con p'))
        return item
