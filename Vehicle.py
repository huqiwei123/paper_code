import random
import threading
import CSV_writer
import Content
import Enviroment
import ActivityLevel
import PreferenceLearning
import numpy as np

# 时间系统锁, 在每个时间点到来时,通知所有Vehicle线程开始一轮循环
time_lock = Enviroment.time_lock
# 车辆锁, 在车辆线程运行到某点或完成时, 发出通知, 通知其他等待车辆线程的线程开始运行
vehicle_lock = threading.Condition()


class Vehicle:
    """
    车辆类

    Attributes:
        vehicle_no (int): 车辆编号
        bs (object): 车辆注册的基站
        cur_location (str): 车辆当前位置
        last_location (str): 车辆的上一个位置
        x: 车辆在环境中的x坐标
        y: 车辆在环境中的y坐标
        cache_status: 描述车辆缓存的内容
        cache_size: 车辆缓存空间大小
        request_status: 车辆请求状态,车辆是否发起了请求
        request_content: 车辆请求的内容

    Methods:
        register: 将本车辆注册到BS中去
        run: 启动车辆运行线程
        run_method: 车辆运行线程,依次调用车辆行驶线程,计算车辆通信范围内的车辆集,如果有请求,则创建请求线程
        select_response_vehcile: 当车辆由请求需要的时候,选择向哪辆车发起请求
        find_content: 内容获取,检查本地是否有内容
    """
    # 车辆自增编号(唯一索引)
    vehicle_no = 1
    # 车辆总实例数
    instance_num = 0
    # 线程等待的屏障, 随这线程数的增加被更新, 当所有线程到达屏障时, 所有线程才从屏障处开始运行
    barrier = threading.Barrier(0)
    # 标记, 确保对BS的操作的代码段在所有车辆线程中只会有一个车辆线程运行一次
    code_executed = False
    # 标记, 确保计算所有车辆缓存命中率在所有车辆线程中只有一个车辆线程运行一次
    cal_cache_hit = False
    # 车辆可以缓存内容的总数
    cache_num = 50
    # 车辆通信范围
    communication_radius = 100
    # 确保barrier.reset在所有线程的第一个线程运行时运行一次
    vehicle_barrier1 = False
    vehicle_barrier2 = False
    vehicle_barrier3 = False

    def __init__(self):
        # 车辆唯一识别号, 每次实例一辆车时,自动加一
        self.vehicle_no = Vehicle.vehicle_no
        Vehicle.vehicle_no += 1
        # 车辆生成的实例数
        Vehicle.instance_num += 1
        # 每实例化创建一辆车,在环境空间中进行计数
        Enviroment.Space.cur_vehicle_num += 1
        # 每实例化创建一辆车, 需要更新线程屏障数, 保证所有车辆线程达到屏障时才被全部唤醒
        Vehicle.barrier = threading.Barrier(Vehicle.instance_num)
        # 车辆注册的bs, 车辆在bs中注册的时候赋值
        self.bs = None

        # 最经常走的路径的起点和终点, tuple表示(start, end)
        self.start_end = random.choice(list(CSV_writer.all_path.keys()))
        # 最经常走的路径的起点和终点的所有可能的路径集
        self.all_path = CSV_writer.all_path[self.start_end]
        # 从最经常走的路径的起点和终点的所有可能的路径集中选择一个路径作为最经常走的路径
        self.habbit = random.choice(self.all_path)
        # 当前走正在走的路径, 初始时默认为习惯路径
        self.cur_path = self.habbit
        # 指示在当前路径上的第几个位置,如果达到当前路径的终点位置,则需要重新选择路径,以大概率选择习惯走的路径
        self.path_num = 0

        # 车辆在初始化的时候,当前位置为习惯最常走的路径的初始点
        self.cur_location = self.start_end[0]
        self.last_location = None

        # 车辆在环境空间中的位置坐标,根据所在的离散位置,在位置中随机确定
        self.x = Enviroment.Space.judge_area(self.cur_location)[0]
        self.y = Enviroment.Space.judge_area(self.cur_location)[1]

        # 在每个时间点内, 分簇后, 簇内的其他车辆
        self.other_vehicle_within_cluster = []

        # 车辆缓存的内容, cache_status由Vehicle.cache_num参数来决定最多可缓存的内容的总数, 初始时通过random_cahce_content方法随机决定每辆车的缓存内容
        self.cache_status = random_cache_content()
        # 每辆车的缓存空间大小为50MB,每个内容的大小固定为1MB,也就是一辆车最多只能缓存50个内容
        self.cache_size = 50
        # 车辆当前请求的状态,是否发起请求
        self.request_status = None

        # 判断这辆车是否是活跃车辆,如果这辆车是活跃车辆,在接下来的几个时间点会根据自己的兴趣多次进行请求
        random_num = random.randint(1, 10)
        # 初始化车辆时,概率为0.2可能为活跃车辆,如果这辆车是活跃车辆,那么在接下来会出现多次请求,否则请求状态为0
        self.activity = True if random_num < 3 else False
        # 初始化车辆时, 如果是活跃车辆,设定请求数, 请求次数在8次到15次随机取值, 否则请求次数为0
        self.request_num = random.randint(8, 15) if self.activity else 0
        # 不活跃的车辆将等待, 在接下来的几个时间点不发起请求
        self.wait_num = random.randint(5, 10) if self.activity is False else 0

        # 车辆历史请求记录,用于计算用户活跃度
        self.request_status_history = []

        # 车辆当前的请求内容,请求暂定为内容号
        self.request_content = None

        # 请求的跳数(不管命中还是没有命中)
        self.hop_count = 0
        # 在每个时间点的请求的响应状态
        self.cur_response_status = False
        # 记录每次请求的命中情况(也就是响应的状态)
        self.response_status_list = []

        # 车辆对内容主题的兴趣偏好
        self.interest_theme = random.choice(Content.content_theme)
        # 车辆对内容格式的兴趣偏好
        self.interest_form = random.choice(Content.content_form)

        # 实例化一个该车辆的用户偏好对象user_preference, 该用户对内容的主题和格式的兴趣偏好封装在一个对象中,可以调用对象中的方法更新用户对主题和格式的兴趣偏好
        self.user_preference = PreferenceLearning.UserPreference()

        # 车辆历史请求记录,用于根据用户的请求历史预测用户的内容兴趣偏好
        self.request_history = []

        # 通信范围内的所有车辆
        self.vehicle_within_area = []

        # 车辆在簇内的活跃度
        self.activity_level = 0

        # 请求终止的车辆号, 如果车辆在某时间点发起请求, 但是request_vehicle = -1, 则说明车辆请求失败,没有获取到内容
        self.request_vehicle = -1

        # 车辆运行的线程,脱离主线程,每个车辆都有独立运行的子线程
        self.run_thread = threading.Thread(target=self.run_method)

    def __str__(self):
        return f"Vehicle[vehicle_no={self.vehicle_no}, cur_location={self.cur_location}]"

    # 在BS中注册本车辆
    def register(self):
        """
        将本车辆注册到BS中去
        Returns: None

        """
        bs = Enviroment.System.bs
        self.bs = bs
        bs.vehicle_register(self)
        return bs

    def run(self):
        """
        调用run方法,启动车辆的线程
        Returns:

        """
        self.run_thread.start()

    def run_method(self):
        """
        车辆开始行驶的线程
        Returns: None

        """
        while True:
            # 实验的总体时间,如果系统总实验时间到, 则结束线程的运行
            if not Enviroment.time_finished:

                # 需要等到每个时间点的达到,该线程才能运行,否则被阻塞
                with time_lock:
                    time_lock.wait()

                # todo: 这里可以模拟车辆的运行速度
                # 时间线程每运行三次,车辆位置才会改变,确保同一个簇内的车辆在接下来3个时间点的相对位置不变,仍然处于同一个簇内
                if (Enviroment.Time.counter - 1) % 5 == 0:
                    drive = Drive(self)
                    drive.start()

                # 在新一轮的时间点, 重置所有车辆的状态, 再发起请求, 对请求结果进行统计
                self.request_status = None
                self.request_content = None
                self.hop_count = 0
                self.cur_response_status = None
                # -1表示没有获得到内容, 没有请求到车辆
                self.request_vehicle = -1

                # 需要所有车辆行驶线程完成位置更新后,bs才能遍历所有车辆当前更新后的位置,完成自己的工作
                Vehicle.barrier.wait()
                if not Vehicle.vehicle_barrier1:
                    Vehicle.barrier.reset()
                    Vehicle.vehicle_barrier1 = True

                # 设置车辆的请求状态
                # 用于设定车辆为活跃车辆的概率数字
                random_activity = random.randint(1, 10)
                # 本此请求数没有达到,继续请求,请求状态为True
                if self.request_num != 0:
                    self.request_num -= 1
                    self.request_status = True
                # 等待数没有达到, 仍处于等待的状态
                if self.wait_num != 0:
                    self.wait_num -= 1
                    self.request_status = False
                # 当请求次数或等待次数达到0时, 重新依概率决定车辆是否是活跃车辆
                if self.request_num == 0 and self.wait_num == 0:
                    # 以概率为0.2设置车辆为活跃车辆,同时设定接下来的请求发起次数
                    self.activity = True if random_activity < 3 else False
                    # 如果是活跃车辆, 设定接下来多个连续时间点会发起请求的次数
                    self.request_num = random.randint(8, 15) if self.activity else 0
                    # 如果不是活跃车辆, 设定接下来多个连续时间点等待的次数
                    self.wait_num = random.randint(5, 10) if self.activity is False else 0
                    # 当前开始发起请求的话, 请求数需要减一
                    if self.activity:
                        self.request_num -= 1
                    # 发起请求
                    if not self.activity:
                        self.wait_num -= 1
                    self.request_status = True if self.activity else False

                # 根据车辆的请求状态, 设定车辆的请求内容
                # 记录车辆历史请求状态,1表示发起请求,0表示没有发起请求,用于计算用户的近期活跃度
                if self.request_status:
                    self.request_status_history.append(1)
                    # 车辆请求的内容应该和用户的兴趣偏好相关
                    random_num = random.randint(1, 10)
                    # 以0.1的概率随机选择内容
                    if random_num > 10:
                        self.request_content = random.choice(Enviroment.System.content_list)
                    # 以0.6的概率选择用户感兴趣的主题的内容
                    elif random_num > 3 and random_num <= 10:
                        self.request_content = random.choice(Enviroment.System.content_by_theme[self.interest_theme])
                    # 以0.3的概率选择用户感兴趣的格式的内容
                    else:
                        self.request_content = random.choice(Enviroment.System.content_by_form[self.interest_form])

                    # # 车辆请求内容request_content所属主题的向量表示
                    # request_content_theme = self.request_content.theme_arr
                    # # 车辆请求内容request_content所属格式的向量表示
                    # request_content_form = self.request_content.form_arr

                    # 根据当前请求内容的主题更新用户对内容主题的兴趣偏好向量
                    self.user_preference.update_user_preference_for_theme(self.request_content)
                    # 根据当前请求内容的格式更新用户对内容格式的兴趣偏好向量
                    self.user_preference.update_user_preference_for_form(self.request_content)
                    self.request_history.append(self.request_content)
                else:
                    self.request_status_history.append(0)
                    self.request_history.append(-1)

                # 每个时间点在所有实例线程中只能运行一次
                if not Vehicle.code_executed:
                    # 和车辆行驶的线程同步, 每过3个时间点, bs会观察所有车辆的当前位置, 并更新路径序列,路径树,并预测未来路径再进行分簇
                    if Enviroment.Time.counter % 5 == 0:
                        self.bs.update_curlocation().add_curlocation_to_path().update_tree()
                        self.bs.predict_nextlocation()
                        self.bs.classify()
                        self.bs.inform_classify_result()
                    Vehicle.code_executed = True

                # 需要等待所有车辆的请求状态确定后才能计算活跃度
                Vehicle.barrier.wait()
                if not Vehicle.vehicle_barrier2:
                    Vehicle.barrier.reset()
                    Vehicle.vehicle_barrier2 = True
                # 计算每辆车的活跃度
                self.activity_level = ActivityLevel.ActivityLevel.cal_activity_level(self)

                # 车辆每过3个时间点才发生位置的改变,所以每过三个时间点,才会计算车辆通信范围内所有其他车辆集
                if (Enviroment.Time.counter - 1) % 5 == 0:
                    cal_vehicle = Area(self)
                    cal_vehicle.start()

                # 等待所有车辆计算完通信范围内的所有其他车辆集后再发起请求
                Vehicle.barrier.wait()
                if not Vehicle.vehicle_barrier3:
                    Vehicle.barrier.reset()
                    Vehicle.vehicle_barrier3 = True

                # 当车辆有请求需要的时候,创建请求线程,并发起请求
                if self.request_status:
                    request = Request(self)
                    request.start()
                    request.join()
                else:
                    self.response_status_list.append(-1)

                # 等待所有请求完成后,可以开始观察
                Vehicle.barrier.wait()
                # 计算缓存命中率
                if not Vehicle.cal_cache_hit:
                    self.bs.cal_cache_hit_ration()
                    Vehicle.cal_cache_hit = True

                # 等待所有线程完成后,将code_executed和cal_cache_hit置为False
                remain = Vehicle.barrier.wait()

                # 当最后一个线程到达的时候执行
                if remain == 0:
                    Vehicle.code_executed = False
                    Vehicle.cal_cache_hit = False
                    Vehicle.vehicle_barrier1 = False
                    Vehicle.vehicle_barrier2 = False
                    Vehicle.vehicle_barrier3 = False
                    Vehicle.barrier.reset()
                    with vehicle_lock:
                        vehicle_lock.notifyAll()

                # 所有车辆实例都已经行驶完成后,通知BS线程,可以开始观察了

                # remain = Vehicle.barrier.wait()
                # # 当最后一个线程执行完成时,通知bs线程
                # if remain == 0:
                #     with vehicle_lock:
                #         vehicle_lock.notifyAll()
                # Vehicle.barrier.reset()

    # 作为请求源,发起请求
    def select_response_vehicle_as_origin(self, exclude_vehicle_list):
        """
        当车辆本地没有缓存内容,需要向其他车辆请求内容时,选择请求的车辆的策略:
        如果通信范围内没有车辆,返回为None
        在通信范围内优先选择同一簇内且距离最近的车辆,如果没有同一簇内的车辆,选择通信范围内最近的车辆
        Returns:
            Object:
                响应车辆

        """
        # 在请求的时候需要排除掉已经请求过的车辆
        exclude_vehicle_set = set(exclude_vehicle_list)
        # 排除通信范围内已经请求过的车辆
        vehicle_within_area_set = set(self.vehicle_within_area).difference(exclude_vehicle_set)
        if len(vehicle_within_area_set) == 0:
            # 通信范围内没有其他还没有请求的车辆,无法请求,也就是cur_response_status为False
            return None
        else:
            # 簇内车辆集合
            other_vehicle_within_cluster_set = set(self.other_vehicle_within_cluster)
            intersection = vehicle_within_area_set.intersection(other_vehicle_within_cluster_set)
            # 如果通信范围内没有簇内车辆,则向距离最近的通信范围内的其他车辆发出请求
            if len(intersection) == 0:
                return self.min_distance_vehicle(list(vehicle_within_area_set))
            else:
                inter = list(intersection)
                return self.min_distance_vehicle(inter)

    # 作为中继节点,发起请求
    def select_response_vehicle_as_relay(self, vehicle, exclude_vehicle_list):
        """
        作为中继节点,选择响应车辆的策略和请求源不同
        如果通信范围内没有车辆,返回None
        首先考虑通信范围内和请求源在同一个簇内且距离最近的车辆,如果没有则请求通信范围内其他距离最近的车辆
        Args:
            vehicle: 源请求车辆
        Returns:
            Object:
                响应车辆

        """
        # 在所有通信范围内的车辆中遍历
        exclude_vehicle_set = set(exclude_vehicle_list)
        # 排除通信范围内已经请求过的车辆
        vehicle_within_area_set = set(self.vehicle_within_area).difference(exclude_vehicle_set)
        if len(vehicle_within_area_set) == 0:
            return None
        else:
            other_vehicle_whitin_cluster_for_origin_set = set(vehicle.other_vehicle_within_cluster)
            intersection = vehicle_within_area_set.intersection(other_vehicle_whitin_cluster_for_origin_set)
            if len(intersection) == 0:
                return self.min_distance_vehicle(list(vehicle_within_area_set))
            else:
                inter = list(intersection)
                return self.min_distance_vehicle(inter)

    def min_distance_vehicle(self, vehicle_list):
        """
        计算所有车辆集vehicle_list,距离自身最近的车辆
        Args:
            vehicle_list: 车辆集

        Returns:

        """
        min_distance_vehicle = vehicle_list[0]
        min_distance = self.cal_distance(min_distance_vehicle)
        for vehicle in vehicle_list:
            cur_distance = self.cal_distance(vehicle)
            if cur_distance < min_distance:
                min_distance = cur_distance
                min_distance_vehicle = vehicle
        return min_distance_vehicle

        # if self == self.bs.vehicle_list[0]:
        #     return self.bs.vehicle_list[1]
        # elif self == self.bs.vehicle_list[1]:
        #     return self.bs.vehicle_list[2]
        # else:
        #     return self.bs.vehicle_list[1]

    # 内容获取,检查本地是否有内容
    def find_content(self, request_content):
        """
        Args:
            request_content: 请求的内容号

        Returns:
            Boolean:
                是否缓存有该内容

        """
        if self.cache_status[request_content.content_no - 1] == 1:
            return True
        else:
            # 判断这个内容request_content是否需要缓存
            is_cache = self.is_cahce(request_content)
            # 当前缓存空间是否已满
            is_full = self.is_full()
            if is_cache:
                if is_full:
                    # 内容满了,需要替换, 暂时采用随机替换策略, 把第一个出现的内容给替换掉
                    self.content_replace()
                    self.cache_status[request_content.content_no - 1] = 1

                else:
                    self.cache_status[request_content.content_no - 1] = 1
            else:
                pass
            return False

    def cal_distance(self, vehicle):
        """
        计算自身和其他车辆之间的距离
        Args:
            vehicle: 其他车辆

        Returns:
            距离
        """
        x_diff = abs(self.x - vehicle.x)
        y_diff = abs(self.y - vehicle.y)
        import math
        distance = math.sqrt(x_diff ** 2 + y_diff ** 2)
        return distance

    def is_full(self):
        """
        判断缓存空间是否已满
        Returns:

        """
        content_num = 0
        for each in self.cache_status:
            if each == 1:
                content_num += 1
                if content_num == Vehicle.cache_num:
                    return True
        return False

    # 如果内容没有被缓存,车辆判断是否要缓存该内容
    def is_cahce(self, request_content):
        """
        策略: 将簇内的车辆活跃度和兴趣偏好向量概率分布乘积加和
        Returns:
            Boolean: True要缓存,False不缓存

        """
        # 总是缓存的策略
        # return True

        content_theme_preference = self.cal_content_theme_preference_probability_distrubition()
        content_form_preference = self.cal_content_form_preference_probability_distrubition()
        # 内容主题向量
        content_theme_arr = request_content.theme_arr
        # 内容格式向量
        content_form_arr = request_content.form_arr

        theme_match_degree = dot(content_theme_preference, content_theme_arr)

        form_match_degree = dot(content_form_preference, content_form_arr)

        # 内容主题匹配度占比0.8, 内容格式匹配度占比0.2
        match_degree = 0.8 * theme_match_degree + 0.2 * form_match_degree

        p_min = min(content_theme_preference)
        p_max = max(content_theme_preference)
        q_min = min(content_form_preference)
        q_max = max(content_form_preference)

        match_degree_threshold = 0.8 * (p_min + q_min) + 0.2 * (p_max + q_max)

        if match_degree > match_degree_threshold:
            return True
        else:
            return False


    # 计算车辆缓存内容主题的偏好概率分布
    def cal_content_theme_preference_probability_distrubition(self):
        factor = []
        list = []
        factor.append(self.activity_level)
        list.append(self.user_preference.probability_distribution_for_theme)
        for vehicle in self.other_vehicle_within_cluster:
            factor.append(vehicle.activity_level)
            list.append(vehicle.user_preference.probability_distribution_for_theme)
        result = []
        for each, fac in zip(list, factor):
            middle = [x * fac for x in each]
            result.append(middle)
        content_theme_preference = [sum(x) for x in zip(*result)]
        return content_theme_preference


    # 计算车辆缓存内容格式的偏好概率分布
    def cal_content_form_preference_probability_distrubition(self):
        factor = []
        list = []
        factor.append(self.activity_level)
        list.append(self.user_preference.probability_distribution_for_form)
        for vehicle in self.other_vehicle_within_cluster:
            factor.append(vehicle.activity_level)
            list.append(vehicle.user_preference.probability_distribution_for_form)
        result = []
        for each, fac in zip(list, factor):
            middle = [x * fac for x in each]
            result.append(middle)
        content_form_preference = [sum(x) for x in zip(*result)]
        return content_form_preference

    # 如果内容满了,需要进行替换, 采用随机替换的方法, 随机选择一个内容, 从缓存中去掉
    def content_replace(self):
        # 内容满了,需要替换, 暂时采用随机替换策略
        indices = [index for index, element in enumerate(self.cache_status) if element == 1]
        if indices:
            random_index = random.choice(indices)
            self.cache_status[random_index] = 0

