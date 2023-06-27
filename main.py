import BS
import PPM
import enviroment

"""
usage: test
"""

time_lock = enviroment.time_lock
bs_lock = BS.bs_lock


class TestAddition:
    """
        Methods:
            test_build_tree: 测试利用路径序列构建路径树
            test_print_path: 测试打印路径序列
            test_BS_prediction: 测试bs实例中根据所有车辆的路径树/上一个位置/当前位置预测车辆的下一个位置
            test_time_system: 测试时间系统
            test_BS_classify: 测试车辆分簇方法
            test_judge_area: 测试离散坐标转实际坐标方法
    """

    # 测试利用路径序列构建路径树
    def test_build_tree(self):
        alist = ["l1", "l2", "l3", "l4", "l2", "l3", "l2", "l3"]
        tree = PPM.BuildTree()
        tree.createTree(alist)
        PPM.print_tree_pattern(tree.root)

    # 测试打印路径序列
    def test_print_path(self):
        # 初始化整个系统
        enviroment.System(1)
        bs = enviroment.System.bs
        vehicle1 = enviroment.System.vehicle_list[0]
        while True:
            with bs_lock:
                if not enviroment.time_finished:
                    # 等待时间系统到达下一个离散时间点时发起通知
                    bs_lock.wait()
                    print(bs.vehicle_path[vehicle1.vehicle_no])

    # 2个车辆实例,利用600s构建树,然后再根据上一个位置和当前位置去预测车辆的下一个位置
    def test_BS_prediction(self):
        enviroment.System(300)
        bs = enviroment.System.bs
        vehicle_list = enviroment.System.vehicle_list
        time_system = enviroment.System.time_system
        # 利用离散时间点的前面10s构建树
        while time_system.now() < 10:
            with bs_lock:
                # 在BS线程更新完数据后再去读取
                bs_lock.wait()
        for vehicle in vehicle_list:
            print("车辆号为 " + str(vehicle.vehicle_no))
            print("当前路径:", end=" ")
            print(bs.vehicle_path[vehicle.vehicle_no])
            print("当前树结构:")
            PPM.print_tree_pattern(bs.vehicle_tree[vehicle.vehicle_no].root)
            print("上一个位置: " + vehicle.last_location)
            print("当前位置: " + vehicle.cur_location)
            print("预测到的下一个位置: " + bs.prediction_result[vehicle.vehicle_no])
            print("============================================================")

    # 测试时间系统
    def test_time_system(self):
        enviroment.System(2)
        time_system = enviroment.System.time_system
        while True:
            with time_lock:
                # 等待时间系统到达下一个离散时间点时发起通知
                if not enviroment.time_finished:
                    # 当系统模拟时间已经结束,不进入等待,并且结束该任务
                    time_lock.wait()
                    print(time_system.now())

    # 测试车辆分簇方法
    def test_BS_classify(self):
        enviroment.System(300)
        time_system = enviroment.System.time_system
        bs = enviroment.System.bs
        while time_system.now() < 10:
            pass
        print("分簇结果为:")
        test_result = {}
        # 测试中,将值列表中的对象以车辆号代替
        for key in bs.classification_result.keys():
            test_result[key] = []
            for vehicle in bs.classification_result[key]:
                test_result[key].append(vehicle.vehicle_no)
        for key in test_result:
            print(key, end=" ")
            print(":", end=" ")
            print(test_result[key])

    # 测试离散坐标转实际坐标方法
    def test_judge_area(self):
        # 初始化并运行环境,环境中有100辆车
        enviroment.System(100)
        # 获得环境中的各个实例
        time_system = enviroment.System.time_system
        bs = enviroment.System.bs
        vehicle_list = enviroment.System.vehicle_list
        while True:
            with bs_lock:
                bs_lock.wait()
                print("当前时刻", end=" ")
                print(time_system.now(), end=" ")
                print("所在的离散位置为:", end=" ")
                print(vehicle_list[0].cur_location, end=" ")
                print(",所在的x轴坐标为:", end=" ")
                print(vehicle_list[0].x, end=" ")
                print(",所在的y轴坐标为:", end=" ")
                print(vehicle_list[0].y)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    test = TestAddition()
    # test.test_build_tree()
    # test.test_print_path()
    # test.test_BS_prediction()
    # test.test_time_system()
    # test.test_BS_classify()
    test.test_judge_area()
