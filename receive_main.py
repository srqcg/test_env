import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.service import Service
from selenium.webdriver.common.keys import Keys
from lxml import etree
from tenacity import retry, wait_fixed, stop_after_attempt
import time
import datetime
import concurrent.futures
from selenium.webdriver.common.action_chains import ActionChains
from rule_receive import *


# 登录收益管理系统
def login_profit(driver: webdriver.Chrome):
    url='http://tech.sso.ziroom.com/login?ReturnURL=http://banana.ziroom.com&_lt=vOulsWMDhgrdcwjPkJY9300Mn6379y5J0jMGXVy4HKxiwpddmVU4eImPA6dSjeO--HcYxVxt0s8RXwYKluuA1vMWtJU_61mx72LAx_8JTmhw0_FUV0XKCsSIf2ihP94o6Kf7LdCI0r5zEuANfmSOoHB41UhX4X6E2gWb3N26l-Seqtz3PkSScBUflaQkImlZ5rBKbBu26rE2EMBCPqii4OZm0mzCQ2-T9QkHrMl-HYr1b3jZJG5lNmeGH9cyPvRz5EnfiUQaR2GzQbYXNJiBCNJVRNfi5DcB32PNyKFpFzxoD1q8pXAAWP-OnsmWsXIiILoTiKA0ENup7a14RfxMCzpNzHTXEqmCPRhCuFfEMONoskn_xfngBbb7lZ-EgMirpW7vFl9G2Q_0_4U1dlJP6nklGI5bzQU9Vf6F'
    driver.get(url)
    driver.find_element(by='id', value='userName').send_keys('wucg')
    driver.find_element(by='id', value='password').send_keys('Syy.0807')
    verify_block = driver.find_element(
        by='xpath', value='//div[@class="verify-move-block"]')
    action = ActionChains(driver)
    action.click_and_hold(verify_block)
    action.move_by_offset(300, 0)
    action.release()
    action.perform()
    driver.find_element(by='id', value='submitBtn').click()


# 完全展开调价管理模块
def price_adjustment(driver: webdriver.Chrome):
    # 调价管理
    driver.find_element(
        by='xpath',
        value='//*[@id="app"]/div/section/aside/div/ul/span[3]/li/div').click()
    time.sleep(0.2)
    # 调价申请
    driver.find_element(
        by='xpath',
        value='//*[@id="app"]/div/section/aside/div/ul/span[3]/li/ul/span[1]/li/div/span').click()
    time.sleep(0.2)
    # 出房价调价
    driver.find_element(
        by='xpath',
        value='//*[@id="app"]/div/section/aside/div/ul/span[3]/li/ul/span[1]/li/ul/span[2]/li/div/span').click()
    time.sleep(0.2)
    # 价格审批
    driver.find_element(
        by='xpath',
        value='//*[@id="app"]/div/section/aside/div/ul/span[3]/li/ul/span[2]/li/div/span').click()
    time.sleep(0.2)


# 完全展开风控处理模块
def risk_management(driver):
    driver.find_element(
        by='xpath',
        value='//*[@id="app"]/div/section/aside/div/ul/span[4]/li/div/span').click()


def main_process():
    chrome = r'D:\S-important\chromedriver.exe'
    option = webdriver.ChromeOptions()
    option.add_experimental_option('excludeSwitches', ['enable-logging'])
    option.add_argument("""--no-sandbox""")
    option.add_experimental_option("detach", True)
    # option.add_argument("""--disable-gpu""")
    driver = webdriver.Chrome(executable_path=chrome, options=option)
    driver.maximize_window()
    driver.implicitly_wait(20)

    # 初始化库存数据
    # df_stock = pd.DataFrame()
    # df_offline_benchmark = pd.DataFrame()
    # df_normal = pd.DataFrame()

    # 获取库存数据
    # for file in os.listdir('./当前库存表'):
    #     if file.startswith('自如库存') and file.endswith('csv'):
    #         try:
    #             # 获取自如库存
    #             df_stock = pd.read_csv(f'./当前库存表/{file}')
    #         except BaseException:
    #             df_stock = pd.read_csv(f'./当前库存表/{file}', encoding='gbk')
    #         df_stock.dropna(axis=1, how='all', inplace=True)
    #         df_stock.dropna(how='all', inplace=True)
    #     if file.startswith('对标') and file.endswith('csv'):
    #         try:
    #             # 获取对标盘
    #             df_offline_benchmark = pd.read_csv(f'./当前库存表/{file}')
    #         except BaseException:
    #             df_offline_benchmark = pd.read_csv(
    #                 f'./当前库存表/{file}', encoding='gbk')
    #         df_offline_benchmark.dropna(axis=1, how='all', inplace=True)
    #         df_offline_benchmark.dropna(how='all', inplace=True)
    #     if file.startswith('普租整租') and file.endswith('csv'):
    #         try:
    #             # 获取普租整租
    #             df_normal = pd.read_csv(f'./当前库存表/{file}')
    #         except BaseException:
    #             df_normal = pd.read_csv(f'./当前库存表/{file}', encoding='gbk')
    #         df_normal.dropna(axis=1, how='all', inplace=True)
    #         df_normal.dropna(how='all', inplace=True)

    login_profit(driver)
    price_adjustment(driver)
    a = Receive(driver,
                # df_stock, df_offline_benchmark, df_normal
                )
    a.start()
    driver.quit()



# @retry(wait=wait_fixed(600),stop=stop_after_attempt(10))
def main():
    print('now reboot!')
    os.system('taskkill -f -t -im chrome.exe')
    main_process()
    while True:
        now = datetime.now().time()
        M = datetime.now().time().minute
        S = datetime.now().time().second
        h = datetime.now().time().hour
        if h <= 6:
            print('too early', '收房审批待机运行中, 切勿关闭', datetime.now().time())
            time.sleep(1)
            continue

        if M in (20,50):
            os.system('taskkill -f -t -im chrome.exe')
            main_process()
        else:
            print('收房审批待机运行中, 切勿关闭',now)
            time.sleep(1)

if __name__ == '__main__':
    main()
