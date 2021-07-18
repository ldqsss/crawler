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

class hindi_news(scrapy.Spider):
    name = 'three'
    website_id = 1133  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://hindi.mykhel.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_cxq',
        'password': 'dg_cxq',
        'db': 'dg_test'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(hindi_news, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response, **kwargs):
        html = BeautifulSoup(response.text, 'lxml')
        for i in html.select('div.os-more.clearfix > a'):
            if i.attrs['href'][0] == '/':
                yield Request('https://hindi.mykhel.com' + i.attrs['href'],callback=self.parse_2)

    def parse_2(self, response):
        page_soup = BeautifulSoup(response.text, 'lxml')
        if len(page_soup.select('article.article_content div.tag-content-left > a')):
            news_list = page_soup.select('article.article_content div.tag-content-left > a')#取出各个新闻的标签
            for i in news_list:
                news_url = 'https://hindi.mykhel.com' + i.attrs['href']
                yield Request(news_url,callback=self.parse_3)
            if page_soup.select('section div.prev-next-story.clearfix.click-for-more a.next.half_width')[
                                0].get('href'):
                next_page_url = 'https://hindi.mykhel.com/' + \
                                page_soup.select('section div.prev-next-story.clearfix.click-for-more a.next.half_width')[
                                    0].get('href')
                #得到第二页中最后一条新闻的url
                last_time_url = 'https://hindi.mykhel.com' + BeautifulSoup(requests.get(next_page_url).text,'lxml').select('article.article_content div.tag-content-left > a')[-1].attrs['href']
                #拿最后一条新闻的时间
                last_time = time_font(BeautifulSoup(requests.get(last_time_url).text,'lxml').select('div.os-breadcrumb div.os-posted-by time')[0].get('datetime'))
                if self.time == None or Util.format_time3(last_time) >= int(self.time):# 截止功能
                    if len(page_soup.select('section div.prev-next-story.clearfix.click-for-more a')):
                        yield Request(next_page_url,callback=self.parse_2)
                else:
                    self.logger.info('时间截至')
        elif len(page_soup.select('div.os-sports-m-news.clearfix div.os-more.clearfix a')):
            list_url = 'https://hindi.mykhel.com' + page_soup.select('div.os-sports-m-news.clearfix div.os-more.clearfix a')[0].get('href')
            yield Request(list_url,callback=self.parse_2)

    def parse_3(self, response):
        item = DemoItem()
        new_soup = BeautifulSoup(response.text, 'lxml')
        item['title'] = new_soup.select('div.os-breadcrumb > div.os-h-b h1.heading')[0].text
        item['body'] = ''
        for bodys in new_soup.select('div.os-sports-article-lt.os-lt p'):
            item['body'] += bodys.text
        if len(new_soup.select('div.os-sports-article-lt.os-lt p')):
            item['abstract'] = new_soup.select('div.os-sports-article-lt.os-lt p')[0].find('strong').text
        else:
            item['abstract'] = new_soup.select('div.os-sports-article-lt.os-lt p')[0].text
        item['images'] = []
        if len(new_soup.select('div.os-sports-article figure > strong > img')):
            new_images_list = new_soup.select('div.os-sports-article figure > strong > img')
            for new_images in new_images_list:
                item['images'].append(new_images.get('src'))
        item['pub_time'] = time_font(new_soup.select('div.os-breadcrumb div.os-posted-by time')[0].get('datetime'))
        item['category1'] = new_soup.select('div.os-breadcrumb div.os-breadcrumb-nav > nav > div')[1].find('span').text
        item['category2'] = new_soup.select('div.os-breadcrumb div.os-breadcrumb-nav > nav > div')[2].find('span').text
        yield item