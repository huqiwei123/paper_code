import random
import threading
import BS
import enviroment

all_location = ["l1", "l2", "l3", "l4", "l5", "l6"]
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
        drive_thread: 车辆驱动行驶的线程

    Methods:
        register: 将本车辆注册到BS中去
        run: 车辆开始行驶
        drive_method: 车辆行驶的方法
        bulk_register: (static)批量注册车辆

    """
    vehicle_no = 1
    instance_num = 0
    thread_run_num = 0

    def __init__(self):
        self.vehicle_no = Vehicle.vehicle_no
        Vehicle.vehicle_no += 1
        Vehicle.instance_num += 1
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
                    # 等待下一个时间离散点到达后,所有车辆开始更新到下一个位置
                    time_lock.wait()
                    self.last_location = self.cur_location
                    self.cur_location = random.choice(all_location)
                    Vehicle.thread_run_num += 1
                    # 所有车辆实例都已经行驶完成后,通知BS线程,可以开始观察了
                    if Vehicle.instance_num == Vehicle.thread_run_num:
                        with vehicle_lock:
                            vehicle_lock.notifyAll()

    # 批量生成并注册车辆
    @staticmethod
    def bulk_register(num: int) -> list:
        """

        Args:
            num: 注册车辆的数量

        Returns:
            list:
                已注册车辆列表

        """
        vehicle_list = []
        for i in range(num):
            vehicle = Vehicle()
            vehicle.register()
            vehicle_list.append(vehicle)
        return vehicle_list
