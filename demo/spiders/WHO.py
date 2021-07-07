import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from scrapy.http import Request, Response
import re
import time
from bs4 import BeautifulSoup
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


# author:刘鼎谦  finished_time:'2021-07-07 17:39:00'
# 新闻数很少, 用Rule爬了
class WhoSpider(CrawlSpider):
    name = 'WHO'
    allowed_domains = ['www.who.int']
    start_urls = [
        'https://www.who.int/southeastasia/news/detail',
        'https://www.who.int/myanmar/news'
                  ]   # 新闻不多，试着用Rule方法来写。

    website_id = 1432  # 网站的id(必填)
    language_id = 1866  # English
    sql = {  # my sql 配置
        'host': '121.36.242.178',
        'user': 'dg_ldq',
        'password': 'dg_ldq',
        'db': 'dg_test_source'
    }
    stopCount = 0

    rules = (   # 这几个Rule的先后顺序不能调换。
        Rule(LinkExtractor(allow=(r'southeastasia/news/detail/\d{2}-\d{2}\S+')),follow=True,callback='parse_item'),
        Rule(LinkExtractor(allow=(r'myanmar/news/\w+/detail/\S+')),follow=True,callback='parse_item'),
        Rule(LinkExtractor(allow=(r"southeastasia/news/detail/\d+")), follow=True),  # 翻页
        Rule(LinkExtractor(allow=(r'myanmar/news/\w+')), follow=True),  # myanmar下 有speech 等二级目录
    )
    # Rule 虽然简洁，但是 设置实践截止很麻烦

    def __init__(self, time=None, *args, **kwargs):
        super(WhoSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def _4matTime(self, time):
        timels=time.strip().split()
        time = timels[1]+' '+timels[0]+' '+timels[2]
        return Util.format_time2(time)



    def parse_item(self,response):
        soup = BeautifulSoup(response.text,'html.parser')
        item = DemoItem()
        try:
            pub_time = self._4matTime(soup.select_one('.timestamp').text)
        except:
            pub_time = Util.format_time(0)
        if self.time is None or Util.format_time3(pub_time) > int(self.time):   # 时间截止，遍历了所有url，没能截止下来
            item['pub_time']=pub_time
            item['title'] =soup.select('.active')[-1].text.strip()
            item['category1'] = response.url.split('/')[3]
            item['category2'] = response.url.split('/')[5] if response.url.split('/')[3] == 'myanmar' else 'news'
            item['body'] = soup.select_one('article').text.strip()
            item['abstract'] = soup.select_one('article').text.strip().split('\n')[0]
            item['images'] = [i.get('src') for i in soup.select_one('section').select('img')]
            return item
        else:
            self.logger.info('时间截止')
            self.stopCount +=1


