import time

import Vehicle
import PPM
import threading
import enviroment

bs_lock = threading.Condition()

time_lock = enviroment.time_lock
vehicle_lock = Vehicle.vehicle_lock


class BS:
    """
    基站类

    Attributes:
        vehicle_list (list): store all vehicle object to a list
        vehicle_curlocation (dict): 车辆当前位置
        vehicle_path (dict): store all vehicle's path to a dict
        vehicle_tree (dict): store all vehicle's tree according to path to a dict
        prediction_result (dict) : 预测结果
        update: 基站更新路径和树结构的线程

    Methods:
        get_bs: 获取BS的唯一实例,不同车辆共用同一个BS实例
        vehicle_register: 车辆在BS上进行注册
        run: 基站线程开始运行,每个时间点,观察所有车辆当前位置,依次更新所有车辆当前位置, 路径序列, 路径树, 预测下一个位置
        update_curlocation(self): 观察所有车辆当前位置,更新到vehicle_curlocation中
        add_curlocation_to_path: 将所有注册车辆的当前位置加入到路径序列中
        update_tree: 当加入当前位置后,更新BS中所有车辆的树结构
        predict_nextlocation: 调用PPM算法预测所有注册车辆的下一个位置,并存储在预测结果的list中
        bs_thread: BS线程,每隔一段时间,观察注册车辆的当前位置,将当前位置加入到路径序列中,最后更新车辆的树结构
    """
    bs = None

    @staticmethod
    def get_bs() -> 'BS':
        """
        获取BS的唯一实例,不同车辆共用同一个BS实例
        Returns:
            object:
                所有车辆共享的BS唯一实例

        """
        if BS.bs is None:
            BS.bs = BS()
        return BS.bs

    def __init__(self):
        self.vehicle_list = []
        self.vehicle_curlocation = {}
        self.vehicle_path = {}
        self.vehicle_tree = {}
        self.prediction_result = {}
        self.update = threading.Thread(target=self.bs_thread)

    def __str__(self):
        vehicle_no = []
        for item in self.vehicle_list:
            vehicle_no.append(item.vehicle_no)
        return f"BS[vehicle_list={vehicle_no}, vehicle_path={self.vehicle_path}]"

    # 在BS中注册该车辆
    def vehicle_register(self, vehicle_obj: 'Vehicle'):
        """
        在BS上注册车辆
        Args:
            vehicle_obj (object): 被注册车辆的实例

        Returns: None

        """
        self.vehicle_list.append(vehicle_obj)
        self.vehicle_curlocation[vehicle_obj.vehicle_no] = vehicle_obj.cur_location
        self.vehicle_path[vehicle_obj.vehicle_no] = []
        self.vehicle_tree[vehicle_obj.vehicle_no] = PPM.BuildTree()
        self.prediction_result[vehicle_obj.vehicle_no] = ""

    def run(self):
        """
        基站线程开始运行,每个时间点,观察所有车辆当前位置,依次更新所有车辆当前位置, 路径序列, 路径树, 预测下一个位置
        Returns:

        """
        self.update.start()

    # 刷新车辆当前位置
    def update_curlocation(self):
        """
        BS每隔一定时间会观察所有注册车辆当前的位置并刷新记录信息
        Returns: None

        """
        for item in self.vehicle_list:
            self.vehicle_curlocation[item.vehicle_no] = item.cur_location
        return self

    # 在每个时间点开始时,迭代调用vehicle实例中的get_curlocation()方法获取车辆当前位置,将所有车辆当前位置加入到路径序列中
    def add_curlocation_to_path(self):
        """
        将所有注册车辆的当前位置加入到路径序列中

        Returns: None

        """
        for item in self.vehicle_list:
            vehicle_no = item.vehicle_no
            self.vehicle_path[vehicle_no].append(self.vehicle_curlocation[vehicle_no])
        return self

    # 获取车辆当前位置更新路径序列后,根据路径序列的最后三个位置,更新树
    def update_tree(self):
        """
        在调用add_curlocation_to_path后,同步更新BS中所有车辆的树结构

        Returns: None

        """
        for vehicle in self.vehicle_list:
            vehicle_no = vehicle.vehicle_no
            if len(self.vehicle_path[vehicle_no]) >= 3:
                self.vehicle_tree[vehicle_no].addTree(self.vehicle_path[vehicle_no][-3:])
        return self

    # 采用PPM算法根据路径树预测所有车辆的下一个位置,更新预测结果集
    def predict_nextlocation(self):
        """
        调用PPM算法,对BS中注册的每一辆车,预测其下一个位置
        Returns:
            dict:
                所有车辆的下一个位置

        """
        for item in self.vehicle_list:
            result = PPM.Predictor.predictor(item)
            self.prediction_result[item.vehicle_no] = result

    # 线程:每到达一个时间点将车辆当前路径加入到车辆对应的历史路径序列中,并更新树结构
    def bs_thread(self):
        """
        BS线程,每隔一段时间,观察注册车辆的当前位置,并更新车辆的树结构,并预测出车辆的下一个位置,更新prediction_result结果

        Returns: None

        """
        while True:
            with vehicle_lock:
                if not enviroment.time_finished:
                    # 等待所有车辆线程的位置更新后再去观察车辆当前位置,更新路径和树结构,并预测下一个位置
                    vehicle_lock.wait()
                    # todo: 等待车辆位置改变后再去观察车辆,与Vehicle线程间存在同步关系
                    self.update_curlocation().add_curlocation_to_path().update_tree()
                    self.predict_nextlocation()
                    Vehicle.Vehicle.thread_run_num = 0
                    with bs_lock:
                        # 通知需要读取BS数据的线程,等BS数据完成更新后,再去读取
                        bs_lock.notifyAll()
