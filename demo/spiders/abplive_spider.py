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
    # 15 Jan 2021 12:04 PM
    # By : एबीपी न्यूज़ | Updated: 15 Jan 2021 12:42 PM (IST)
    # %Y-%m-%d %H:%M:%S
    if len(re.findall(r'By: .*? \| (\d+ \S+ \d+ \d+:\d+ \S+)', time_past)):
        time_past = re.findall(r'By: .*? \| (\d+ \S+ \d+ \d+:\d+ \S+)', time_past)
    elif len(re.findall(r'Updated: (\d+ \S+ \d+ \d+:\d+ \S+)', time_past)):
        time_past = re.findall(r'Updated: (\d+ \S+ \d+ \d+:\d+ \S+)', time_past)
    elif len(re.findall(r'Updated : (\d+ \S+ \d+ \d+:\d+ \S+)', time_past)):
        time_past = re.findall(r'Updated : (\d+ \S+ \d+ \d+:\d+ \S+)', time_past)
    month = time_past[0].split(' ')[1]
    year = time_past[0].split(' ')[2]
    day = time_past[0].split(' ')[0]
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
    return year + '-' + month + '-' + day + ' ' + time_past[0].split(' ')[3] + ":00"

class abplive(scrapy.Spider):
    name = 'abplive'
    website_id = 1136 # 网站的id(必填)
    language_id = 1930 # 所用语言的id
    start_urls = ['https://www.abplive.com']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_cxq',
        'password': 'dg_cxq',
        'db': 'dg_test'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(abplive, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response, **kwargs):
        html = BeautifulSoup(response.text,'lxml')
        for i in html.select('div.custom_menuitems._zindx span._r_t > a')[0:13]:
            yield Request(i.attrs['href'],callback=self.parse_2)
        for i in html.select('div.custom_menuitems._zindx span._r_t')[-1].select('div > span > a')[1:19]:
            yield Request(i.attrs['href'],callback=self.parse_2)

    def parse_2(self,response, **kwargs):
        soup = BeautifulSoup(response.text,'lxml')
        #若有新闻列表
        if len(soup.select('div.other_news > a')):
            for i in soup.select('div.uk-width-expand.uk-first-column div.other_news > a')[:-1]:
                yield Request(i.attrs['href'],callback=self.parse_3)
            #是否可以换页
            if len(soup.select('ul.pagination > li')) > 3:
                next_url = soup.select('ul.pagination > li')[-2].find('a').attrs['href']
                #取当前页的最后一条新闻url
                last_new = soup.select('div.other_news > a')[-1].attrs['href']
                # 选取最后一篇新闻给parse_judge进行判断，判断通过后就将下一页的爬取
                response.meta['don_t filter'] = True
                yield Request(last_new, callback=self.parse_judge,meta={'next_url':next_url}, dont_filter=True)

    #用于判断是否截至
    def parse_judge(self,response):
        response.meta['dont_filter'] = False
        next_url = response.meta['next_url']
        last_new = response.url
        #判断是否要爬取
        if len(BeautifulSoup(requests.get(last_new).text, 'lxml').select('p.article-author')):
            last_time = time_font(BeautifulSoup(requests.get(last_new).text, 'lxml').select('p.article-author')[0].text)
            if self.time == None or Util.format_time3(last_time) >= int(self.time):  # 截止功能
                yield Request(next_url,meta=response.meta, callback=self.parse_2)
            else:
                self.logger.info('时间截至')
        elif len(BeautifulSoup(requests.get(last_new).text, 'lxml').find_all('span', id='dateSpanElem')):
            last_time = time_font(
                BeautifulSoup(requests.get(last_new).text, 'lxml').find_all('span', id='dateSpanElem')[0].text)
            if self.time == None or Util.format_time3(last_time) >= int(self.time):  # 截止功能
                yield Request(next_url,meta=response.meta ,callback=self.parse_2)
            else:
                self.logger.info('时间截至')
        #最后将该文章爬了
        yield Request(response.url,callback=self.parse_3)

    def parse_3(self,response, **kwargs):
        new_soup = BeautifulSoup(response.text, 'lxml')
        if len(new_soup.select('p.article-author')):
            item = DemoItem()
            item['body'] = ''
            if len(new_soup.find_all('div', style='text-align: justify;')):
                item['abstract'] = new_soup.find('div', style='text-align: justify;').text
                for i in new_soup.find_all('div', style='text-align: justify;'):
                    item['body'] += i.text
            elif len(new_soup.find_all('p', style='text-align: justify;')):
                item['abstract'] = new_soup.find('p', style='text-align: justify;').text
                for i in new_soup.find_all('p', style='text-align: justify;'):
                    item['body'] += i.text
            item['title'] = new_soup.find('h1', class_='article-title').text
            item['abstract'] = ''
            if len(new_soup.find_all('h2', class_='article-excerpt')):
                item['abstract'] = new_soup.find('h2', class_='article-excerpt').text
            item['images'] = []
            if len(new_soup.find_all('div', class_='news_featured cont_accord_to_img')):
                item['images'].append(
                    new_soup.find_all('div', class_='news_featured cont_accord_to_img')[0].find('img').get('data-src'))
            if len(new_soup.find('ul', class_='uk-breadcrumb').select('li > a')):
                item['category1'] = new_soup.find('ul', class_='uk-breadcrumb').select('li > a')[0].text
                item['category2'] = new_soup.find('ul', class_='uk-breadcrumb').select('li > a')[1].text
            item['pub_time'] = time_font(new_soup.select('p.article-author')[0].text)
            yield item