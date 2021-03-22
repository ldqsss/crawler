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
class DainiktribuneonlineSpider(scrapy.Spider):
    name = 'dainiktribuneonline'
    allowed_domains = ['dainiktribuneonline.com']   # 动态网站
    start_urls = ['https://www.dainiktribuneonline.com/']

    website_id = 1094  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # my sql 配置
        'host': '121.36.242.178',
        'user': 'dg_ldq',
        'password': 'dg_ldq',
        'db': 'dg_test_source'
    }

    api = {
        'world':     'https://www.dainiktribuneonline.com/Pagination/ViewAll?id=57&page={0}&topNews=35069,34949,34950,34951,34920&_={1}',
        'nation':    'https://www.dainiktribuneonline.com/Pagination/ViewAll?id=42&page={0}&topNews=35065,35078,35067,35066,34934&_={1}',
        'sport':     'https://www.dainiktribuneonline.com/Sports/GetPaginationNews?id=50&page={0}&topNews=35070,34958,35033,34960&_={1}',
        'punjab':    'https://www.dainiktribuneonline.com/Pagination/ViewAll?id=45&page={0}&topNews=34966,34961,34962,34969,34971&_={1}',
        'himachal':  'https://www.dainiktribuneonline.com/Pagination/ViewAll?id=272&page={0}&topNews=35080,34974,34978,34981,34982&_={1}',
        'chandigarh':'https://www.dainiktribuneonline.com/Pagination/ViewAll?id=20&page={0}&topNews=34967,34968,34975,34970,34976&_={1}',
        'business':  'https://www.dainiktribuneonline.com/Sports/GetPaginationNews?id=19&page={0}&topNews=35068,34946,34924,34915&_={1}',
        'astha':     'https://www.dainiktribuneonline.com/Pagination/ViewAll?id=277&page={0}&topNews=34959,34910,34909,34908,34907&_={1}',
        'lifestyle': 'https://www.dainiktribuneonline.com/Sports/GetPaginationNews?id=276&page={0}&topNews=35076,34759,34757,34754,34665,34496,34311&_={1}',
        'haryana':   'https://www.dainiktribuneonline.com/Pagination/ViewAll?id=270&page={0}&topNews=35071,35004,35007,35026,35027&_={1}',
        'rohtak':    'https://www.dainiktribuneonline.com/Pagination/ViewAll?id=273&page={0}&topNews=35036,35043,34904,34902,34886&_={1}',
        'karnal':    'https://www.dainiktribuneonline.com/Pagination/ViewAll?id=274&page={0}&topNews=35029,35028,35004,34863,34862&_={1}',
        'gurugram':  'https://www.dainiktribuneonline.com/Pagination/ViewAll?id=275&page={0}&topNews=35004,35049,35028,35040,34903&_={1}',
        'editorials':'https://www.dainiktribuneonline.com/Sports/GetPaginationNews?id=60&page={0}&topNews=34945,34683,34510,34453,34181,34016&_={1}',
        'comments':  'https://www.dainiktribuneonline.com/Sports/GetPaginationNews?id=59&page={0}&topNews=34947,34948,34957,34695,34693,34686&_={1}'
    }


    def __init__(self, time=None, *args, **kwargs):
        super(DainiktribuneonlineSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def get_pubtime(self, url):
        soup = BeautifulSoup(requests.get(url,
                            headers ={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/86.0.4240.75 Safari/537.36'}
                    ).text, 'html.parser')
        time_url = 'https://www.dainiktribuneonline.com' + soup.select('.card-top-align')[-1].get('href')
        html = BeautifulSoup(requests.get(time_url,
                            headers ={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/86.0.4240.75 Safari/537.36'}
                    ).text,'html.parser')
        pub_time = Util.format_time3(Util.format_time2(html.select_one('.time-share span').text.strip()))
        return pub_time

    def parse(self, response):
        soup = BeautifulSoup(response.text,'html.parser')
        for i in soup.select('.sub-categories  li>a'):
            meta = {'category1': i.text.strip()}
            if re.findall('news', i.get('href')):
                try:
                    url1 = self.api[i.get('href').split('/')[-1]]
                    for j in range(1,400):
                        url = url1.format(str(j), str(int(time.time() * 1000)))
                        if self.time is None or (self.get_pubtime(url)) >= int(self.time):
                            yield Request(url, meta=meta,callback=self.parse_essay)
                        else:
                            self.logger.info('时间截止')
                            break
                except:
                    self.logger.info('Next page no more')
            else:
                continue

    def parse_essay(self,response):
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('.ts-news-content'):
            response.meta['title'] = i.select_one('a').text.strip()
            url = 'https://www.dainiktribuneonline.com' + i.select_one('a').get('href')
            yield Request(url=url, meta=response.meta,callback=self.parse_item)

    def parse_item(self,response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = None
        item['pub_time'] = Util.format_time2(soup.select_one('.time-share span').text.strip())
        item['body'] = ''.join(i.text.strip()+'\n' for i in soup.select('.story-desc p'))
        item['images'] = [i.get('src') for i in soup.select('.news-area img')]
        item['title'] = soup.select_one('.glb-heading h1').text.strip()
        item['abstract'] = soup.select_one('.glb-heading p').text.strip()
        return item


