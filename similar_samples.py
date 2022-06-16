import pandas as pd
import numpy as np
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.service import Service
from selenium.webdriver.common.keys import Keys

df_stock = pd.DataFrame()
df_offline_benchmark = pd.DataFrame()
df_normal = pd.DataFrame()


for file in os.listdir('./当前库存表'):
    if file.startswith('自如库存') and file.endswith('csv'):
        try:
            # 获取自如库存
            df_stock = pd.read_csv(f'./当前库存表/{file}')
        except BaseException:
            df_stock = pd.read_csv(f'./当前库存表/{file}', encoding='gbk')
        df_stock.dropna(axis=1, how='all', inplace=True)
        df_stock.dropna(how='all', inplace=True)

    # if file.startswith('对标') and file.endswith('csv'):
    #     try:
    #         # 获取对标盘
    #         df_offline_benchmark = pd.read_csv(f'./当前库存表/{file}')
    #     except BaseException:
    #         df_offline_benchmark = pd.read_csv(
    #             f'./当前库存表/{file}', encoding='gbk')
    #     df_offline_benchmark.dropna(axis=1, how='all', inplace=True)
    #     df_offline_benchmark.dropna(how='all', inplace=True)

    if file.startswith('普租整租') and file.endswith('csv'):
        try:
            # 获取普租整租
            df_normal = pd.read_csv(f'./当前库存表/{file}')
        except BaseException:
            df_normal = pd.read_csv(f'./当前库存表/{file}', encoding='gbk')
        df_normal.dropna(axis=1, how='all', inplace=True)
        df_normal.dropna(how='all', inplace=True)

# 调整样本量需求
sample_num_request = 2

# 新签调整率
one_top_index = 0.95

editions = [
            (['精选业主直租',
            '业主直租2.0',
             '整租3.1',
              '整租3.2',
              '资管增益1号-整租3.2'],
             1,
             '整租3.X'),
            (['增益-速优家'],
            0.971,
            '速优家'),
            (['资管省心1号-心舍Plus版',
             '资管增益1号-心舍plus版'],
            0.893,
            '心舍1'),
            (['心舍2.0'],
             0.855,
             '心舍2.0')
            ]