# 车辆行驶线程
class Drive(threading.Thread):
    """
    车辆行驶,位置改变的线程,同时赋值车辆的请求状态和请求内容,并将请求的内容加入到历史请求集合中,用来判断用户的兴趣偏好
    """
    drive_lock = threading.Condition()

    def __init__(self, vehicle):
        super().__init__()
        self.vehicle = vehicle

    def run(self) -> None:
        # 车辆行驶过程

        cur_path_length = len(self.vehicle.cur_path)

        # 车辆还没有到该路径的终点
        if self.vehicle.path_num < cur_path_length - 1:
            self.vehicle.last_location = self.vehicle.cur_location
            self.vehicle.cur_location = self.vehicle.cur_path[self.vehicle.path_num]
            self.vehicle.path_num += 1
        # 车辆到达当前最路径的终点处
        else:
            self.vehicle.last_location = self.vehicle.cur_location
            self.vehicle.cur_location = self.vehicle.cur_path[self.vehicle.path_num]
            self.vehicle.path_num = 0
            # 0.9的概率选择习惯走的路径,0.1的概率随机选择其他路径
            random_num = random.randint(1, 10)
            if random_num > 4:
                self.vehicle.cur_path = random.choice(self.vehicle.all_path)
            else:
                self.vehicle.cur_path = self.vehicle.habbit



        self.vehicle.x = Enviroment.Space.judge_area(self.vehicle.cur_location)[0]
        self.vehicle.y = Enviroment.Space.judge_area(self.vehicle.cur_location)[1]


