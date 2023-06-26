import threading
import time

# 创建条件变量对象
time_lock = threading.Condition()

# 定义时间步长
time_step = 1

# 定义总的模拟时间
total_time = 100

# 定义一个标志，用于通知其他线程模拟时间已经结束
time_finished = False


# 定义环境时间
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

    time_system = None

    # 获取全局唯一实例Time(time_system)
    @staticmethod
    def get_time_system():
        if Time.time_system is None:
            Time.time_system = Time()
        return Time.time_system

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
            print(4)
            # 等待time_step完成后,发出时间系统信号,通知所有其他线程运行
            with time_lock:
                print(5)
                time_lock.notifyAll()
                print(6)

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

# 定义环境空间
# todo: class Space:
