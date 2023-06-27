import random
import threading
import time
import Vehicle
import BS

# 创建条件变量对象
time_lock = threading.Condition()

# 定义时间步长
time_step = 1

# 定义总的模拟时间
total_time = 900

# 定义一个标志，用于通知其他线程模拟时间已经结束
time_finished = False

# 表征离散化位置序列,将空间进行划分,每个空间用一个离散的字符来表示
all_location_label = ["l1", "l2", "l3", "l4", "l5", "l6", "l7", "l8", "l9", "l10", "l11", "l12", "l13", "l14", "l15",
                      "l16", "l17", "l18", "l19", "l20", "l21", "l22", "l23", "l24", "l25"]


# 定义整个系统
class System:
    time_system = None
    bs = None
    vehicle_list = []

    def __init__(self, vehicle_num: int):
        System.time_system = Time()
        System.bs = BS.BS()
        System.vehicle_list = Space.bulk_register(vehicle_num)
        System.time_system.run()
        System.bs.run()
        for vehicle in System.vehicle_list:
            vehicle.run()


# 定义时间
class Time:
    """
    模拟环境时间,离散化时间系统为每1s得到一个时间点,总共有100个时间点
    Attributes:
        __now(私有属性): 当前时间

    Methods:
        run_time: 时间系统开始运行
        run_time_method: 时间运行的方法
        now: 获取当前时间
    """

    def __init__(self):
        # 系统的初始时间为0
        self.__now = 0
        # 定义在Time类中定义一个时间线程,当Time被实例化时自动执行该时间线程
        self.time_thread = threading.Thread(target=self.run_time_method)

    def run(self):
        """
        系统模拟时间开始运行
        Returns:

        """
        self.time_thread.start()

    def run_time_method(self):
        """
        时间运行的方法
        Returns:

        """
        for now in range(total_time + 1):
            # 休眠时间步长
            time.sleep(time_step)
            self.__now = now
            # 等待time_step完成后,发出时间系统信号,通知所有其他线程运行
            with time_lock:
                time_lock.notifyAll()

        # 模拟时间已经结束,不发起通知,让所有其他等待线程阻塞
        with time_lock:
            global time_finished
            time_finished = True

    def now(self):
        """
        获取系统时间
        Returns: None

        """
        return self.__now


# 定义空间
class Space:
    """
    模拟环境空间
    todo: 环境空间需要有一张映射表,表征空间区域和离散化位置序列的对应关系

    Methods:
        bulk_register: (static)批量注册车辆
        judge_area: 将离散位置转变为空间坐标值
        todo: cal_throughput: 每个时间点计算环境数据中流量
    """

    width = 100
    height = 100
    cur_vehicle_num = 0

    # 根据车辆所在的离散位置来随机确定该离散位置中车辆的坐标
    @staticmethod
    def judge_area(location) -> list:
        """
        将离散位置值转变为空间坐标值
        Args:
            location: 离散位置值

        Returns:
            list:
                x,y坐标位置

        """
        coordinate = []
        # 确定x轴坐标(在离散位置空间中随机取值)
        if location in ["l1", "l6", "l11", "l16", "l21"]:
            coordinate.append(random.randrange(0, 20))
        elif location in ["l2", "l7", "l12", "l17", "l22"]:
            coordinate.append(random.randrange(20, 40))
        elif location in ["l3", "l8", "l13", "l18", "l23"]:
            coordinate.append(random.randrange(40, 60))
        elif location in ["l4", "l9", "l14", "l19", "l24"]:
            coordinate.append(random.randrange(60, 80))
        else:
            coordinate.append(random.randrange(80, 100))
        # 确定y轴坐标(在离散位置空间中随机取值)
        if location in ["l1", "l2", "l3", "l4", "l5"]:
            coordinate.append(random.randrange(80, 100))
        elif location in ["l6", "l7", "l8", "l9", "l10"]:
            coordinate.append(random.randrange(60, 80))
        elif location in ["l11", "l12", "l13", "l14", "l15"]:
            coordinate.append(random.randrange(40, 60))
        elif location in ["l16", "l17", "l18", "l19", "l20"]:
            coordinate.append(random.randrange(20, 40))
        else:
            coordinate.append(random.randrange(0, 20))
        return coordinate

    # 在环境中批量生成并注册车辆
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
            vehicle = Vehicle.Vehicle()
            vehicle.register()
            vehicle_list.append(vehicle)
        return vehicle_list
