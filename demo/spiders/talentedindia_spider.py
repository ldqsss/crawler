# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests
from datetime import datetime

def time_font(time_past):
    #2021-02-09T17:15:51+05:30
    #%Y-%m-%d %H:%M:%S
    big_time = time_past.split('T')[0]
    small_time = time_past.split('T')[1]
    small_time = small_time.split('+')[0]
    return big_time + ' ' + small_time

class talentedindia(scrapy.Spider):
    name = 'talentedindia_spider'
    website_id = 1141 # 网站的id(必填)
    language_id = 1740 # 所用语言的id
    start_urls = ['https://www.talentedindia.co.in/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_cxq',
        'password': 'dg_cxq',
        'db': 'dg_test'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(talentedindia, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response, **kwargs):
        html = BeautifulSoup(response.text,'lxml')
        for i in html.find('ul', id='menu-main-menu', class_='menu').find_all('a')[1:]:
            yield Request(i.attrs['href'],callback=self.parse_2)

    def parse_2(self, response, **kwargs):
        page = BeautifulSoup(response.text,'lxml')
        category1 = page.find('div', class_='breadcrumbs').find('span', class_='current').text
        for i in page.find_all('div', class_='column half b-col'):
            yield Request(i.find('a',class_='image-link').get('href'), callback=self.parse_3,meta={'category1':category1})

        page_time = time_font(page.find_all('div', class_='column half b-col')[-1].find('time').get('datetime'))
        #判断是否要爬下一页
        if page.find('a',class_='next page-numbers') != None:
            if self.time == None or Util.format_time3(page_time) >= int(self.time):
                yield Request(page.find('a',class_='next page-numbers').attrs['href'],callback=self.parse_2)

    def parse_3(self, response, **kwargs):
        item = DemoItem()
        new_soup = BeautifulSoup(response.text,'lxml')
        item['title'] = new_soup.find('h1', class_='post-title item fn').text
        item['category1'] = response.meta['category1']
        item['category2'] = ''
        item['abstract'] = new_soup.find('div', class_='post-container cf').find_all('p')[1].text
        item['body'] = ''
        for i in new_soup.find('div', class_='post-container cf').find_all('p'):
            item['body'] += i.text
        item['pub_time'] = time_font(new_soup.find('time', class_='value-title').get('datetime'))
        item['images'] = new_soup.find('div', class_='featured').find('a').get('href')
        yield item