# 车辆请求线程
class Request(threading.Thread):
    """
    车辆发起请求的线程
    """

    def __init__(self, vehicle):
        super().__init__()
        # 发起请求的车辆
        self.vehicle = vehicle
        # 请求的内容号
        self.content_no = None
        # 请求传递的次数,初始为0
        self.request_num = 0
        # 请求是否命中的状态
        self.response_status = False
        # 请求成功的车辆号
        self.response_vehicle = -1
        # 已经请求过的车辆集, 不能再次请求
        self.have_been_requested = []

    def run(self) -> None:
        # 填入车辆请求的内容
        self.content_no = self.vehicle.request_content.content_no
        # 车辆请求发起过程,当本地无法获得内容的时候,随机从其他车辆中请求内容
        local_result = self.vehicle.find_content(self.vehicle.request_content)
        self.have_been_requested.append(self.vehicle)
        if local_result:
            self.response_vehicle = self.vehicle.vehicle_no
            self.vehicle.hop_count = self.request_num
            self.response_status = True
            self.vehicle.cur_response_status = self.response_status
            self.vehicle.request_vehicle = self.vehicle.vehicle_no
            self.vehicle.response_status_list.append(True)
        else:
            self.request_another()

    # 向另一辆车发起请求
    def request_another(self):
        """
        不考虑车辆的通信范围,先在车辆所在的簇内寻找内容,若找不到,则到簇外寻找
        Returns:
        """
        # 在簇内车辆中寻找内容
        # for vehicle in self.vehicle.other_vehicle_within_cluster:
        #     self.request_num += 1
        #     # 当请求次数超过一定跳数的时候,放弃请求,认为请求失败
        #     if self.request_num > 20:
        #         return
        #     # 在簇内车辆集中找,找到则返回
        #     if vehicle.find_content(self.content_no):
        #         self.response_status = True
        #         self.vehicle.response_status_list.append(True)
        #         return
        # other_vehicle_within_cluster_set = set(self.vehicle.other_vehicle_within_cluster)
        # vehicle_list = set(self.vehicle.bs.vehicle_list)
        # # 簇外车辆集,簇内车辆找不到内容就到簇外车辆中寻找内容
        # other_vehicle_out_cluster_set = vehicle_list.difference(other_vehicle_within_cluster_set)
        # for vehicle in other_vehicle_out_cluster_set:
        #     self.request_num += 1
        #     if self.request_num > 20:
        #         return
        #     if vehicle.find_content(self.content_no):
        #         self.response_status = True
        #         self.vehicle.response_status_list.append(True)
        #         return

        # 发起请求,找到请求者要请求的响应对象
        # 初始,源请求车辆选择响应的车辆发起请求
        self.request_num += 1
        response_vehicle = self.vehicle.select_response_vehicle_as_origin(self.have_been_requested)
        self.have_been_requested.append(response_vehicle)
        # 调用请求类中的Request中的request方法
        if response_vehicle is None:
            self.vehicle.hop_count = self.request_num
            self.vehicle.cur_response_status = False
            self.vehicle.response_status_list.append(False)
            self.vehicle.request_vehicle = -1
            return
        response_result = response_vehicle.find_content(self.vehicle.request_content)
        if response_result:
            self.response_vehicle = response_vehicle.vehicle_no
            self.vehicle.request_vehicle = response_vehicle.vehicle_no
        self.response_status = response_result
        while not self.response_status and self.request_num < 20:
            # 调用请求车辆的方法,找到下一个需要响应的车辆,向该车辆去请求
            self.request_num += 1
            response_vehicle = response_vehicle.select_response_vehicle_as_relay(self.vehicle, self.have_been_requested)
            self.have_been_requested.append(response_vehicle)
            # 对请求的处理结果
            if response_vehicle is None:
                self.vehicle.hop_count = self.request_num
                self.vehicle.cur_response_status = False
                self.vehicle.response_status_list.append(False)
                self.vehicle.request_vehicle = -1
                return
            response_result = response_vehicle.find_content(self.vehicle.request_content)
            if response_result:
                self.response_vehicle = response_vehicle.vehicle_no
                self.vehicle.request_vehicle = response_vehicle.vehicle_no
            self.response_status = response_result
        self.vehicle.hop_count = self.request_num
        self.vehicle.cur_response_status = response_result
        self.vehicle.response_status_list.append(self.response_status)


# 计算通信范围内的所有车辆的线程
class Area(threading.Thread):
    """
    车辆计算通信范围内其他车辆集的线程
    """

    def __init__(self, vehicle):
        super().__init__()
        self.vehicle = vehicle

    def run(self) -> None:
        for vehicle in Enviroment.System.bs.vehicle_list:
            if vehicle is not self.vehicle:
                distance = self.vehicle.cal_distance(vehicle)
                if distance <= Vehicle.communication_radius:
                    self.vehicle.vehicle_within_area.append(vehicle)

# 车辆初始的缓存状态, 缓存状态随机决定,但是一辆车最多只能缓存4个内容
def random_cache_content():
    target_count = Vehicle.cache_num
    result = []
    count_1 = 0
    while count_1 < target_count:
        value = random.randint(0, 1)
        result.append(value)
        if value == 1:
            count_1 += 1
    content_num = len(Enviroment.System.content_list)
    result.extend([0] * (content_num - len(result)))
    return result

def dot(list1, list2):
    result = [x * y for x, y in zip(list1, list2)]
    return sum(result)