class Samples:
    def __init__(
            self,
            driver: webdriver.Chrome,
            order: int,
            business_type,
            way: str,
            building: str,
            room_type,
            area: float,
            balcony: str,
            toilet: str,
            is_one_top,
            price_promotion: int):
        self.driver = driver
        self.order = order
        self.business_type = business_type
        self.way = way
        self.building = building
        self.room_type = room_type
        self.area = area
        self.balcony = balcony
        self.toilet = toilet
        self.is_one_top = is_one_top
        self.price_promotion = price_promotion
        self.df_stock = df_stock
        # self.df_benchmark = df_benchmark
        self.df_normal = df_normal
        self.edition = None
        self.source_edition = None
        self.condition_stock_status = '库存状态 != None'
        self.condition_building = f'楼盘名称 == "{self.building}"'
        self.condition_room_type = f'户型_a == "{self.room_type}"'
        self.condition_balcony = f'是否有阳台_a == "{self.balcony}"'
        self.condition_toilet = f'是否有独卫_a == "{self.toilet}"'
        self.benchmark_coefficient = None
        self.building_benchmark = None
        self.price_source = None
        self.price_evaluate_model = None

    def start(self):
        """开始"""
        if self.way == '自如友家':
            if self.area <= 10:
                area_top = self.area + 0.5
                area_bottom = self.area - 0.5
            else:
                area_top = self.area + 1
                area_bottom = self.area - 1

            price_evaluate = self.get_samples(area_top, area_bottom)

        else:
            if self.area <= 100:
                area_top = self.area + 5
                area_bottom = self.area - 5
            else:
                area_top = self.area + 10
                area_bottom = self.area - 10
            price_evaluate = self.get_samples(area_top, area_bottom)

        # 价格自适应369
        if price_evaluate != 0:
            price_evaluate = self.suit(price_evaluate)

        return price_evaluate

    def get_samples(self, area_top, area_bottom):
        """获取盘中相似户型价格"""
        self.condition_area_top = f'面积<={area_top}'
        self.condition_area_bottom = f'面积>={area_bottom}'

        # 新签续约分流
        if self.business_type == '新签':
            price_evaluate = self.determine_new_sign()
        else:
            price_evaluate = self.determine_extension()
        return price_evaluate

    def determine_new_sign(self):
        """确定新签价格"""
        # 友家
        if self.way == '自如友家':
            self.query_word()
            # 查询库存
            sample_num, price_mean_friend = self.get_query(self.df_stock, self.query_friend)
            if sample_num:
                price_evaluate = self.one_top_adjust(price_mean_friend, one_top_index)

                print('新签友家有库存样本', price_evaluate)
                self.price_source = '自如库存'

            # 0427不再查询对标盘
            else:
                price_evaluate = 0

            return price_evaluate

        # 整租
        if self.way == '自如整租':
            # 查询库存
            for edition in editions:
                self.edition = edition[0]
                self.product_index = edition[1]
                self.source_edition_stock = edition[2]
                self.query_word()

                sample_num_stock, price_mean_stock = self.get_query(self.df_stock, self.query_whole)
                if sample_num_stock:
                    break
                else:
                    print('此产品版本无样本')

            if sample_num_stock:

                price_mean_stock = price_mean_stock * self.product_index
                # 一顶层处理
                price_evaluate_stock = self.one_top_adjust(price_mean_stock, one_top_index)

                print(f'新签整租有库存样本{sample_num_stock}个', price_evaluate_stock)
            else:
                price_evaluate_stock = 0

            # 查询普租盘
            # else:
            print('尝试查询普租')
            self.edition = ['普租整租']
            self.source_edition_normal = '普租整租'
            self.query_word()

            sample_num_normal, price_mean_normal = self.get_query(self.df_normal, self.query_whole)


            if sample_num_normal:
                # 新模型
                wuye, year_index, part_index = self.query_wuye_year(price_mean_normal)
                print('物业费:', wuye, '年代系数', year_index, '价格段系数', part_index)
                # 先使用模型
                if all([wuye, year_index, part_index]):
                    self.price_evaluate_model = price_mean_normal * (1 + year_index + part_index) + wuye * self.area / 2
                    print('模型价格:', self.price_evaluate_model)
                    price_evaluate_normal = self.price_evaluate_model
                else:
                    # 再使用普租1.08,1.05
                    if self.room_type == '3居':
                        price_evaluate_normal = price_mean_normal * 1.05
                    else:
                        price_evaluate_normal = price_mean_normal * 1.08
                # 最后一顶层
                price_evaluate_normal = self.one_top_adjust(price_evaluate_normal,one_top_index)
                print(f'新签整租有普租样本{sample_num_normal}个', price_evaluate_normal)

            else:
                print('无普租样本')
                price_evaluate_normal = 0

            # 对库存和普租样本进行判断, 并确定样本来源和产品版本
            if not any([sample_num_stock, sample_num_normal]):
                price_evaluate = self.last_for_analyst()

            else:
                # 比较样本量
                price_evaluate = self.compare(
                    price_evaluate_stock,
                    price_evaluate_normal,
                    sample_num_stock,
                    sample_num_normal,
                    self.source_edition_stock,
                    self.source_edition_normal)

            return price_evaluate

    def determine_extension(self) ->int:
        """确定续约价格"""
        # 友家
        if self.way == '自如友家':
            self.query_word()

            # 查询库存
            sample_num, price_mean_friend = self.get_query(self.df_stock, self.query_friend)
            if sample_num:
                price_diff_rate = (price_mean_friend - self.price_promotion) / self.price_promotion
                print('续约友家有库存样本', price_mean_friend, '差异率', price_diff_rate)

                price_evaluate = self.extension_adjust(price_mean_friend,price_diff_rate)

                price_evaluate = self.one_top_adjust(price_evaluate, one_top_index)

                self.price_source = '自如库存'
            else:
                print(f'相似户型不满{sample_num_request}间')
                # 不满足条件, 交给分析师处理
                price_evaluate = self.last_for_analyst()

            return price_evaluate

        # 整租
        if self.way == '自如整租':
            # 查询库存
            for edition in editions:
                self.edition = edition[0]
                self.product_index = edition[1]
                self.source_edition_stock = edition[2]
                self.query_word()

                sample_num_stock, price_mean_stock = self.get_query(self.df_stock, self.query_whole)
                if sample_num_stock:
                    break
                else:
                    print('此版本无样本')

            if sample_num_stock:

                price_diff_rate = (price_mean_stock - self.price_promotion) / self.price_promotion
                # 产品版本影响
                price_mean_stock = price_mean_stock * self.product_index

                price_evaluate_stock = self.extension_adjust(price_mean_stock,price_diff_rate)

                price_evaluate_stock = self.one_top_adjust(price_evaluate_stock,one_top_index)
                print('续约整租有库存样本', price_evaluate_stock)
            else:
                price_evaluate_stock = 0

            # 查询普租盘
            # else:
            print('尝试查询普租')
            self.edition = ['普租整租']
            self.source_edition_normal = '普租整租'
            self.query_word()

            sample_num_normal, price_mean_normal = self.get_query(self.df_normal, self.query_whole)

            if sample_num_normal:
                wuye, year_index, part_index = self.query_wuye_year(price_mean_normal)
                if all([wuye, year_index, part_index]):
                    print('物业费:',wuye,'年代系数',year_index,'价格段系数',part_index)
                    self.price_evaluate_model = price_mean_normal * (1 + year_index + part_index) + wuye * self.area / 2
                    print('模型价格:', self.price_evaluate_model)
                    price_evaluate_normal = self.price_evaluate_model
                else:
                    # 普租1.08,1.05
                    if self.room_type == '3居':
                        price_evaluate_normal = price_mean_normal * 1.05
                    else:
                        price_evaluate_normal = price_mean_normal * 1.08

                price_diff_rate = (price_evaluate_normal - self.price_promotion) / self.price_promotion

                price_evaluate_normal = self.extension_adjust(price_evaluate_normal,price_diff_rate)
                # 一顶层处理
                price_evaluate_normal = self.one_top_adjust(price_evaluate_normal, one_top_index)

                print('续约整租有普租样本均价', price_evaluate_normal)
            else:
                print('无普租样本')
                price_evaluate_normal = 0

            # 对库存和普租样本进行判断, 并确定样本来源和产品版本
            if not any([sample_num_stock, sample_num_normal]):
                price_evaluate = self.last_for_analyst()

            else:
                # todo 比较样本量
                price_evaluate = self.compare(
                    price_evaluate_stock,
                    price_evaluate_normal,
                    sample_num_stock,
                    sample_num_normal,
                    self.source_edition_stock,
                    self.source_edition_normal)

            return price_evaluate

    def query_word(self):
        """定义查询语句"""
        # 友家
        self.condition_way_1 = '自如产品=="友家"'
        self.query_friend = f'{self.condition_way_1} & {self.condition_stock_status} & {self.condition_building}&{self.condition_balcony} &' \
            f'{self.condition_toilet}&{self.condition_area_top} &{self.condition_area_bottom}'
        # 整租
        self.condition_product_version = f'产品版本  in {self.edition}'
        self.condition_way_2 = f'自如产品!="友家" &  {self.condition_product_version}  '
        self.query_whole = f'{self.condition_way_2} & {self.condition_stock_status} & {self.condition_building} & {self.condition_room_type} &' \
                           f'{self.condition_area_top} & {self.condition_area_bottom} '

        # if self.way=='自如友家':
        #     print('当前查询语句:',self.query_friend)
        # else:
        #     print('当前查询语句:',self.query_whole)

    def get_query(self, df_type: pd.DataFrame, query_type):
        """分时间, 对特定盘进行相似类型查询"""

        for days_diff in (90, 180, 360):
            df = df_type.query(
                f'{query_type} & {self.condition_days(days_diff)}')
            num = df.count()[0]
            if num >= sample_num_request:
                price_mean = df['促销价格'].mean()
                return num, price_mean

        # 如果一年内没有出房超过2例, 则放弃库存表, 改用其他盘
        return 0, 0

    def condition_days(self, days):
        s = f'距离上次出租日期天数<={days}'
        return s

    def one_top_adjust(self, price_mean, one_top_index):
        """对新签一顶层的价格调整"""
        print('进行一顶层调整')
        if self.is_one_top:
            price = price_mean * one_top_index
        else:
            price = price_mean
        return price

    def extension_adjust(self, price_mean, price_diff_rate):
        """对续约确定价格, 及一顶层的价格调整"""
        print('进行续约定价调整')
        if price_diff_rate <= 0.03:
            price = price_mean
        elif price_diff_rate <= 0.08:
            price = (price_mean + self.price_promotion) / 2
        else:
            # price= self.last_for_analyst()
            price = self.price_promotion * 1.08

        return price

    def last_for_analyst(self):
        # 等待分析师处理
        self.price_evaluate = 0
        return self.price_evaluate

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

    def query_wuye_year(self, price: int):
        print('普租成交均价', price)
        df = df_normal.query(f'楼盘名称 == "{self.building}"')
        wuye = float(df['物业费'].max())
        year = float(df['年代系数'].max())
        # 要确保物业费有值, 否则返回空
        if not wuye > 0:
            print('无对应物业费信息')
            return None, None, None

        if price < 3000:
            part_index = 0.11
        elif price < 4000:
            part_index = 0.08
        elif price < 5000:
            part_index = 0.05
        elif price < 7000:
            part_index = 0.00001
        else:
            if price < 8000:
                part_index = -0.02
            elif price < 9000:
                part_index = -0.04
            elif price < 10000:
                part_index = -0.06
            else:
                part_index = -0.095

        return wuye, year, part_index

    def compare(
            self,
            price_evaluate_stock,
            price_evaluate_normal,
            sample_num_stock,
            sample_num_normal,
            source_edition_stock,
            source_edition_normal):
        """比较样本量,决定样本选择"""
        def whole_final_determine(source: str):
            self.price_source = source
            if source == '普租样本':
                price_evaluate = price_evaluate_normal
                self.source_edition = source_edition_normal
                print(sample_num_stock, sample_num_normal, '选b')
            else:
                price_evaluate = price_evaluate_stock
                self.source_edition = source_edition_stock
                print(sample_num_stock, sample_num_normal, '选a')

            return price_evaluate

        if sample_num_normal >= 30 or sample_num_stock < 2:
            price_evaluate = whole_final_determine('普租样本')
        elif sample_num_stock < 10:
            if 2 * sample_num_stock < sample_num_normal:
                price_evaluate = whole_final_determine('普租样本')
            else:
                price_evaluate = whole_final_determine('自如库存')
        else:
            price_evaluate = whole_final_determine('自如库存')

        return price_evaluate
