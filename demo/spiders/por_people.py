import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from scrapy.http import Request, Response
import re
import time
from bs4 import BeautifulSoup


# author:刘鼎谦


class PorPeopleSpider(scrapy.Spider):
    name = 'por_people'
    allowed_domains = ['portuguese.people.com.cn']
    start_urls = ['http://portuguese.people.com.cn/']
    # 本网站，就5个一级目录。每个目录有10页左右内容，每页10篇文章

    website_id = 1275  # 网站的id(必填)
    language_id = 2122  # 葡萄语id
    sql = {  # my sql 配置
        'host': '121.36.242.178',
        'user': 'dg_ldq',
        'password': 'dg_ldq',
        'db': 'dg_test_source'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(PorPeopleSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.find(class_='w980 nav white clear').select('a')[1:-3]:
            category1 = i.text.strip()
            url = i.get('href')
            yield Request(url=url, meta={'category1':category1}, callback=self.parse_page)

    def parse_page(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        lpt = soup.select('.p1_2 li > a')[-1].get('href').split('/')
        last_pub_time = '{0}-{1}-{2} 00:00:00'.format(lpt[2], lpt[3][:2], lpt[3][2:])
        if self.time is None or Util.format_time3(last_pub_time) >= int(self.time):
            for i in soup.select('.p1_2 > li > a'):
                url = 'http://portuguese.people.com.cn'+i.get('href')
                yield Request(url, callback=self.parse_item, meta=response.meta)
        else:
            flag = False
            self.logger.info('时间截止')
        if flag:
            try:  # 翻页
                next = soup.select_one('a.common_current_page ~ a').get('href')
                nextPage = response.url.split('index')[0] + next
                yield Request(url=nextPage, callback=self.parse_page, meta=response.meta)
            except:
                print('Next Page NO more')


    def get_pub_time(self, rawtime):
        t = rawtime.split('/')
        pub_time = '{0}-{1}-{2} 00:00:00'.format(t[4], t[5][:2], t[5][2:])
        return pub_time

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['title'] = soup.select_one('h1').text.strip()  # h1标签就一个，表示标题
        item['images'] = [i.get('src') for i in soup.select('img')]
        rawtime = response.url
        item['pub_time'] = self.get_pub_time(rawtime)
        item['category2'] = None
        item['body'] = ''.join(i.text.strip() + '\n' for i in soup.select('.txt_con p'))   # p 标签共7个，都是正文内容
        item['abstract'] = soup.select('p')[0].text.strip()
        return item