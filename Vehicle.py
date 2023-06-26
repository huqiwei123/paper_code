import random
import threading
import BS
import enviroment

all_location = ["l1", "l2", "l3", "l4", "l5"]
time_lock = enviroment.time_lock


class Vehicle:
    """
    车辆类

    Attributes:
        vehicle_no (int): 车辆编号
        bs (object): 车辆注册的基站
        cur_location (str): 车辆当前位置
        last_location (str): 车辆的上一个位置
        drive_thread: 车辆驱动行驶的线程

    Methods:
        register: 将本车辆注册到BS中去
        run: 车辆开始行驶
        drive_method: 车辆行驶的方法

    """
    vehicle_no = 1

    def __init__(self):
        self.vehicle_no = Vehicle.vehicle_no
        Vehicle.vehicle_no += 1
        self.bs = None
        self.cur_location = random.choice(all_location)
        self.last_location = None
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
        bs = BS.BS.get_bs()
        self.bs = bs
        bs.vehicle_register(self)
        return BS.BS.get_bs()

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
                    print(str(self.vehicle_no) + ": 11")
                    # 等待下一个时间离散点到达后发起通知
                    time_lock.wait()
                    print(str(self.vehicle_no) + ": 12")
                    self.last_location = self.cur_location
                    print(str(self.vehicle_no) + ": 13")
                    self.cur_location = random.choice(all_location)
                    print(str(self.vehicle_no) + ": 14")
