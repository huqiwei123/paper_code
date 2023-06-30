import random
import threading
import Enviroment

time_lock = Enviroment.time_lock
vehicle_lock = threading.Condition()


# todo: 如何去表征不同车辆的行驶习惯?
# todo: 如何去表征不同车辆的兴趣偏好对应的请求模型?
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
    vehicle_no = 1
    instance_num = 0
    barrier = threading.Barrier(0)

    # todo: 车辆通信范围
    communication_radius = 5

    def __init__(self):
        # 车辆唯一识别号
        self.vehicle_no = Vehicle.vehicle_no
        Vehicle.vehicle_no += 1
        Vehicle.instance_num += 1
        # 每实例化创建一辆车,在环境空间中进行计数
        Enviroment.Space.cur_vehicle_num += 1
        Vehicle.barrier = threading.Barrier(Vehicle.instance_num)

        self.bs = None
        # 车辆在初始化的时候,随机给定一个离散位置值
        self.cur_location = random.choice(Enviroment.all_location_label)
        self.last_location = None

        # 车辆在环境空间中的位置坐标,根据所在的离散位置,在位置中随机确定
        self.x = Enviroment.Space.judge_area(self.cur_location)[0]
        self.y = Enviroment.Space.judge_area(self.cur_location)[1]

        # 分簇后,簇内的其他车辆
        self.other_vehicle_within_cluster = []

        # 车辆缓存的内容,暂时定为10个内容,随机缓存
        self.cache_status = [random.randint(0, 1) for _ in range(10)]
        # 每辆车的缓存空间大小为80,每个内容的大小固定为20,也就是一辆车最多只能缓存4个内容
        self.cache_size = 80
        # 车辆当前请求的状态,是否发起请求
        self.request_status = None
        # 车辆当前的请求内容,请求暂定为内容号
        self.request_content = None

        # 记录每次请求的命中情况
        self.response_status_list = []

        # todo: 通过兴趣偏好学习方法实时生成并更新用户实时内容兴趣偏好
        self.theme_interest = []
        self.form_interest = []

        # todo: 车辆历史请求记录,用于根据用户的请求历史预测用户的内容兴趣偏好
        self.request_history = []

        # 通信范围内的所有车辆
        self.vehicle_within_area = []

        # 车辆运行的线程,脱离与主线程,每个车辆都有独立运行的子线程
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
            if not Enviroment.time_finished:
                with time_lock:
                    # 等待下一个时间离散点到达后,所有车辆开始更新到下一个位置
                    time_lock.wait()
                drive = Drive(self)
                drive.start()
                Vehicle.barrier.wait()
                cal_vehicle = Area(self)
                cal_vehicle.start()
                Vehicle.barrier.wait()
                # 当车辆由请求需要的时候,创建请求线程,并发起请求
                if self.request_status:
                    request = Request(self)
                    request.start()
                    request.join()
                else:
                    self.response_status_list.append(-1)
                # 所有车辆实例都已经行驶完成后,通知BS线程,可以开始观察了
                remain = Vehicle.barrier.wait()
                # 当最后一个线程执行完成时,通知bs线程
                if remain == 0:
                    with vehicle_lock:
                        vehicle_lock.notifyAll()

    # 车辆每隔1秒发生位置的变化
    # def drive_method(self):
    #     """
    #     车辆每个时间点的行驶和对内容的请求
    #
    #     Returns: None
    #
    #     """
    #     while True:
    #         if not Enviroment.time_finished:
    #             # 先要获得锁condition,再在锁的作用域中调用wait
    #             with time_lock:
    #                 # 等待下一个时间离散点到达后,所有车辆开始更新到下一个位置
    #                 time_lock.wait()
    #
    #                 # 车辆行驶过程
    #                 self.last_location = self.cur_location
    #                 self.cur_location = random.choice(Enviroment.all_location_label)
    #                 self.x = Enviroment.Space.judge_area(self.cur_location)[0]
    #                 self.y = Enviroment.Space.judge_area(self.cur_location)[1]
    #
    #                 # 车辆当前请求的状态,是否发起请求,暂时定为随机发起请求
    #                 self.request_status = False if random.randint(0, 1) == 0 else True
    #                 # todo: 车辆请求的内容应该和用户的兴趣偏好相关,大概率请求用户感兴趣的东西,这个可以通过csv去读给定的数据
    #                 self.request_content = 2
    #
    #                 # 当车辆发起请求时,需要将用户请求的内容(请求内容号)记录到历史记录中
    #                 if self.request_status:
    #                     self.request_history.append(self.request_content)
    #                 else:
    #                     # 如果本次车辆没有发起请求,则请求历史中添加-1表示没有发起请求
    #                     self.request_history.append(-1)
    #
    #                 # 车辆请求发起过程,当本地无法获得内容的时候,随机从其他车辆中请求内容
    #                 # todo: 当本地无法获得内容,需要写一个方法,在通信范围内的簇内车辆获取内容,如果通信范围内没有簇内车辆,则随机选择一个通信范围内的其他车辆
    #                 if self.request_status:
    #                     local_result = self.find_content(self.request_content)
    #                     if local_result:
    #                         self.response_status_list.append(True)
    #                     else:
    #                         request = Communication.Request(self)
    #                         request.run()
    #                 else:
    #                     self.response_status_list.append(-1)
    #                 Vehicle.thread_run_num += 1
    #                 # 所有车辆实例都已经行驶完成后,通知BS线程,可以开始观察了
    #                 if Vehicle.instance_num == Vehicle.thread_run_num:
    #                     with vehicle_lock:
    #                         vehicle_lock.notifyAll()

    # todo: 向哪辆车发起请求?
    def select_response_vehicle(self):
        """
        当车辆本地没有缓存内容,需要向其他车辆请求内容时,选择请求的车辆
        Returns:
            Object:
                响应车辆

        """
        # todo: 首先必须是通信范围内的车辆,其次在通信范围内的所有车辆中优先选择簇内车辆
        # 在所有通信范围内的车辆中遍历
        # if self.vehicle_within_area is None:
        #     raise Exception(f"{self.vehicle_no}号车辆通信范围内没有其他车辆,无法请求内容")
        # for vehicle in self.vehicle_within_area:

        if self == self.bs.vehicle_list[0]:
            return self.bs.vehicle_list[1]
        elif self == self.bs.vehicle_list[1]:
            return self.bs.vehicle_list[2]
        else:
            return self.bs.vehicle_list[1]

    # 内容获取,检查本地是否有内容
    def find_content(self, request_content):
        """

        Args:
            request_content: 请求的内容号

        Returns:
            Boolean:
                是否缓存有该内容

        """
        if self.cache_status[request_content - 1] == 1:
            return True
        else:
            # todo: 如果没有这个内容,是否要缓存这个内容?
            return False

    # todo: 如果内容没有被缓存,车辆判断是否要缓存该内容
    # def is_cahce(self):

    # todo: 如果内容满了,需要进行替换
    # def content_replace(self):


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
        self.vehicle.last_location = self.vehicle.cur_location
        self.vehicle.cur_location = random.choice(Enviroment.all_location_label)
        self.vehicle.x = Enviroment.Space.judge_area(self.vehicle.cur_location)[0]
        self.vehicle.y = Enviroment.Space.judge_area(self.vehicle.cur_location)[1]

        # 车辆当前请求的状态,是否发起请求,暂时定为随机发起请求
        self.vehicle.request_status = False if random.randint(0, 1) == 0 else True
        # todo: 车辆请求的内容应该和用户的兴趣偏好相关,大概率请求用户感兴趣的东西,这个可以通过csv去读给定的数据
        self.vehicle.request_content = 2

        # 当车辆发起请求时,需要将用户请求的内容(请求内容号)记录到历史记录中
        if self.vehicle.request_status:
            self.vehicle.request_history.append(self.vehicle.request_content)
        else:
            # 如果本次车辆没有发起请求,则请求历史中添加-1表示没有发起请求
            self.vehicle.request_history.append(-1)


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
        # 请求传递的次数
        self.request_num = 1
        # 请求是否命中的状态
        self.response_status = False

    def run(self) -> None:
        # 填入车辆请求的内容
        self.content_no = self.vehicle.request_content
        # 车辆请求发起过程,当本地无法获得内容的时候,随机从其他车辆中请求内容
        # todo: 当本地无法获得内容,需要写一个方法,在通信范围内的簇内车辆获取内容,如果通信范围内没有簇内车辆,则随机选择一个通信范围内的其他车辆
        local_result = self.vehicle.find_content(self.content_no)
        if local_result:
            self.vehicle.response_status_list.append(True)
        else:
            self.request_another()

    def request_another(self):

        # 发起请求,找到请求者要请求的响应对象
        response_vehicle = self.vehicle.select_response_vehicle()
        # 调用请求类中的Request中的request方法
        response_result = response_vehicle.find_content(self.content_no)
        self.response_status = response_result
        while not self.response_status and self.request_num < 10:
            # 调用请求车辆的方法,找到下一个需要响应的车辆,向该车辆去请求
            response_vehicle = response_vehicle.select_response_vehicle()
            # 对请求的处理结果
            response_result = response_vehicle.find_content(self.content_no)
            self.request_num += 1
            self.response_status = response_result
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
                x_diff = abs(self.vehicle.x - vehicle.x)
                y_diff = abs(self.vehicle.y - vehicle.y)
                import math
                distance = math.sqrt(x_diff ** 2 + y_diff ** 2)
                if distance <= Vehicle.communication_radius:
                    self.vehicle.vehicle_within_area.append(vehicle)
