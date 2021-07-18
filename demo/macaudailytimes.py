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

def time_font(time):
    #Wednesday, July 7, 2021 - 11 hours ago
    #%Y-%m-%d %H:%M:%S
    time_past = time.split('-')[0].strip(' ')
    month = time_past.split(' ')[1]
    day = time_past.split(' ')[2].strip(',')
    year = time_past.split(' ')[3]
    if month == 'Jan':
        month = '01'
    elif month == 'Feb':
        month = '02'
    elif month == 'Mar':
        month = '03'
    elif month == 'Apr':
        month = '04'
    elif month == 'May':
        month = '05'
    elif month == 'Jun':
        month = '06'
    elif month == 'Jul':
        month = '07'
    elif month == 'Aug':
        month = '08'
    elif month == 'Sep':
        month = '09'
    elif month == 'Oct':
        month = '10'
    elif month == 'Nov':
        month = '11'
    else:
        month = '12'
    return year + '-' + month + '-' + day + ' ' + '00:00:00'

class macaudailytimes(scrapy.Spider):
    name = 'macaudailytimes_spider'
    website_id = 675 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.macaudailytimes.com.mo']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_cxq',
        'password': 'dg_cxq',
        'db': 'dg_test'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(macaudailytimes, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response, **kwargs):
        soup = BeautifulSoup(response.text,'lxml')

    def _parse(self, response, **kwargs):
        news_soup = BeautifulSoup(response.text, 'lxml')
        for i in news_soup.find('ul', class_='top-menu').find_all('li'):
            yield Request(i.find('a').get('href'),callback=self.parse2)

    def parse2(self,response):
        page = BeautifulSoup(response.text, 'lxml')
        for i in page.find('div',class_='grid-3-4 list-one-col').find_all('div',class_='blog-item'):
            title = i.find_all('a')[-1].text
            img = i.find('img').get('src')
            news_time = time_font(i.find('div',class_='meta-data').find_all('span')[1].text.strip(' '))
            if self.time == None or Util.format_time3(news_time) >= int(self.time):
                yield  Request(i.find_all('a')[-1].get('href'),callback=self.parse3,meta={'title':title,'img':img,'time':news_time})
        last_time = time_font(page.find('div',class_='grid-3-4 list-one-col').find_all('div',class_='blog-item')[-1].find('div',class_='meta-data').find_all('span')[1].text.strip(' '))
        if self.time == None or Util.format_time3(last_time) >= int(self.time):
            yield Request(page.find('ul',class_='pagination').find_all('li')[-2].find('a').get('href'),callback=self.parse2)

    def parse3(self,response):
        item = DemoItem()
        new_soup = BeautifulSoup(response.text,'lxml')
        item['pub_time'] = response.meta['time']
        item['title'] = response.meta['title']
        item['images'] = response.meta['img']
        item['body'] = ''
        for i in new_soup.find('div', class_='entry').find_all('p'):
            item['body'] += i.text.strip('\n').strip(' ')
        item['category1'] = ''
        item['category2'] = ''
        yield item