# coding:utf8
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import json
import requests
import re
import random
import time
import os

user = os.environ.get("User")
pwd = os.environ.get("Pwd")


def login_get_cookie(browser, url):
    browser.get(url)
    username = browser.find_element_by_name("account")
    username.clear()
    username.send_keys(user)
    password = browser.find_element_by_name("password")
    password.clear()
    password.send_keys(pwd)
    login_button = browser.find_element_by_css_selector("div.login_btn_panel > a.btn_login")
    login_button.send_keys(Keys.ENTER)
    print("请扫码登陆，再任意输入继续运行")
    input()
    cookies = {}
    cookie_items = browser.get_cookies()  # 获取到的cookie是列表
    print(cookie_items)
    print("---------------------------------")
    for cookie_item in cookie_items:
        cookies[cookie_item['name']] = cookie_item['value']
    print(cookies)
    write_json("cookies.json", cookies)


def write_json(file, content):
    with open(file, "w", encoding="utf8")as f:
        json.dump(content, f, ensure_ascii=False,indent="\t")


def read_return_cookies(file="cookies.json"):
    with open(file, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    return cookies


def get_token(url, cookies):
    # 登录之后的微信公众号首页url变化为：https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=1849751598，从这里获取token信息,后面需要用到
    response = requests.get(url=url, cookies=cookies)
    token = re.findall(r'token=(\d+)', str(response.url))[0]
    return token


# 获取这个公众号的fakeid，后面爬取公众号文章需要此字段
def get_fakeid(search_url, cookies, token, query):
    header = {"HOST": "mp.weixin.qq.com",
              "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0"}
    # 搜索微信公众号接口需要传入的参数，有三个变量：微信公众号token、随机数random、搜索的微信公众号名字query
    query_id = {'action': 'search_biz', 'token': token, 'lang': 'zh_CN', 'f': 'json', 'ajax': '1',
                'random': random.random(), 'query': query, 'begin': '0',
                'count': '5'}

    # 打开搜索微信公众号接口地址，需要传入相关参数信息如：cookies、params、headers
    search_response = requests.get(search_url, cookies=cookies, headers=header, params=query_id)

    # 取搜索结果中的第一个公众号
    lists = search_response.json().get('list')[0]

    fakeid = lists.get('fakeid')
    return fakeid  # 公众号标识


def get_article_title(appmsg_url, cookies, token, fakeid):
    header = {
        "HOST": "mp.weixin.qq.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0"
    }
    articles = list()
    for j in range(0, 201, 5):
        try:
            # 搜索文章需要传入几个参数：登录的公众号token、要爬取文章的公众号fakeid、随机数random
            param = {'token': token, 'lang': 'zh_CN', 'f': 'json', 'ajax': '1', 'random': random.random(),
                     'action': 'list_ex',
                     'begin': str(j),  # 不同页，此参数变化，变化规则为每页加5
                     'count': '5', 'query': '', 'fakeid': fakeid, 'type': '9'}
            # 打开搜索的微信公众号文章列表页
            appmsg_response = requests.get(appmsg_url, cookies=cookies, headers=header, params=param)
            print("\r爬取进度为{}%".format(j / 200 * 100), end="")
            max_num = appmsg_response.json().get('app_msg_cnt')
            print(max_num)
            if j % 20 == 0:
                time.sleep(random.randrange(3, 5))
            for i in appmsg_response.json().get('app_msg_list'):
                article = {}
                article["title"] = i.get("title")
                article["link"] = i.get("link")
                articles.append(article)
            print("        %d" % len(articles))
        except Exception as e:
            print(repr(e))
            time.sleep(5)
    return articles


def main():
    browser = webdriver.Firefox()
    url = "https://mp.weixin.qq.com/"
    query = "新浪娱乐"
    login_get_cookie(browser, url)
    token = get_token(url, read_return_cookies())
    print(token)

    # 搜索微信公众号的接口地址
    search_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?'
    fakeid = get_fakeid(search_url, read_return_cookies(), token, query)
    print(fakeid)

    # 微信公众号文章接口地址
    appmsg_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg?'
    articles = get_article_title(appmsg_url, read_return_cookies(), token, fakeid)

    write_json("articles.json", articles)


if __name__ == '__main__':
    main()
