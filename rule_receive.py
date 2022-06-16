import re
import pandas as pd
import numpy as np
from lxml import etree
from datetime import datetime
from dateutil.parser import parse
import os
import shutil
import random
import time
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.service import Service
from selenium.webdriver.common.keys import Keys
from similar_samples import *


class Receive:
    def __init__(
            self,
            driver: webdriver.Chrome,
            # df_stock: pd.DataFrame,
            # df_offline: pd.DataFrame,
            # df_normal: pd.DataFrame
    ):
        super().__init__()
        # self.df_stock = df_stock
        # self.df_offline = df_offline
        # self.df_normal = df_normal
        self.driver = driver
        self.df_log = pd.DataFrame()
        self.count_num = 1

        # 点击进入标准价列表
        self.driver.find_element(
            by='xpath',
            value='//*[@id="app"]/div/section/aside/div/ul/span[3]/li/ul/span[2]/li/ul/span[1]/a/li').click()
        time.sleep(0.2)
        self.out_wait()

        # 设置顺序及其变化后的位置
        self.order = 1

        # 审批总数
        self.total_amount = int(
            self.driver.find_element(
                by='xpath',
                value='//*[@id="must_do_not_change_this_id"]/div[2]/div/div[2]/div[1]/div[2]/span/span').text)

    def initial(self):
        self.building_benchmark = None
        self.benchmark_coefficient = None
        self.building_name = None
        # 随时打断当前审批
        self.is_break = 0
        self.break_reason = None
        self.is_arith_big = 0
        # 确定最终价格列表
        self.price_final_list = []
        self.diff_con_final = []
        self.evaluate_room_num = 0
        self.price_source = None
        self.source_edition = None
        self.adjust_rate_mean = None
        self.shutdown = None
        self.confidence = None
        self.price_evaluate_model = None

    def start(self):
        # 初始化时间,并开始循环
        now_time = datetime.now().strftime('%Y-%m-%d')
        now_time_format = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

        # 当前为0条时直接结束
        if self.total_amount == 0:
            return None

        while True:
            self.out_wait()
            self.initial()
            print(f'当前页面order,{self.order}')
            self.get_ready()
            self.check_in()
            self.count_num += 1
            # 遇到三居心舍先返回,不处理

            if self.is_break == 1:
                self.get_exit()
                if self.shutdown == 1:
                    break
                continue

            if self.survey_type in ['-', '--']:
                # '暂时跳过'
                # self.get_break()
                # continue
                self.survey_type_adjust()
                this_log_dict = {
                    '申请单号': [self.apply_number],
                    '业务类型': [self.business_type],
                    '实勘类型': [self.survey_type],
                    '友家/整租': [self.way],
                    '所属大区': [self.district],
                    '楼盘名称': [self.building_name],
                    '调价幅度': [self.price_change_list],
                    '平均调价幅度': [self.adjust_rate_mean],
                    '审批结果': [self.judge_result],
                    '是否流转分析师': [self.is_break],
                    '流转原因': [self.break_reason],
                }

            else:
                if self.business_type == '新签':
                    self.new_sign()

                elif self.business_type == '续约':
                    self.extension()

                this_log_dict = {
                    '申请单号': [self.apply_number],
                    '业务类型': [self.business_type],
                    '实勘类型': [self.survey_type],
                    '友家/整租': [self.way],
                    '所属大区': [self.district],
                    '楼盘名称': [self.building_name],
                    # '对标盘名称': [self.building_benchmark],
                    # '对标盘系数': [self.benchmark_coefficient],
                    '面积': [self.area_list],
                    '户型': [self.room_type],
                    '阳台': [self.balcony_list],
                    '独卫': [self.toilet_list],
                    '一顶层': [self.is_one_top],
                    '通过价格': [self.price_final_list],
                    '可定价房间数': [self.evaluate_room_num],
                    '价格来源': [self.price_source],
                    '来源版本': [self.source_edition],
                    '是否流转分析师': [self.is_break],
                    '流转原因': [self.break_reason],
                    '算法价': [self.price_arithmetic_list],
                    '置信度': [self.confidence],
                    '算法&程序价差异': [self.diff_con_final],
                    '是否算法差异大': [self.is_arith_big],
                    '新模型价格':[self.price_evaluate_model]

                }

            # 记录审批历史
            df_this_log = pd.DataFrame(this_log_dict)
            self.df_log = self.df_log.append(df_this_log)

            # 将收房审批按每日汇总
            try:
                # print('正在创建记录文件夹')
                os.mkdir(f'./receive_record/收房审批文件夹{now_time}')
            except BaseException:
                # print('无需创建')
                pass
            self.df_log.to_csv(
                f'./receive_record/收房审批文件夹{now_time}/收房审批记录 {now_time_format}.csv',
                encoding='gbk',
                index=False)
            shutil.copy(
                './receive_record/合并csv.py',
                f'./receive_record/收房审批文件夹{now_time}')
            shutil.copy(
                './receive_record/每日收房汇总 - 自动图片.py',
                f'./receive_record/收房审批文件夹{now_time}')
            # 将收房审批按每月汇总
            try:
                os.mkdir(f'./receive_record/{datetime.now().month}月收房汇总')
            except BaseException:
                pass
            self.df_log.to_csv(
                f'./receive_record/{datetime.now().month}月收房汇总/收房审批记录 {now_time_format}.csv',
                encoding='gbk',
                index=False)
            shutil.copy('./receive_record/合并csv.py',
                        f'./receive_record/{datetime.now().month}月收房汇总')
            shutil.copy('./receive_record/每日收房汇总 - 自动图片.py',
                        f'./receive_record/{datetime.now().month}月收房汇总')

            # 展示页面用于分隔每个审批
            print(
                '可定价:',
                self.price_final_list,
                self.order,
                '  可审批' if self.is_break == 0 else '  已流转',
                '*' * 50)

            self.out_wait()
            self.get_exit()
            if self.shutdown == 1:
                break

        print('收房审批, End ')

    def get_ready(self):
        """获取单号,业务类型,实勘类型"""

        # 获取当前调价单号
        self.apply_number = '"' + self.driver.find_element(
            by='xpath',
            value=f'//*[@id="must_do_not_change_this_id"]/div[2]/div/div[2]/div[2]/div[1]/div[3]/table/tbody/tr[{self.order}]/td[1]/div').text
        print('-' * 50, f'第{self.count_num}个申请单号,{self.apply_number},')

        # 获取当前业务类型
        self.business_type = self.driver.find_element(
            by='xpath',
            value=f'//*[@id="must_do_not_change_this_id"]/div[2]/div/div[2]/div[2]/div[1]/div[3]/table/tbody/tr[{self.order}]/td[3]/div').text

        # 获取当前实勘类型
        self.survey_type = self.driver.find_element(
            by='xpath',
            value=f'//*[@id="must_do_not_change_this_id"]/div[2]/div/div[2]/div[2]/div[1]/div[3]/table/tbody/tr[{self.order}]/td[4]/div').text

        # 产品线
        self.way = self.driver.find_element(
            by='xpath',
            value=f'//*[@id="must_do_not_change_this_id"]/div[2]/div/div[2]/div[2]/div[1]/div[3]/table/tbody/tr[{self.order}]/td[5]/div').text
        print('产品线:', self.way)

    def check_in(self):
        """进入审批详情阶段"""

        # 点击浏览进入详情页
        self.query_button = self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/div/form/div[1]/div[12]/div/div/button[1]/span')
        self.check_button = self.driver.find_element(
            by='xpath',
            value=f'//*[@id="must_do_not_change_this_id"]/div[2]/div/div[2]/div[2]/div[1]/div[4]/div[2]/table/tbody/tr[{self.order}]/td[17]/div/a')
        self.check_button.click()
        # 如遇意外, 大概是价格超过算法价范围
        # try:
        #     self.check_button.click()
        # except:
        #     self.get_break()
        #     ActionChains(
        #         self.driver).move_to_element_with_offset(
        #         self.query_button, 0, 200).click().perform()
        #     time.sleep(0.5)
        #     self.check_button.click()

        # 等待一切加载完成
        self.in_wait()

        # 获取审批状态
        audit_status = self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[1]/div/section/div[3]/div[1]/span[2]/span').text
        print(audit_status)
        if audit_status != '等待审批':
            self.is_break = 1
            self.get_break()
            # 已被审批则返回并刷新,然后重跑
            self.driver.refresh()
            self.order = 1
            return None

    def new_sign(self):
        """新签分支"""
        if self.way == '自如友家':
            self.new_friend_home()
        if self.way == '自如整租':
            self.new_whole_rent()

    def extension(self):
        """续约分支"""
        if self.way == '自如友家':
            self.extension_friend_home()
        if self.way == '自如整租':
            self.extension_whole_rent()

    def survey_type_adjust(self):
        """调整类型处理办法"""
        print('正在进行调整类处理')
        # self.in_wait()
        self.spider_attribute_new()

        # 获取调整后价格
        self.price_adjust_list = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[3]/table/tbody/tr/td[8]/div')

        if self.way == '自如整租':
            self.price_adjust_list = [int(self.price_adjust_list[0].text)]
        else:
            self.price_adjust_list = [int(i.text)
                                      for i in self.price_adjust_list[1:]]
        print('调整后价格:', self.price_adjust_list)

        # 获取首次价格
        self.price_first_word = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[3]/div/div/section/div[1]/div[1]/div[3]/table/tbody/tr/td[7]/div/span')[-1].text.replace(' ', '')
        print(self.price_first_word)

        if self.way == '自如整租':
            self.price_first_list = re.findall(
                '整租：(.*?)元', self.price_first_word, re.I)[0].strip()
            self.price_first_list = [int(float(self.price_first_list))]
        else:
            # 友家的考虑到房间顺序会乱的问题, 根据房间编号找
            self.room_num_list = self.driver.find_elements(
                by='xpath',
                value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[4]/div[2]/table/tbody/tr/td[1]/div/span')[1:]
            self.room_num_list = [i.text for i in self.room_num_list]
            print(self.room_num_list)

            self.price_first_list = []
            for room_num in self.room_num_list:
                room_price = re.findall(
                    f'{room_num}卧(.*?)元',
                    self.price_first_word,
                    re.I)[0].strip()
                self.price_first_list.append(int(float(room_price)))
        print('首次价格:', self.price_first_list)

        # 确定对比初次定价涨幅
        self.price_change_list = [
            (adjust - first) / first for adjust,
            first in zip(
                self.price_adjust_list,
                self.price_first_list)]
        self.price_change_list = [round(i * 100, 1)
                                  for i in self.price_change_list]

        print('调价幅度列表:', self.price_change_list)

        # 平均调价幅度
        self.adjust_rate_mean = round(
            sum(self.price_change_list) / len(self.price_change_list), 1)

        if all([change <= 3 for change in self.price_change_list]):
            self.judge_result = '通过'
            # 通过按钮
            self.driver.find_element(
                by='xpath',
                value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[4]/button[1]').click()
            # 备注栏
            self.driver.find_element(
                by='xpath',
                value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[5]/div/div[2]/div[2]/div/textarea').send_keys('程序自动审批11111')
            time.sleep(0.5)
            # 提交按钮
            submit_button = self.driver.find_element(
                by='xpath',
                value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[5]/div/div[3]/div/button[2]')
            submit_button.click()
            time.sleep(0.5)

            # 测试阶段,点击空白跳过,并返回
            # ActionChains(
            #     self.driver).move_to_element_with_offset(
            #     submit_button, 0, 200).click().perform()
            # time.sleep(0.5)

        else:
            self.judge_result = '驳回'
            # 驳回按钮
            self.driver.find_element(
                by='xpath',
                value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[4]/button[2]').click()
            self.driver.find_element(
                by='xpath',
                value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[5]/div/div[2]/div[2]/div/textarea').send_keys('调价幅度大, 程序自动驳回, 有疑问请联系大区分析师')
            time.sleep(0.5)
            # 提交按钮
            submit_button = self.driver.find_element(
                by='xpath',
                value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[5]/div/div[3]/div/button[2]')
            submit_button.click()
            time.sleep(0.5)

            # 测试阶段,点击空白跳过,并返回
            # ActionChains(
            #     self.driver).move_to_element_with_offset(
            #     submit_button, 0, 200).click().perform()
            # time.sleep(0.5)

        # 调试阶段, 使用返回
        # self.order += 1
        # self.driver.back()
        # return None

    def new_friend_home(self):
        """新签友家,规则判断"""
        print('新签友家规则')
        self.spider_attribute_new()

        # 对每个房间进行判断
        for i, (area, balcony, toilet, price_apply) in enumerate(zip(
                self.area_list, self.balcony_list, self.toilet_list, self.price_arithmetic_list)):
            a = Samples(
                self.driver,
                self.order,
                self.business_type,
                self.way,
                self.building_name,
                self.room_type,
                area,
                balcony,
                toilet,
                self.is_one_top,
                price_apply,
                # self.df_stock,
                # self.df_offline,
                # self.df_normal
            )
            price_evaluate = a.start()

            price_arith_this = self.price_arithmetic_list[i]

            if price_evaluate:
                self.price_final_list.append(price_evaluate)
                self.evaluate_room_num += 1
            elif self.confidence >= 0.95:
                self.price_final_list.append(price_arith_this)
                self.evaluate_room_num += 1
                print('使用算法价,',price_arith_this)

            else:
                self.is_break = 1
                self.break_reason = "无法估价(新签友家)"
                self.get_break()
                break
        print(
            '俩价格列表长度', len(
                self.price_final_list), len(
                self.price_arithmetic_list))

        if len(self.price_final_list) == len(self.price_arithmetic_list):
            self.price_source = a.price_source
            self.source_edition = a.source_edition
            # 定价和算法价差异, 差异过大则不批
            print(self.price_final_list)
            if self.judge_arithmetic():
                self.friend_audit()
            else:
                self.is_break = 1
                self.break_reason = '和算法差异大'
                self.is_arith_big = 1
                self.get_break()
        else:
            print('无法决定所有房间价格')

    def friend_audit(self):
        """友家,执行审批阶段"""
        print('友家审批')
        # 点击通过按钮
        self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[4]/button').click()
        time.sleep(0.3)
        # 修正价格列表
        adjust_price_list = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[5]/div/div[2]/div[1]/div/div/div[5]/div[2]/table/tbody/tr/td[8]/div/div/div/div/input')

        # 在修正价格框中输入价格, 用索引的原因是方便输入值
        if self.room_type == '3室':
            for i in range(len(adjust_price_list))[1:]:
                time.sleep(0.5)
                adjust_price_list[i].clear()
                adjust_price_list[i].send_keys(self.price_final_list[i - 1])
        else:
            for i in range(len(adjust_price_list)):
                time.sleep(0.5)
                adjust_price_list[i].clear()
                adjust_price_list[i].send_keys(self.price_final_list[i])

        # 在备注框中输入文字
        self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[5]/div/div[2]/div[2]/div/textarea').send_keys('程序自动审批111111111')
        # 提交按钮
        submit_button = self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[5]/div/div[3]/div/button[2]')
        time.sleep(0.5)
        submit_button.click()
        time.sleep(0.5)

        # 测试阶段,点击空白跳过,并返回
        # ActionChains(self.driver).move_to_element_with_offset(submit_button, 0, 200).click().perform()
        # time.sleep(0.5)
        # # 并返回
        # self.driver.back()
        # self.order = self.order + 1

    def new_whole_rent(self):
        """新签整租规则"""
        print('新签整租规则阶段')
        self.spider_attribute_new()
        a = Samples(
            self.driver,
            self.order,
            self.business_type,
            self.way,
            self.building_name,
            self.room_type,
            self.area_list[0],
            self.balcony_list[0],
            self.toilet_list[0],
            self.is_one_top,
            self.price_arithmetic_list[0],
            # self.df_stock,
            # self.df_offline,
            # self.df_normal
        )

        price_evaluate = a.start()
        # 获取对标盘名称和系数
        self.building_benchmark = a.building_benchmark
        self.benchmark_coefficient = a.benchmark_coefficient

        self.price_evaluate_model = a.price_evaluate_model

        if price_evaluate == 0:
            self.is_break = 1
            self.break_reason = '无法估价(新签整租)'
            self.get_break()
        else:
            # if price_evaluate > 10000:
            #     pass
            # 0426加入供需系数0.9,0506取消
            # price_evaluate = price_evaluate * 0.9
            # price_evaluate = self.suit(price_evaluate)
            self.evaluate_room_num += 1
            self.price_source = a.price_source
            self.source_edition = a.source_edition
            self.price_final_list.append(price_evaluate)
            print(self.price_final_list)
            if self.judge_arithmetic():
                self.whole_audit()
            else:
                self.is_break = 1
                self.break_reason = '和算法差异大'
                self.is_arith_big = 1
                self.get_break()

    def whole_audit(self):
        """整租审批阶段"""
        print('整租审批阶段')
        self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[4]/button').click()
        # 修正价格列表
        adjust_price_list = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[5]/div/div[2]/div[1]/div/div/div[5]/div[2]/table/tbody/tr/td[8]/div/div/div/div/input')

        # 在修正价格框中输入价格
        for i in range(len(adjust_price_list))[:1]:
            time.sleep(0.5)
            adjust_price_list[i].clear()
            adjust_price_list[i].send_keys(self.price_final_list[i])

        # 在备注框中输入文字
        self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[5]/div/div[2]/div[2]/div/textarea').send_keys(
            '程序自动审批111111111')
        # 提交按钮
        submit_button = self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[5]/div/div[3]/div/button[2]')
        time.sleep(0.5)
        # submit_button.click()
        # time.sleep(0.5)

        # 测试阶段,点击空白跳过,并返回
        ActionChains(self.driver).move_to_element_with_offset(submit_button, 0, 200).click().perform()
        time.sleep(0.5)
        # 并返回
        self.driver.back()
        self.order = self.order + 1

    def extension_friend_home(self):
        """续约友家规则, 与新签不同处在于有户型变更"""
        print('续约友家规则阶段')
        self.spider_attribute_extension()
        if self.is_break:
            self.break_reason = '户型变更(续约友家)'
            self.get_break()
            return None

        for i,(area, balcony, toilet, price_apply) in enumerate(zip(
                self.area_list, self.balcony_list, self.toilet_list, self.price_list_promotion)):
            a = Samples(
                self.driver,
                self.order,
                self.business_type,
                self.way,
                self.building_name,
                self.room_type,
                area,
                balcony,
                toilet,
                self.is_one_top,
                price_apply,
                # self.df_stock,
                # self.df_offline,
                # self.df_normal
            )
            price_evaluate = a.start()

            price_arith_this = self.price_arithmetic_list[i]

            if price_evaluate:
                self.price_final_list.append(price_evaluate)
                self.evaluate_room_num += 1
            elif self.confidence >= 0.95:
                self.price_final_list.append(price_arith_this)
                self.evaluate_room_num += 1
                print('使用算法价,', price_arith_this)

            else:
                self.is_break = 1
                self.break_reason = "无法估价(续约友家)"
                self.get_break()
                break


        print(
            '俩价格列表长度', len(
                self.price_final_list), len(
                self.price_arithmetic_list))

        if len(self.price_final_list) == len(self.price_arithmetic_list):
            self.price_source = a.price_source
            self.source_edition = a.source_edition
            print(self.price_final_list)

            if self.judge_arithmetic():
                self.friend_audit()
            else:
                self.is_break = 1
                self.break_reason = '和算法差异大'
                self.is_arith_big = 1
                self.get_break()
        else:
            print('无法决定所有房间价格')

    def extension_whole_rent(self):
        """续约整租规则"""
        print('续约整租规则阶段')
        self.spider_attribute_extension()
        if self.is_break:
            self.break_reason = '户型变更(续约整租)'
            self.get_break()
            return None

        a = Samples(
            self.driver,
            self.order,
            self.business_type,
            self.way,
            self.building_name,
            self.room_type,
            self.area_list[0],
            self.balcony_list[0],
            self.toilet_list[0],
            self.is_one_top,
            self.price_list_promotion[0],
            # self.df_stock,
            # self.df_offline,
            # self.df_normal
        )

        price_evaluate = a.start()

        self.price_evaluate_model = a.price_evaluate_model

        if price_evaluate == 0 or abs(
                self.price_arithmetic_list[0] - price_evaluate) / self.price_arithmetic_list[0] > 0.2:
            self.is_break = 1
            print('无相似估计价格')
            self.break_reason = '无法估价(续约整租)'
            self.get_break()
        else:
            if price_evaluate > 10000:
                pass
                # 0426加入供需系数0.9,0506取消
                # price_evaluate = price_evaluate * 0.9
                # price_evaluate = self.suit(price_evaluate)
            self.evaluate_room_num += 1
            self.price_final_list.append(price_evaluate)
            self.price_source = a.price_source
            self.source_edition = a.source_edition
            print(self.price_final_list)

            if self.judge_arithmetic():
                self.whole_audit()
            else:
                self.is_break = 1
                self.break_reason = '和算法差异大'
                self.is_arith_big = 1
                self.get_break()

    def spider_attribute_new(self):
        """获取新签房间属性: 楼盘名称, 楼层, 面积, 卫, 阳, 调后价"""
        print('新签抓取环节')
        # 获取当前大区
        self.district = self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[1]/div/section/div[2]/div[2]/span[2]').text
        self.district = re.findall('深圳(.*?区).*?', self.district, re.S)[0]

        self.building_name = self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[1]/div/section/div[1]/div[3]/span[2]').text
        print(self.building_name)
        self.room_floor = self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[1]/div/section/div[2]/div[3]/span[2]/span').text
        self.is_one_top = self.judge_one_top(self.room_floor)
        self.room_type = self.driver.find_element(
            by='xpath', value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[3]/table/tbody/tr[1]/td[4]/div/span').text[19:21]
        print('居室类型:', self.room_type)
        self.area_list_0 = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[3]/table/tbody/tr/td[2]/div/span')

        self.toilet_list_0 = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[3]/table/tbody/tr/td[4]/div/div/span[1]')
        self.balcony_list_0 = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[3]/table/tbody/tr/td[4]/div/div/span[2]')
        self.price_arithmetic_list_0 = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[3]/table/tbody/tr/td[8]/div')
        self.confidence_0 = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[3]/table/tbody/tr/td[6]/div/span')
        # 遇到调整类型不再继续分析
        if self.survey_type in ['-', '--']:
            return None

        # 0510改版
        if self.way == '自如友家':
            self.area_list = [float(i.text) for i in self.area_list_0[1:]]
            # 方便记录
            self.balcony_list = [i.text for i in self.balcony_list_0]
            self.balcony_list = list(
                map((lambda x: '有阳台' if x != '无阳台' else x), self.balcony_list))
            self.toilet_list = [i.text for i in self.toilet_list_0]
            self.price_arithmetic_list = [
                int(i.text) for i in self.price_arithmetic_list_0[1:]]
            self.confidence = int(self.confidence_0[1].text[-4:-1].replace('/',''))

        elif self.way == '自如整租':
            self.area_list = [float(self.area_list_0[0].text)]
            # 方便记录
            self.balcony_list = [i.text for i in self.balcony_list_0]
            self.toilet_list = [i.text for i in self.toilet_list_0]
            self.price_arithmetic_list = [
                int(self.price_arithmetic_list_0[0].text)]
            self.confidence = int(self.confidence_0[0].text[-4:-1].replace('/',''))

        print(f'算法置信度: {self.confidence}')

    def spider_attribute_extension(self):
        """获取续约房间属性: 楼盘名称, 楼层, 面积, 卫, 阳, 调后价"""
        print('续约抓取环节')
        # 获取当前大区
        self.district = self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[1]/div/section/div[2]/div[2]/span[2]').text
        self.district = re.findall('深圳(.*?区).*?', self.district, re.S)[0]

        self.building_name = self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[1]/div/section/div[1]/div[3]/span[2]').text
        print(self.building_name)
        self.room_floor = self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[1]/div/section/div[2]/div[3]/span[2]/span').text
        self.is_one_top = self.judge_one_top(self.room_floor)
        self.room_type = self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[3]/table/tbody/tr[1]/td[4]/div/span').text[
            19:21]
        print('居室类型:', self.room_type)
        self.area_list_0 = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[3]/table/tbody/tr/td[2]/div/span')

        self.toilet_list_0 = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[3]/table/tbody/tr/td[4]/div/div/span[1]')
        self.balcony_list_0 = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[3]/table/tbody/tr/td[4]/div/div/span[2]')
        self.price_arithmetic_list_0 = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[3]/table/tbody/tr/td[8]/div')
        self.confidence_0 = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[3]/table/tbody/tr/td[6]/div/span')
        # 用于判断是否产品线变更, 抓不到则是空了一段时间后续约
        try:
            self.extension_information = self.driver.find_element(
                by='xpath',
                value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[5]/div/div/div').text.strip()
            self.extension_information = self.extension_information.split(' ')
        except BaseException:
            self.is_break = 1
            return None
        print('之前产品线:', self.extension_information)

        # 0510改版
        if self.way == '自如友家':
            self.area_list = [float(i.text) for i in self.area_list_0[1:]]
            # 方便记录
            self.balcony_list = [i.text for i in self.balcony_list_0]
            self.balcony_list = list(
                map((lambda x: '有阳台' if x != '无阳台' else x), self.balcony_list))
            self.toilet_list = [i.text for i in self.toilet_list_0]
            self.price_arithmetic_list = [
                int(i.text) for i in self.price_arithmetic_list_0[1:]]
            self.confidence = int(self.confidence_0[1].text[-4:-1].replace('/',''))

            product_change_judge = [('友家' in i)
                                    for i in self.extension_information]
            print(any(product_change_judge))
            if not any(product_change_judge):
                self.is_break = 1
                return None

            # 出房价格信息,同一框中第一条和后续几条的抓取逻辑并不相同
            self.price_list_promotion = []
            try:
                price_num_1 = self.driver.find_element(
                    by='xpath',
                    value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[5]/div/div/div/div[3]/table/tbody/tr[1]/td[9]/div').text
                price_num_rest = self.driver.find_elements(
                    by='xpath',
                    value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[5]/div/div/div/div[3]/table/tbody/tr/td[5]/div')[1:]
            except BaseException:
                self.is_break = 1
                # 抓不到意味着从整租续约成了友家
                return None

            price_num_rest = [i.text for i in price_num_rest]
            print(price_num_1, price_num_rest)
            self.price_list_promotion.append(price_num_1)
            self.price_list_promotion.extend(price_num_rest)
            self.price_list_promotion = [
                int(i) for i in self.price_list_promotion]
            # 检查是否有户型的变更
            # print('是否变更俩列表长度',len(self.price_list_apply),len(self.price_list))
            if len(
                    self.price_arithmetic_list) != len(
                    self.price_list_promotion):
                print('***户型变更***')
                # 意味着友家居室数量变动
                self.is_break = 1

        elif self.way == '自如整租':
            self.area_list = [float(self.area_list_0[0].text)]
            # 方便记录
            self.balcony_list = [i.text for i in self.balcony_list_0]
            self.toilet_list = [i.text for i in self.toilet_list_0]
            self.price_arithmetic_list = [
                int(self.price_arithmetic_list_0[0].text)]
            self.confidence = int(self.confidence_0[0].text[-4:-1].replace('/',''))

            product_change_judge = [('友家' not in i)
                                    for i in self.extension_information]
            print(any(product_change_judge))
            if not any(product_change_judge):
                self.is_break = 1
                return None

            try:
                # 出房价格信息
                self.price_list_promotion = self.driver.find_elements(
                    by='xpath',
                    value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[5]/div/div/div/div/div[3]/table/tbody/tr/td[7]/div/span')
                self.price_list_promotion = [
                    int(self.price_list_promotion[0].text)]
            except BaseException:
                self.price_list_promotion = []

            # 检查是否有户型的变更
            if len(self.price_list_promotion) != 1:
                print('***户型变更***')
                # 意味着从友家续约成了整租
                self.is_break = 1

        print(f'算法置信度: {self.confidence}')

    def check_out(self):
        """结束该审批阶段"""
        self.out_wait()
        time.sleep(1)

    def out_wait(self):
        """列表页等待一切加载完毕"""
        time.sleep(0.5)
        check_list_this_page = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/div/div[2]/div[2]/div[1]/div[3]/table/tbody/tr/td[1]/div')

    def in_wait(self):
        """详情页等待一切加载完毕"""
        total_area = self.driver.find_element(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/section/div[1]/div[2]/div/div/div/div[3]/table/tbody/tr[1]/td[2]/div').text
        time.sleep(0.2)

    def adjust_rate_clean(self, adjust_range_list: list):
        """调整类型, 调价幅度列表清洗"""
        list_int = []
        for i in adjust_range_list:
            try:
                list_int.append(float(i[:-1]))
            except BaseException:
                pass
        return list_int

    def judge_one_top(self, room_floor: str):
        """判断是否一顶层"""
        this_floor = int(room_floor[:2])
        try:
            total_floor = int(room_floor[-2:])
        except BaseException:
            return 0
        if this_floor == 1:
            return 1
        elif total_floor <= 8 and this_floor >= 6:
            return 1
        else:
            return 0

    def turn_page(self):
        # 流转分析师满10则翻页
        if self.order > 10:
            try:
                self.driver.find_element(
                    by='xpath',
                    value='//*[@id="must_do_not_change_this_id"]/div[2]/div/div[2]/div[2]/div[2]/div/button[2]').click()
                time.sleep(0.5)
                self.order = 1
            except BaseException:
                # 无法翻页则完成
                self.shutdown = 1

    def get_exit(self):
        # 当前顺序大于列表长度则退出

        try:
            turn_button = self.driver.find_element(
                by='xpath',
                value='//*[@id="must_do_not_change_this_id"]/div[2]/div/div[2]/div[2]/div[2]/div/button[2]')
        except BaseException:
            self.get_break()
            time.sleep(0.5)
            ActionChains(
                self.driver).move_to_element_with_offset(
                self.query_button, 0, 200).click().perform()
            time.sleep(0.5)
            return None

        check_list_this_page = self.driver.find_elements(
            by='xpath',
            value='//*[@id="must_do_not_change_this_id"]/div[2]/div/div[2]/div[2]/div[1]/div[3]/table/tbody/tr/td[1]/div')

        # 刚好剩下10个时,退出, 否则翻页
        if self.order == 11:
            if turn_button.is_enabled():
                turn_button.click()
                self.order = 1
                return None
            else:
                self.shutdown = 1
                return None

        # 剩下不满10个
        if self.order > len(check_list_this_page):
            self.shutdown = 1
            return None

    def get_break(self):
        # 用于随时打断当前审批, 进入下一条
        self.order += 1
        self.driver.back()
        time.sleep(0.5)

    def suit(self, num):
        """自适应价格"""
        hundred = (num // 100.001) * 100
        ten = num - hundred
        if ten <= 10:
            ten = -10
            hundred = (num // 100.001) * 100
        elif ten <= 50:
            ten = 30
        elif ten <= 70:
            ten = 60
        else:
            ten = 90

        return int(hundred + ten)

    def judge_arithmetic(self):
        """判断和算法价的差异"""
        for price_i, price_a in zip(
                self.price_final_list, self.price_arithmetic_list):
            diff = round((abs(price_i - price_a) / price_a) * 100, 2)
            self.diff_con_final.append(diff)
        print('置信度:', self.confidence, '算法价:', self.price_arithmetic_list)
        print('定价和算法差异:', self.diff_con_final)
        if self.confidence >= 90:
            if any([i >= 20 for i in self.diff_con_final]):
                print('差异过大, 不处理')
                return 0
        if self.confidence >= 1:
            if any([i >= 30 for i in self.diff_con_final]):
                print('差异过大, 不处理')
                return 0
        return 1
