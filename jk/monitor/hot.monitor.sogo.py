# coding:utf-8
# __author__ = chenzhengqiang
# __date__ = 2018/03/21

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import time
import argparse
import urlparse
from selenium import webdriver
from bs4 import BeautifulSoup
from pyvirtualdisplay import Display
from pymongo import MongoClient
import datetime
from selenium.webdriver.chrome.options import Options

G_FIRSTPAGE="https://wap.sogou.com/web/searchList.jsp?keyword={0}"
G_SECONDPAGE="https://wap.sogou.com/web/search/ajax_query.jsp?keyword={0}&p=2"

def statistics(url, keyword, driver, page=0, rankings = None):
    '''
    :param url: the sogo page url
    :param keyword: 感冒了怎么办
    :param driver:  the instance of firefox driver
    :param page: 0,1
    :param rankings: as the following
    :return: rankings
    '''

    if rankings is None:
        rankings = {"_id":keyword, "rankings": [{}, {}],
                    "results": 0, "natural": 0, "vr": 0}
    count = 0
    timeout_count = 0

    while True:
        try:
            driver.get(url.format(keyword))
            html = driver.execute_script("return document.documentElement.outerHTML")
        except Exception,e:
            print e
            timeout_count +=1
            print timeout_count
            html = ""
            time.sleep(3)

        if html or timeout_count >=3:
            break

    if html:
        soup = BeautifulSoup(html, 'lxml')
        for item in soup.find_all("h3", class_="vr-tit"):
            for child in item.children:
                if child.name == "a":
                    count += 1
                    try:
                        url_quries = urlparse.parse_qs(urlparse.urlparse(child["href"]).query)
                    except:
                        continue

                    if "url" not in url_quries:
                        continue

                    for url in url_quries["url"]:
                        if url.find("m.169kang.com") != -1:
                            rankings["results"] += 1
                            url_quries = urlparse.parse_qs(urlparse.urlparse(url).query)
                            if not url_quries or 'z' in url_quries:
                                rankings["rankings"][page][str(count)] = 0  # natural search
                                rankings["natural"] += 1
                            else:
                                rankings["rankings"][page][str(count)] = 1  # vr search
                                rankings["vr"] += 1
    return rankings

if __name__ == "__main__":
    
    mongo_conn = MongoClient("10.5.0.78", 38000)
    db = mongo_conn["hot_wap"]
    display = Display(visible=0, size=(800,600))
    display.start()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0"
    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override", user_agent)
    driver = webdriver.Firefox(firefox_profile = profile, executable_path="/home/backer/backer/monitor/geckodriver")
    driver.set_page_load_timeout(30)
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    count = 0

    with open("./hot.txt") as f:
        for line in f:
            keyword = line.strip().replace("\r\n", "").replace("\n", "")
            if not keyword:
                continue
            rankings = statistics(G_FIRSTPAGE, keyword, driver)
            time.sleep(0.3)
            rankings = statistics(G_SECONDPAGE,keyword, driver,1, rankings)
            time.sleep(0.3)
            db[today_str].save(rankings)
            count += 1

    # query = u"艾滋病初期症状"
    # element = driver.find_element_by_id("keyword")
    # element.clear()
    # element.send_keys(query)

    # driver.find_element_by_class_name('qbtn').click()
    # time.sleep(10)


    # driver.get("https://m.sogou.com/web/searchList.jsp?htprequery=感冒怎么办&keyword=艾滋病初期症状")
    # search_html = driver.execute_script("return document.documentElement.outerHTML")
    # print(search_html)
    # elem = driver.find_element_by_id("keyword")
    # elem.send_keys(u"感冒怎么办")
    # elem.send_keys(Keys.ENTER)

    # fpw.write("{0}".format(driver.page_source))
    driver.quit()
    display.stop()
