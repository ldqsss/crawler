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
    #调整时间格式
    # September 8, 2020,  11:55 pm
    #%Y-%m-%d %H:%M:%S
    big_time = time_past[5].string.strip(' ')#July 14, 2020,
    small_time = time_past[6].string.strip(' ')#11:31 AM
    day = big_time.split(' ')[1].strip(',')
    month = big_time.split(' ')[0]
    year = big_time.split(' ' )[2].strip(',')
    hour = small_time.split(' ')[0].split(':')[0]
    minute = small_time.split(' ')[0].split(':')[1]
    half = small_time.split(' ')[1]
    if half == 'pm':
        hour = int(hour) + 11
    hour = str(hour)
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
    return year + '-' + month + '-' + day + ' ' + hour + ':' + minute + ':00'

class inkhabar(scrapy.Spider):
    name = 'inkhabar'
    website_id = 1135 # 网站的id(必填)
    language_id = 1740 # 所用语言的id
    start_urls = ['https://www.inkhabar.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_cxq',
        'password': 'dg_cxq',
        'db': 'dg_test'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(inkhabar, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response, **kwargs):
        for i in BeautifulSoup(response.text , 'lxml').select('div.row h2.panel-title a')[0:12]:
            if i.get('href') != '#':
                yield Request(i.get('href'),callback=self.parse_2)

    def parse_2(self, response , **kwargs):
        news_list = BeautifulSoup(response.text,'lxml').select('div.col-md-8.cat-grid-gap div.well.ft2 div.thumbnail > a')
        j = 5
        #由于该网页二级目录没有翻页功能，因此自己规定每五条新闻为一页
        for i in range(len(news_list)):
            if i + j >= len(news_list):
                time_url = news_list[len(news_list) - 1].get('href')
                time_ = time_font(
                    BeautifulSoup(requests.get(time_url).text, 'lxml').select('ul.story-update-details > li'))
                if Util.format_time3(time_) < int(self.time):
                    self.logger.info('时间截止')
                    break
            else:
                time_url = news_list[i + j].get('href')
                time_ = time_font(
                    BeautifulSoup(requests.get(time_url).text, 'lxml').select('ul.story-update-details > li'))
                if Util.format_time3(time_) < int(self.time):
                    self.logger.info('时间截止')
                    break
            yield Request(news_list[i].get('href'),callback=self.parse_3)

    def parse_3(self , response , **kwargs):
        item = DemoItem()
        new_soup = BeautifulSoup(response.text, 'lxml')
        if len(new_soup.select('div.story-title h1')):
            item['title'] = new_soup.select('div.story-title h1')[0].text.strip('\n').strip(' ')
        item['body'] = ''
        if len(new_soup.select('div.article-body')):
            bodys = new_soup.select('div.article-body')[0]
            # 文章内容
            boby = ''
            for body_1 in bodys.select('p'):
                if body_1.string:
                    item['body'] += body_1.string.strip('\n')
        else:
            self.logger.info('body异常:' + response.url)
        times_list = new_soup.select('ul.story-update-details > li')
        item['pub_time'] = time_font(times_list)
        # 图片url
        item['images'] = []
        if len(new_soup.select('div#featuredimage picture img')):
            for image in new_soup.select('div#featuredimage picture img'):
                item['images'].append(image.get('src'))
        item['category1'] = new_soup.select('ol.breadcrumb > li')[0].find('span', itemprop='name').string
        item['category2'] = new_soup.select('ol.breadcrumb > li')[1].find('span', itemprop='name').string
        item['abstract'] = ''
        if len(new_soup.select('div.story-short-title h2')):
            item['abstract'] = new_soup.select('div.story-short-title h2')[0].string
        else:
            item['abstract'] = new_soup.select('div.article-body p')[0].string.strip(' ').strip('\n')
        yield item