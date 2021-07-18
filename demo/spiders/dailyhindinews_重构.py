import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests

def time_font(time_past):
    #2021-01-08T02:35:30+05:30
    #%Y-%m-%d %H:%M:%S
    big_time = time_past.split('T')[0]
    small_time = time_past.split('T')[1].split('+')[0]
    return big_time + ' ' + small_time

class dailyhindinews(scrapy.Spider):
    name = 'two'
    website_id = 1130  # 网站的id(必填)
    language_id = 1740  # 所用语言的id
    start_urls = ['https://www.dailyhindinews.com//']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_cxq',
        'password': 'dg_cxq',
        'db': 'dg_test'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(dailyhindinews, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response, **kwargs):
        html = BeautifulSoup(response.text, 'lxml')
        url_list_1 = html.select('div#primary > main#main.site-main > div > a')
        url_list_2 = html.select('div#primary > main#main.site-main > div > div > a')
        column_url_list = []

        for column in url_list_1:
            column_url_list.append(column.get('href'))
        for column in url_list_2:
            column_url_list.append(column.get("href"))

        for column in column_url_list:
            yield Request(column , callback=self.parse_2)

    def parse_2(self, response, **kwargs):
        soup = BeautifulSoup(response.text, 'lxml')
        for i in soup.select('article > a'):
            yield Request(i.attrs['href'], callback=self.parse_3)
        if soup.select('div.nav-links a.next.page-numbers')[0].attrs['href']:
            next_page = soup.select('div.nav-links a.next.page-numbers')[0].attrs['href']
            last_time_url = BeautifulSoup(requests.get(next_page).text,'lxml').select('article > a')[-1].attrs['href']
            last_time = time_font(BeautifulSoup(requests.get(last_time_url).text,'lxml').select('header.entry-header > div.entry-meta > span.posted-on > a > time')[0].get('datetime'))
            if self.time == None or Util.format_time3(last_time) >= int(self.time):
                next_page = soup.select('div.nav-links a.next.page-numbers')[0].attrs['href']
                yield Request(next_page,callback=self.parse_2)
            else:
                self.logger.info('时间截止')

    def parse_3(self , response , **kwargs):
        new_soup = BeautifulSoup(response.text, 'lxml')
        item = DemoItem()
        item = {
            'title': '',
            'body': '',
            'pub_time': '',
            'category1': '',
            'category2': '',
            'images': [],
            'abstract': ''
        }
        item['title'] = new_soup.select("div#primary > main#main > article > header.entry-header > h1")[0].string
        item['abstract'] = new_soup.select('div#primary > main#main > article > div.entry-content > p')[0].text
        body_list = new_soup.select('div#primary > main#main > article > div.entry-content > p')
        for each_body in body_list:
            item['body'] += each_body.text
        image_list = new_soup.select('div#primary > main#main > article > div.entry-content > p > img')
        for each_image_list in image_list:
            item['images'].append(each_image_list.get('src'))
        item['pub_time'] = time_font(
            new_soup.select('header.entry-header > div.entry-meta > span.posted-on > a > time')[0].get('datetime'))
        item['category1'] = new_soup.select('header.entry-header > div.cat-links > a')[0].text
        if len(new_soup.select('header.entry-header > div.cat-links > a')):
            item['category2'] = new_soup.select('header.entry-header > div.cat-links > a')[1].text
        else:
            item['category2'] = item['category1']
        yield item