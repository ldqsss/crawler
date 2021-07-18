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
    #July 6, 2020
    #%Y-%m-%d %H:%M:%S
    time_past = time_past.strip(" ").strip('\n')
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
    elif month == 'Jun':
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
    return year + '-' + month + '-' + day + ' ' + '00:00:00'

class apnlive(scrapy.Spider):
    name = 'apnlive_spider'
    website_id = 1140 # 网站的id(必填)
    language_id = 1930 # 所用语言的id
    start_urls = ['https://hindi.apnlive.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_cxq',
        'password': 'dg_cxq',
        'db': 'dg_test'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(apnlive, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response, **kwargs):
        #先得到初始页的bs4
        html = BeautifulSoup(response.text,'lxml')
        for i in html.find('ul' , id='menu-menu' , class_='tdb-block-menu tdb-menu tdb-menu-items-visible').select('a'):
            yield Request(i.attrs['href'] , callback=self.parse_2)

    def parse_2(self, response, **kwargs):
        page = BeautifulSoup(response.text,'lxml')
        for i in page.find_all('div', class_='tdb_module_loop td_module_wrap td-animation-stack'):
            yield Request(i.find('div',class_='td-module-meta-info').find('a').get('href'),callback=self.parse_3)
        #确认是否有新闻
        if page.find('div',class_='page-nav td-pb-padding-side') != None:
            #确认是否可以翻页
            if len(page.find_all('div', class_='tdb_module_loop td_module_wrap td-animation-stack')) != 0:
                page_time = time_font(page.find_all('div', class_='tdb_module_loop td_module_wrap td-animation-stack')[-1].find('time' ,class_='entry-date updated td-module-date').text)
                if self.time == None or Util.format_time3(page_time) >= int(self.time):
                    yield Request(page.find('div',class_='page-nav td-pb-padding-side').select('a')[-1].attrs['href'], callback=self.parse_2)

    def parse_3(self, response, **kwargs):
        item = DemoItem()
        new_soup = BeautifulSoup(response.text,'lxml')
        item['title'] = new_soup.find('header', class_='td-post-title').find('h1', class_='entry-title').text
        item['category1'] = new_soup.find('div', class_='entry-crumbs').select('span')[1].text
        if len(new_soup.find('div', class_='entry-crumbs').select('span')) >= 4:
            item['category2'] = new_soup.find('div', class_='entry-crumbs').select('span')[2].text
        item['body'] = ''
        for i in new_soup.find('div', class_='td-pb-span8 td-main-content').select(
                'div.wpb_wrapper div.td-fix-index p'):
            item['body'] += i.text.strip('\n').strip(' ')
        if new_soup.find('p', class_='td-post-sub-title') != None:
            item['abstract'] = new_soup.find('p', class_='td-post-sub-title').text
        else:
            item['abstract'] = item['title']
        item['images'] = new_soup.find('div', class_='td-post-featured-image').a['href']
        item['pub_time'] = time_font(new_soup.find('span', class_='td-post-date').text)
        yield item