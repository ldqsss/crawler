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
    #March 13, 2021
    #%Y-%m-%d %H:%M:%S
    month = time_past.split(' ')[0]
    day = time_past.split(' ')[1].strip(',')
    year = time_past.split(' ')[2]
    if month == 'January':
        month = '01'
    elif month == 'February':
        month = '02'
    elif month == 'March':
        month = '03'
    elif month == 'April':
        month = '04'
    elif month == 'May':
        month = '05'
    elif month == 'June':
        month = '06'
    elif month == 'July':
        month = '07'
    elif month == 'August':
        month = '08'
    elif month == 'September':
        month = '09'
    elif month == 'October':
        month = '10'
    elif month == 'November':
        month = '11'
    else:
        month = '12'
    return year + '-' + month + '-' + day + ' 00:00:00'

def time_font_2(past_time):
    #2021 25 March
    year = past_time.split(' ')[0]
    day = past_time.split(' ')[1]
    month = past_time.split(' ')[2]
    if month == 'January':
        month = '01'
    elif month == 'February':
        month = '02'
    elif month == 'March':
        month = '03'
    elif month == 'April':
        month = '04'
    elif month == 'May':
        month = '05'
    elif month == 'June':
        month = '06'
    elif month == 'July':
        month = '07'
    elif month == 'August':
        month = '08'
    elif month == 'September':
        month = '09'
    elif month == 'October':
        month = '10'
    elif month == 'November':
        month = '11'
    else:
        month = '12'
    return year + '-' + month + '-' + day + ' 00:00:00'

class ujjawalprabhat(scrapy.Spider):
    name = 'ujjawalprabhat_spider'
    website_id = 1143 # 网站的id(必填)
    language_id = 1740 # 所用语言的id
    start_urls = ['https://ujjawalprabhat.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_cxq',
        'password': 'dg_cxq',
        'db': 'dg_test'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(ujjawalprabhat, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response, **kwargs):
        html = BeautifulSoup(response.text,'lxml')
        for i in html.find('ul', id='menu-main-menu', class_='menu', role='menubar').find_all('a')[1:]:
            if i.attrs['href'] != '#':
                yield Request(i.attrs['href'],callback=self.parse_2)

    def parse_2(self,response,**kawargs):
        page = BeautifulSoup(response.text, 'lxml')
        category1 = page.find('h1', class_='page-title').text
        if page.find('ul', id='posts-container', class_='posts-items') != None:
            for i in page.find('ul', id='posts-container', class_='posts-items').find_all('a', class_='post-thumb'):
                images = i.find('img').get('data-src')
                yield Request(i.attrs['href'],callback=self.parse_3,meta={'images':images,'category1':category1})
        else:
            for i in page.find('div', class_='masonry-grid-wrapper masonry-with-spaces').find_all('div',
                                                                                                  class_='featured-area'):
                images = i.find('img').get('data-src')
                yield Request(i.find('a').get('href'), callback=self.parse_3, meta={'images':images,'category1':category1})
        #看能否爬下一页
        if page.find('span', class_='last-page first-last-pages') != None:
            next_page = page.find('span', class_='last-page first-last-pages').find('a').attrs['href']
            if page.find('div', class_='year-month') != None:
                time = page.find('div', class_='year-month').find('em').text.strip('-').strip(' ') + ' ' + \
                       page.find('div', class_='mag-box-container clearfix').find_all('div', class_='day-month')[
                           -1].text
                pub_time = time_font_2(time)
            elif page.find('div', class_='masonry-grid-wrapper masonry-with-spaces') != None:
                pub_time = time_font(
                    page.find('div', class_='masonry-grid-wrapper masonry-with-spaces').find_all('span',class_='date meta-item tie-icon')[-1].text)
            elif page.find('ul', id='posts-container', class_='posts-items') != None:
                pub_time = time_font(page.find('ul', id='posts-container', class_='posts-items').find_all('span',class_='date meta-item tie-icon')[-1].text)
            if self.time == None or Util.format_time3(pub_time) >= int(self.time):
                yield Request(next_page,callback=self.parse_2)
        #这是第二种二级目录
        elif page.find('li', class_='the-next-page') != None:
            next_page = page.find('li', class_='the-next-page').find('a').attrs['href']
            if page.find('div', class_='year-month') != None:
                time = page.find('div', class_='year-month').find('em').text.strip('-').strip(' ') + ' ' + \
                       page.find('div', class_='mag-box-container clearfix').find_all('div', class_='day-month')[
                           -1].text
                pub_time = time_font_2(time)
            elif page.find('div', class_='masonry-grid-wrapper masonry-with-spaces') != None:
                pub_time = time_font(
                    page.find('div', class_='masonry-grid-wrapper masonry-with-spaces').find_all('span',class_='date meta-item tie-icon')[-1].text)
            elif page.find('ul', id='posts-container', class_='posts-items') != None:
                pub_time = time_font(page.find('ul', id='posts-container', class_='posts-items').find_all('span',class_='date meta-item tie-icon')[-1].text)
                if self.time == None or Util.format_time3(pub_time) >= int(self.time):
                    yield Request(next_page, callback=self.parse_2)

    def parse_3(self,response,**kwargs):
        item = DemoItem()
        new_soup = BeautifulSoup(response.text, 'lxml')
        item['category1'] = response.meta['category1']
        item['images'] = response.meta['images']
        item['body'] = ''
        item['pub_time'] = time_font(new_soup.find('span', class_='date meta-item tie-icon').text)
        if new_soup.find('div', class_='entry-content entry clearfix') != None:
            for i in new_soup.find('div', class_='entry-content entry clearfix').find_all('p'):
                item['body'] += i.text
            item['abstract'] = new_soup.find('div', class_='entry-content entry clearfix').find('p').text
        else:
            item['body'] = new_soup.find('div', class_='entry-content entry clearfix').text
            item['abstract'] = item['body'].strip('\n').split('\n')[0]
        yield item