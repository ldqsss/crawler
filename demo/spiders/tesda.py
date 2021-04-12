import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from scrapy.http import Request, Response
import re
import time
from bs4 import BeautifulSoup


# author:刘鼎谦
class TesdaSpider(scrapy.Spider):  # 这个网站新闻很少 5*76
    name = 'tesda'
    allowed_domains = ['www.tesda.gov.ph']
    start_urls = ['https://www.tesda.gov.ph/Gallery']

    website_id = 9999  # 还不清楚id具体是啥
    language_id = 1866  # 所用语言的id
    sql = {  # my sql 配置
        'host': '121.36.242.178',
        'user': 'dg_ldq',
        'password': 'dg_ldq',
        'db': 'dg_test_source'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(TesdaSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def judge_time(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        date = soup.select_one('.col-md-12 > p').text.split('\r')[0]
        tt = date.split()
        date = tt[1]+' '+tt[0]+' '+tt[2]
        if self.time is None or (Util.format_time3(Util.format_time2(date))) >= int(self.time):
            return True
        else:
            return False

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        article_1st = 'https://www.tesda.gov.ph' + soup.find(class_='large-3 medium-3 small-3 column events').select_one('a').get('href')
        if self.time is not None and self.judge_time(article_1st):
            pass
        elif self.time is None:
            pass
        else:
            flag = False
            self.logger.info('时间截止')
        if flag:
            for i in soup.find_all(class_='large-3 medium-3 small-3 column events'):
                url = 'https://www.tesda.gov.ph' + i.select_one('a').get('href')
                image = ['https://www.tesda.gov.ph' + i.select_one('img').get('src')]
                meta = {'images':image}
                yield Request(url=url,meta=meta,callback=self.parse_item)

            nextPage = 'https://www.tesda.gov.ph' + soup.select_one('.active ~ li > a').get('href')
            yield Request(url=nextPage)

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['category1'] = None
        item['category2'] = None
        item['title'] = soup.select_one('.col-md-12>h4').text.strip()
        item['abstract'] =soup.select_one('.col-md-12> p').text.strip()
        item['images'] = response.meta['images']
        tt = soup.select_one('.col-md-12 > p').text.split('\r')[0].split()
        if re.match('^\D',tt[0]):
            ss = tt[0]+ ' ' + tt[1]+ ' ' + tt[2]
        else:
            ss = tt[1] + ' ' + tt[0] + ' ' + tt[2]
        item['pub_time'] = Util.format_time2(ss)
        item['body'] = ''.join(i.text.strip() + '\n' for i in soup.select('.col-md-12> p'))
        return item
