import random
import threading
import Enviroment
import Communication

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
        response_status: 车辆请求内容的响应状态,描述请求是否成功
        drive_thread: 车辆驱动行驶的线程

    Methods:
        register: 将本车辆注册到BS中去
        run: 车辆开始行驶
        drive_method: 车辆行驶的方法
        local_search_content: 内容获取,检查本地是否有内容,如果没有就发起请求,暂定为指定车辆
        request_process: 响应车辆对请求的处理方法
        response_process: 请求车辆对响应的处理方法

    """
    vehicle_no = 1
    instance_num = 0
    thread_run_num = 0

    # todo: 车辆通信范围
    communication_radius = 5

    def __init__(self):
        # 车辆唯一识别号
        self.vehicle_no = Vehicle.vehicle_no
        Vehicle.vehicle_no += 1

        Vehicle.instance_num += 1
        # 每实例化创建一辆车,在环境空间中进行计数
        Enviroment.Space.cur_vehicle_num += 1

        self.bs = None
        self.cur_location = random.choice(Enviroment.all_location_label)
        self.last_location = None

        # 车辆在环境空间中的位置坐标,根据所在的离散位置,在位置中随机确定
        self.x = Enviroment.Space.judge_area(self.cur_location)[0]
        self.y = Enviroment.Space.judge_area(self.cur_location)[1]

        # 车辆缓存的内容,暂时定为10个内容,随机缓存
        self.cache_status = [random.randint(0, 1) for _ in range(10)]
        # 缓存空间大小
        self.cache_size = 100
        # 车辆当前请求的状态,是否发起请求,暂定为一定发起请求
        self.request_status = True
        # 车辆当前的请求内容,请求暂定为内容号,从1到10编号的内容中随机选择一个请求
        self.request_content = random.randint(1, 10) if self.request_status else None
        # 车辆当前请求是否成功
        self.response_status = False

        # todo: 通过兴趣偏好学习方法实时生成并更新用户实时内容兴趣偏好
        self.theme_interest = []
        self.form_interest = []

        # todo: 车辆历史请求记录
        self.quest_history = []

        # 为vehicle创建一个drive线程,每10s更新一次车辆位置,表征车辆正在行驶
        self.drive_thread = threading.Thread(target=self.drive_method)

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
        车辆开始行驶
        Returns: None

        """
        self.drive_thread.start()

    # todo: 车辆每隔1秒发生位置的变化,暂时定为随机,后期需要修改
    def drive_method(self):
        """
        车辆每个时间点的行驶和对内容的请求

        Returns: None

        """
        while True:
            if not Enviroment.time_finished:
                # 先要获得锁condition,再在锁的作用域中调用wait
                with time_lock:
                    # 等待下一个时间离散点到达后,所有车辆开始更新到下一个位置
                    time_lock.wait()

                    # 车辆行驶过程
                    self.last_location = self.cur_location
                    self.cur_location = random.choice(Enviroment.all_location_label)
                    self.x = Enviroment.Space.judge_area(self.cur_location)[0]
                    self.y = Enviroment.Space.judge_area(self.cur_location)[1]

                    # 车辆请求发起过程,当本地无法获得内容的时候,随机从其他车辆中请求内容
                    self.local_search_content(Enviroment.System.bs.vehicle_list[1])

                    Vehicle.thread_run_num += 1
                    # 所有车辆实例都已经行驶完成后,通知BS线程,可以开始观察了
                    if Vehicle.instance_num == Vehicle.thread_run_num:
                        with vehicle_lock:
                            vehicle_lock.notifyAll()

    # todo: 向哪辆车发起请求?

    # 内容获取,检查本地是否有内容,如果没有就发起请求,暂定为指定车辆
    def local_search_content(self, response_vehicle):
        """

        Args:
            response_vehicle: 当本地获取不到内容的时候,向指定车辆发起内容请求

        Returns: None

        """
        if self.request_status:
            if self.cache_status[self.request_status - 1] == 1:
                self.response_status = True
            else:
                # 创建一个发起请求的线程,并启动该线程
                request_thread = Communication.Request(self.request_content, self, response_vehicle)
                request_thread.start()

    # 车辆对收到的请求进行处理
    def request_process(self, quest_vehicle):
        """
        响应车辆对请求的处理方法
        Args:
            quest_vehicle: 请求车辆

        Returns: None

        """
        # 对请求者的请求进行处理,检查请求者的请求在本地是否有,如果有则返回
        if self.cache_status[quest_vehicle.request_content - 1] == 1:
            # 如果有内容,就创建一个响应线程,给予响应
            response_thread = Communication.Response(quest_vehicle.request_content, self, quest_vehicle)
            response_thread.start()

    # 车辆对收到的响应进行处理
    def response_process(self):
        """
        请求车辆对响应的处理方法
        Returns: None

        """
        self.response_status = True

    # todo: 如果内容没有被缓存,车辆判断是否要缓存该内容
    # def is_cahce(self):

    # todo: 如果内容满了,需要进行替换
    # def content_replace(self):
