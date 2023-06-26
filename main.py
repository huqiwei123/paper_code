import BS
import PPM
import Vehicle
import enviroment

"""
usage: test
"""

time_lock = enviroment.time_lock


class TestAddition:
    """
        Methods:
            test_build_tree: 测试利用路径序列构建路径树
            test_print_path: 测试打印路径序列
            test_BS_prediction: 测试bs实例中根据所有车辆的路径树/上一个位置/当前位置预测车辆的下一个位置
            test_time_system: 测试时间系统
    """

    def test_build_tree(self):
        alist = ["l1", "l2", "l3", "l4", "l2", "l3", "l2", "l3"]
        tree = PPM.BuildTree()
        tree.createTree(alist)
        PPM.print_tree_pattern(tree.root)

    def test_print_path(self):
        time_system = enviroment.Time.get_time_system()
        bs = BS.BS.get_bs()
        vehicle1 = Vehicle.Vehicle()
        vehicle1.register()
        vehicle2 = Vehicle.Vehicle()
        vehicle2.register()
        time_system.run()
        vehicle1.run()
        vehicle2.run()
        bs.run()
        while True:
            with time_lock:
                if not enviroment.time_finished:
                    # 等待时间系统到达下一个离散时间点时发起通知
                    time_lock.wait()
                    print(bs.vehicle_path[vehicle1.vehicle_no])

    # todo: 当前问题:时间设定为5s,BS每1s读取一次环境中的车辆当前路径,而在5s时间内所构建的路径序列中只有2个位置
    def test_BS_prediction(self):
        # 实例化一个环境时间
        time_system = enviroment.Time.get_time_system()
        time_system.run()
        # 获得全局唯一的bs实例
        bs = BS.BS.get_bs()
        bs.run()
        # 注册vehicle1
        vehicle1 = Vehicle.Vehicle()
        vehicle1.register()
        vehicle1.run()
        # 注册vehicle2
        vehicle2 = Vehicle.Vehicle()
        vehicle2.register()
        vehicle2.run()
        # 利用离散时间点的前面10s构建树
        while time_system.now() < 100:
            with time_lock:
                # todo:与BS线程间存在同步关系,需要BS观察车辆并更新数据后,在读取
                # question: 由于没有同步可能导致出现路径有时候多打一个或少打一个
                time_lock.wait()
                print(bs.vehicle_path[vehicle1.vehicle_no])
                print(bs.vehicle_path[vehicle2.vehicle_no])
        # PPM.print_tree_pattern(bs.vehicle_tree[vehicle1.vehicle_no].root)
        # PPM.print_tree_pattern(bs.vehicle_tree[vehicle2.vehicle_no].root)
        # print("vehicle1上一个位置: " + vehicle1.last_location)
        # print("vehicle1当前位置 " + vehicle1.cur_location)
        # print("vehicle2上一个位置 " + vehicle2.last_location)
        # print("vehicle2当前位置 " + vehicle2.cur_location)
        # print("预测结果为: ")
        # print(bs.prediction_result)

    def test_time_system(self):
        time_system = enviroment.Time.get_time_system()
        time_system.run()
        while True:
            with time_lock:
                # 等待时间系统到达下一个离散时间点时发起通知
                if not enviroment.time_finished:
                    # 当系统模拟时间已经结束,不进入等待,并且结束该任务
                    time_lock.wait()
                    print(time_system.now())


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    test = TestAddition()
    # test.test_build_tree()
    test.test_print_path()
    # test.test_BS_prediction()
    # test.test_time_system()
