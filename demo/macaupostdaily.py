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

class macaupostdaily(scrapy.Spider):
    name = 'macaupostdaily_spider'
    website_id = 674 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.macaupostdaily.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_cxq',
        'password': 'dg_cxq',
        'db': 'dg_test'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(macaupostdaily, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response, **kwargs):
        header = {
            'Accept': 'application/json,text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Length': '11',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': 'PHPSESSID=h2q86fctchauhq3ngeg8cu2ld7',
            'Host': 'www.macaupostdaily.com',
            'Origin': 'https://www.macaupostdaily.com',
            'Referer': 'https://www.macaupostdaily.com/',
            'sec-ch-ua': 'Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
            'sec-ch-ua-mobile': '?0',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        url = 'https://www.macaupostdaily.com/'
        url_list = []
        time_list = []
        title_list = []
        img_list = []

        news_soup = BeautifulSoup(response.text,'lxml')
        for i in news_soup.find('ul', class_='new_list', id='fu').find_all('li'):
            url_list.append('https://www.macaupostdaily.com' + i.find('a').get('href'))
            time_list.append(i.find('div', class_='time').text.strip('\n').strip(' ') + ":00")
            title_list.append(i.find('strong').text.strip('\n'))
            img_list.append(url + i.find('img').get('src'))

        request_url = 'https://www.macaupostdaily.com/index.php/Article/news_list'

        # 后面post得到的url
        i = 2
        while(i):
            Data = {
                'cid': '',
                'page': "%d" % i
            }

            rep = requests.post(url=request_url, data=Data, headers=header).json()
            for list in rep['list']:
                url_list.append("https://www.macaupostdaily.com/article" + list['id'] + ".html")
                title_list.append(list['title'])
                time_list.append(list['time'] + ":00")
                img_list.append('https://www.macaupostdaily.com' + list['img'])
            for new in range(0,len(url_list)):
                if self.time == None or Util.format_time3(time_list[new]) >= int(self.time):
                    yield Request(url_list[new],callback=self.parse_2,meta={'time':time_list[new],
                                                                          'title':title_list[new],'img':img_list[new]})
            if Util.format_time3(time_list[-1]) < int(self.time):
                break
            url_list = []
            time_list = []
            img_list = []
            title_list = []
            i = i + 1

    def parse_2(self,response):
        new_soup = BeautifulSoup(response.text , 'lxml')
        item = DemoItem()
        item['pub_time'] = response.meta['time']
        item['title'] = response.meta['title']
        item['images'] = response.meta['img']
        item['body'] = ''
        for i in new_soup.find('div', class_='art_cont').find_all('p'):
            item['body'] += i.text.strip('\n').strip(' ')
        item['category1'] = ''
        item['category2'] = ''
        yield item

