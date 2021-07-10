import requests
import scrapy
from scrapy import FormRequest

from demo.util import Util
from demo.items import DemoItem
from scrapy.http import Request, Response
import re
import time
from bs4 import BeautifulSoup


# author:刘鼎谦  finished_time: 2021-07-10  动态网站
class BurmaSpider(scrapy.Spider):
    name = 'burma'
    allowed_domains = ['burma.irrawaddy.com']
    start_urls = ['https://burma.irrawaddy.com/category/news',
                  'https://burma.irrawaddy.com/category/article',
                  'https://burma.irrawaddy.com/category/opinion',
                  'https://burma.irrawaddy.com/category/business',
                  'https://burma.irrawaddy.com/category/lifestyle',
                  'https://burma.irrawaddy.com/category/opinion/interview',
                  'https://burma.irrawaddy.com/category/lifestyle/food',
                  'https://burma.irrawaddy.com/category/lifestyle/health']

    url_api = 'https://burma.irrawaddy.com/wp-admin/admin-ajax.php'

    website_id = 1408  # 网站的id(必填)
    language_id = 2065  # 缅甸语言
    sql = {  # my sql 配置
        'host': '121.36.242.178',
        'user': 'dg_ldq',
        'password': 'dg_ldq',
        'db': 'dg_test_source'
    }

    flag = True
    def __init__(self, time=None, *args, **kwargs):
        super(BurmaSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        meta = {'category1': response.url.split('/')[4],
                'category2':  response.url.split('/')[-1] if  response.url.split('/').__len__() == 6 else None}
        if meta['category2'] is None and meta['category1'] in ['news', 'article', 'lifestyle','business'] :
            meta['offset'] = '5'
            meta['cat'] = soup.select_one('body').get('class')[3].split('-')[1],
            meta['posts[]'] = soup.select_one('.container article').get('class')[0].split('-')[1]
            yield FormRequest(url=self.url_api, formdata={
                'action': 'irr_load_more_articles',
                'offset': '5',
                'cat': meta['cat'],
                'posts[]': meta['posts[]']
            },callback=self.parse_more, meta=meta)
        elif meta['category2'] is None and meta['category1'] == 'opinion' :
            meta['offset'] = '9'
            yield FormRequest(url=self.url_api, callback=self.parse_more,formdata={
                'action': 'irr_load_more_opinions',
                'offset': '9'
            },meta=meta)
        else:
            meta['query_paged']='1'
            yield FormRequest(url=response.url, formdata={
                    'filter_mood': 'all',
                    'filter_date': '1y',
                    'date_after':'',
                    'date_before':'',
                    'date_year': '2012',
                    'query_paged': '1',  # 除此之外是无效参数
                    'next_page':'',
            },callback=self.parse_more, meta=meta)

    def parse_more(self, response):  # 动态翻页
        soup = BeautifulSoup(response.text, 'html.parser')
        last_pub = '-'.join(
            re.search('\d{4}/\d{2}/\d{2}', soup.select('.title a')[-1].get('href')).group().split('/')) + " 00:00:00"
        if self.time is None or Util.format_time3(last_pub) >= int(self.time):
            articles = [a.get('href') for a in soup.select('.title a')]
            for article in articles:
                self.logger.info(f'{article}')
                yield Request(article, callback=self.parse_item, meta=response.meta)
        else:
            self.logger.info('时间截止.')
            self.flag = False

        if self.flag:
            if response.meta['category2'] is None:
                if response.meta['category1'] in ['news', 'article', 'lifestyle','business']:
                   response.meta['offset'] = str(int(response.meta['offset'])+6)
                   yield FormRequest(url=self.url_api, formdata={
                       'action': 'irr_load_more_articles',
                       'offset': response.meta['offset'],
                       'cat': response.meta['cat'],
                       'posts[]': response.meta['posts[]']
                   }, callback=self.parse_more, meta=response.meta)
                else:
                    response.meta['offset'] = str(int(response.meta['offset'])+3)
                    yield FormRequest(url=self.url_api, callback=self.parse_more, formdata={
                        'action': 'irr_load_more_opinions',
                        'offset': response.meta['offset']
                    }, meta=response.meta)
            else:
                response.meta['query_paged'] = str(int(response.meta['query_paged'])+1)
                yield FormRequest(url=response.url, formdata={
                    'filter_mood': 'all',
                    'filter_date': '1y',
                    'date_after': '',
                    'date_before': '',
                    'date_year': '2012',
                    'query_paged': response.meta['query_paged'],  # 除此之外是无效参数
                    'next_page': '',
                }, callback=self.parse_more, meta=response.meta)

    def parse_item(self,response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['title'] = soup.select_one('h1').text
        item['images'] = [soup.select_one('article figure').get('style')[22:-2]]
        item['pub_time'] = '-'.join(re.search('\d{4}/\d{2}/\d{2}', response.url).group().split('/')) + " 00:00:00"
        item['category2'] = response.meta['category2']
        item['body'] = ''.join(i.text.strip()+'\n' for i in soup.select('.article-entry  p'))
        item['abstract'] = soup.select_one('.article-entry  p').text
        return item