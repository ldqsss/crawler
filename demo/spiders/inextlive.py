import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests

def time_font(time_past):
    #调整时间格式
    #Mon, 04 Jan 2021 16:50:33
    #%Y-%m-%d %H:%M:%S
    time = re.findall('.*?Date:(.*?)      .*?' , time_past)[0]
    day = time.split(' ')[2]
    month = time.split(' ')[3]
    year = time.split(' ' )[4]
    detail_time = time.split(' ')[5]
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
    return (year + '-' + month + '-' + day + ' ' + detail_time).strip("\t")
class inextlive(scrapy.Spider):
    name = 'one'
    website_id = 1127  # 网站的id(必填)
    language_id =1930 # 所用语言的id
    start_urls = ['https://www.inextlive.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_cxq',
        'password': 'dg_cxq',
        'db': 'dg_test'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(inextlive, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response, **kwargs):
        html = BeautifulSoup(response.text , 'lxml')
        test_page_list = []
        page_list = []
        # 解析一级目录
        test_page_list = html.select('div#mainNav.MainLMenu.tab li')
        for i in range(14):
            if i > 0:
                page_list.append(test_page_list[i].a['href'])
        test_page_list.clear()
        for i in page_list:
            test_page_list.append(i)
        page_list.clear()
        for each_test_url in test_page_list:
            try:
                test_url = BeautifulSoup(requests.get(each_test_url).text, 'lxml').select('article div.MainHd > h2 > a')
                if len(test_url):
                    for i in test_url:
                        page_list.append(i.get('href'))
                else:
                    page_list.append(each_test_url)
            except:
                self.logger.info('错误url: ' + each_test_url)
        for page in page_list:
            yield Request(page, callback=self.parse_1)

    def parse_1(self, response):
        page_soup = BeautifulSoup(response.text, 'lxml')
        # 如果可以换页
        if len(page_soup.select('article.topicBox div.pagination.border0 li.last')):
            next_page_url = page_soup.select('article.topicBox div.pagination.border0 li.last > a')[0].get('href')
            this_page_url = response.url
            j = 0
            # j决定爬取的页数
            while j < 3 and next_page_url:
                this_page_soup = BeautifulSoup(requests.get(this_page_url).text, 'lxml')
                news_url_list = this_page_soup.select('ul.topicList > li > a')
                last_new_url = news_url_list[-1].get('href')
                last_time = time_font(
                    BeautifulSoup(requests.get(last_new_url).text, 'lxml').select('div.articleHd div.dateInfo span.fl')[
                        0].text)
                if self.time == None or Util.format_time3(last_time) >= int(self.time):
                    for news_url in news_url_list:
                        yield Request(news_url.get('href'),callback=self.parse_2)
                else:
                    self.logger.info('时间截止')
                    break
                j = j + 1
                this_page_url = next_page_url
        elif len(page_soup.select('article.topicBox div.newsFJagran div.pagination.border0 ul > li')):
            self.logger.info('本页面特殊翻页: ' + response.url)
            j = 1
            this_page_url = response.url + '/' + str(j)
            while j < 3:
                this_page_soup = BeautifulSoup(requests.get(this_page_url).text, 'lxml')
                news_url_list = this_page_soup.select('ul.topicList > li > a')
                try:
                    last_new_url = news_url_list[-1].get('href')
                except:
                    self.logger.info(response.url)
                last_time = time_font(
                    BeautifulSoup(requests.get(last_new_url).text, 'lxml').select('div.articleHd div.dateInfo span.fl')[
                        0].text)
                if self.time == None or Util.format_time3(last_time) >= int(self.time):
                    for news_url in news_url_list:
                        Request(news_url.get('href') , callback=self.parse_2)
                else:
                    self.logger.info('时间截止')
                    break
                j = j + 1
                this_page_url = response.url + '/' + str(j)
        else:
            news_url_list = page_soup.select('ul.topicList > li > a')
            for news_url in news_url_list:
                last_time = time_font(BeautifulSoup(requests.get(news_url.get('href')).text ,'lxml').select('div.articleHd div.dateInfo span.fl')[0].text)
                if self.time == None or Util.format_time3(last_time) >= int(self.time):
                    yield Request(news_url.get('href'), callback=self.parse_2)

    def parse_2(self, response, **kwargs):
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
        new_soup = BeautifulSoup(response.text, 'lxml')
        item['title'] = new_soup.find('div', class_='topHeading', id='12').h1.string

        bodys = new_soup.select('article .articleBody > p')
        #文章内容
        for body_1 in bodys:
            item['body'] += body_1.text
        item['pub_time'] = time_font(new_soup.select('.articleHd .dateInfo .fl')[0].text)
        #图片url
        image_list = []
        if len(new_soup.find_all('img', id='jagran_image_id')):
            for image in new_soup.find_all('img', id='jagran_image_id'):
                image_list.append(
                    new_soup.find("body").select_one(".container .ls-area-body article .bodySummery").find("img").get("data-src"))
        item['images'] = image_list
        item['category1'] = new_soup.select('aside.breadcrum li.first > a > span')[0].string
        if len(new_soup.select('aside.breadcrum li:nth-of-type(3) > a > span')):
            item['category2'] = new_soup.select('aside.breadcrum li:nth-of-type(3) > a > span')[0].text
        else:
            item['category2'] = item['category1']
        if len(new_soup.select('aside.breadcrum li:nth-of-type(4) > span')):
            item['abstract'] = new_soup.select('aside.breadcrum li:nth-of-type(4) > span')[0].text
        else:
            item['abstract'] = new_soup.select('article .articleBody > p')[0].text
        yield item

