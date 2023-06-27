import random
import threading
import enviroment

time_lock = enviroment.time_lock
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
        drive_thread: 车辆驱动行驶的线程

    Methods:
        register: 将本车辆注册到BS中去
        run: 车辆开始行驶
        drive_method: 车辆行驶的方法

    """
    vehicle_no = 1
    instance_num = 0
    thread_run_num = 0

    def __init__(self):
        # 车辆唯一识别号
        self.vehicle_no = Vehicle.vehicle_no
        Vehicle.vehicle_no += 1

        Vehicle.instance_num += 1
        # 每实例化创建一辆车,在环境空间中进行计数
        enviroment.Space.cur_vehicle_num += 1

        self.bs = None
        self.cur_location = random.choice(enviroment.all_location_label)
        self.last_location = None

        # 车辆在环境空间中的位置坐标,根据所在的离散位置,在位置中随机确定
        self.x = enviroment.Space.judge_area(self.cur_location)[0]
        self.y = enviroment.Space.judge_area(self.cur_location)[1]

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
        bs = enviroment.System.bs
        self.bs = bs
        bs.vehicle_register(self)
        return bs

    def run(self):
        """
        车辆开始行驶
        Returns: None

        """
        self.drive_thread.start()

    # todo:车辆每隔1秒发生位置的变化,暂时定为随机,后期需要修改
    def drive_method(self):
        """
        车辆行驶的方法

        Returns: None

        """
        while True:
            if not enviroment.time_finished:
                # 先要获得锁condition,再在锁的作用域中调用wait
                with time_lock:
                    # 等待下一个时间离散点到达后,所有车辆开始更新到下一个位置
                    time_lock.wait()
                    self.last_location = self.cur_location
                    self.cur_location = random.choice(enviroment.all_location_label)
                    self.x = enviroment.Space.judge_area(self.cur_location)[0]
                    self.y = enviroment.Space.judge_area(self.cur_location)[1]
                    Vehicle.thread_run_num += 1
                    # 所有车辆实例都已经行驶完成后,通知BS线程,可以开始观察了
                    if Vehicle.instance_num == Vehicle.thread_run_num:
                        with vehicle_lock:
                            vehicle_lock.notifyAll()
