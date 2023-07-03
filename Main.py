import BS
import PPM
import Enviroment
import Vehicle
import unittest

"""
usage: test
"""

time_lock = Enviroment.time_lock
bs_lock = BS.bs_lock
vehicle_lock = Vehicle.vehicle_lock


class TestAddition(unittest.TestCase):
    """
        Methods:
            1.test_build_tree: 测试利用路径序列构建路径树
            2.test_print_path: 测试打印路径序列
            3.test_BS_prediction: 测试bs实例中根据所有车辆的路径树/上一个位置/当前位置预测车辆的下一个位置
            4.test_time_system: 测试时间系统
            5.test_BS_classify: 测试车辆分簇方法
            6.test_judge_area: 测试离散坐标转实际坐标方法
            7.test_content_list: 测试内容集的生成并获取内容的主题和形式
            8.test_vehicle_communication: 测试车辆间请求内容和响应内容的通信
            9.test_vehicle_within_area: 测试车辆获取其通信范围内所有车辆的list
            10.test_inform_classify_result: 测试每辆车获得簇内其他车辆的集合
    """

    # 初始化测试环境
    def setUp(self) -> None:
        pass

    # 清理测试环境的代码
    def tearDown(self) -> None:
        pass

    # 1.测试利用路径序列构建路径树
    def test_build_tree(self):
        alist = ["l1", "l2", "l3", "l4", "l2", "l3", "l2", "l3"]
        tree = PPM.BuildTree()
        tree.createTree(alist)
        PPM.print_tree_pattern(tree.root)

    # 2.测试打印路径序列
    def test_print_path(self):
        # 初始化整个系统
        Enviroment.System().run()
        bs = Enviroment.System.bs
        vehicle1 = Enviroment.System.vehicle_list[0]
        while True:
            with vehicle_lock:
                if not Enviroment.time_finished:
                    # 等待时间系统到达下一个离散时间点时发起通知
                    vehicle_lock.wait()
                    if Enviroment.Time.counter % 4 == 0:
                        print(bs.vehicle_path[vehicle1.vehicle_no])

    # 3.2个车辆实例,利用600s构建树,然后再根据上一个位置和当前位置去预测车辆的下一个位置
    def test_BS_prediction(self):
        Enviroment.System(300).run()
        bs = Enviroment.System.bs
        vehicle_list = Enviroment.System.vehicle_list
        time_system = Enviroment.System.time_system
        # 利用离散时间点的前面10s构建树
        while time_system.now() < 30:
            with vehicle_lock:
                # 在BS线程更新完数据后再去读取
                vehicle_lock.wait()
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

    # 4.测试时间系统
    def test_time_system(self):
        Enviroment.System().run()
        time_system = Enviroment.System.time_system
        while True:
            with vehicle_lock:
                # 等待时间系统到达下一个离散时间点时发起通知
                if not Enviroment.time_finished:
                    # 当系统模拟时间已经结束,不进入等待,并且结束该任务
                    vehicle_lock.wait()
                    print(time_system.now())

    # 5.测试车辆分簇方法
    def test_BS_classify(self):
        Enviroment.System(10).run()
        time_system = Enviroment.System.time_system
        bs = Enviroment.System.bs
        while time_system.now() < 1800:
            with vehicle_lock:
                vehicle_lock.wait()
                print(time_system.now())
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

    # 6.测试离散坐标转实际坐标方法
    def test_judge_area(self):
        # 初始化并运行环境,环境中有100辆车
        Enviroment.System(100).run()
        # 获得环境中的各个实例
        time_system = Enviroment.System.time_system
        vehicle_list = Enviroment.System.vehicle_list
        while True:
            with vehicle_lock:
                vehicle_lock.wait()
                if Enviroment.Time.counter % 4 == 0:
                    print("当前时刻", end=" ")
                    print(time_system.now(), end=" ")
                    print("所在的离散位置为:", end=" ")
                    print(vehicle_list[0].cur_location, end=" ")
                    print(",所在的x轴坐标为:", end=" ")
                    print(vehicle_list[0].x, end=" ")
                    print(",所在的y轴坐标为:", end=" ")
                    print(vehicle_list[0].y)

    # 7.测试内容集的生成并获取内容的主题和形式
    def test_content_list(self):
        Enviroment.System().run()
        content_list = Enviroment.System.content_list
        for content in content_list:
            print("内容号为:", end=" ")
            print(content.content_no, end=" ")
            print("的内容主题为:", end=" ")
            print(content.theme, end=" ")
            print(",对应的向量表示为:", end=" ")
            print(content.theme_arr, end=" ")
            print(",内容的格式为:", end=" ")
            print(content.form, end=" ")
            print(",对应的向量表示为:", end=" ")
            print(content.form_arr)

    # 8.测试车辆间请求内容和响应内容的通信
    def test_vehicle_communication(self):
        Enviroment.System(500).run()
        time_system = Enviroment.System.time_system
        vehicle1 = Enviroment.System.vehicle_list[0]
        vehicle2 = Enviroment.System.vehicle_list[1]
        vehicle3 = Enviroment.System.vehicle_list[2]
        # 车辆1向车辆2发起内容请求
        # 车辆2缓存有内容1
        vehicle2.cache_status = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        # 车辆1没有缓存内容1,车辆1向车辆2请求内容1
        vehicle1.cache_status = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        vehicle3.cache_status = [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        vehicle1.request_content = 2
        while time_system.now() < 60:
            with vehicle_lock:
                vehicle_lock.wait()
                new_list = []
                for vehicle in vehicle1.other_vehicle_within_cluster:
                    new_list.append(vehicle.vehicle_no)
                alist = []
                for vehicle in vehicle1.vehicle_within_area:
                    alist.append(vehicle.vehicle_no)
                print(
                    f"在时刻{time_system.now()}时,{vehicle1.vehicle_no}号车辆当前是否发起请求:{vehicle1.request_status},此时刻的所有响应状态列表为:"
                    f"{vehicle1.response_status_list}")
                if Enviroment.Time.counter % 4 == 0:
                    print(
                        f"在时刻{time_system.now()}时,{vehicle1.vehicle_no}号车辆自身簇内其他车辆的集合为:{new_list},通信范围内的"
                        f"其他车辆集合为:{alist}")

        # import matplotlib.pyplot as plt
        # plt.plot(vehicle1.response_status_list)
        # plt.show()

    # 9.测试车辆获取其通信范围内所有车辆的list
    def test_vehicle_within_area(self):
        env = Enviroment.System(500)
        vehicle_list = env.vehicle_list
        time_system = env.time_system
        env.run()
        while time_system.now() < 10:
            with vehicle_lock:
                vehicle_lock.wait()
                if Enviroment.Time.counter % 4 == 0:
                    for vehicle in vehicle_list:
                        print(
                            f"在时刻{time_system.now()}下,车辆{vehicle.vehicle_no}的坐标位置为({vehicle.x},{vehicle.y}),当前"
                            f"通信范围内的车辆list为:", end=" ")
                        view_list = []
                        for v in vehicle.vehicle_within_area:
                            view_list.append(v.vehicle_no)
                        print(view_list)

    # 10.bs告知每辆车分类结果
    def test_inform_classify_result(self):
        env = Enviroment.System(100)
        vehicle_list = env.vehicle_list
        time_system = env.time_system
        env.run()
        while time_system.now() < 10:
            with vehicle_lock:
                vehicle_lock.wait()
                if Enviroment.Time.counter % 4 == 0:
                    print(f"在时刻{time_system.now()}时,所有车辆自身簇内其他车辆的集合为:")
                    for vehicle in vehicle_list:
                        new_list = []
                        for v in vehicle.other_vehicle_within_cluster:
                            new_list.append(v.vehicle_no)
                        print(f"第{vehicle.vehicle_no}号车辆簇内其他车辆集合为:{new_list}")

    def test_cal_activityLevel(self):
        env = Enviroment.System(50, 100)
        vehicle_list = env.vehicle_list
        time_system = env.time_system
        env.run()
        while time_system.now() < 30:
            pass
        with vehicle_lock:
            vehicle_lock.wait()
            for vehicle in vehicle_list:
                print(f"{vehicle.vehicle_no}簇内的其他车辆为{vehicle.other_vehicle_within_cluster}")
                print(f"{vehicle.vehicle_no}号车辆的请求历史状态为{vehicle.request_status_history}")
                print(f"{vehicle.vehicle_no}号车辆的活跃度等级为{vehicle.activity_level}")
                print(f"{vehicle.vehicle_no}号车辆请求成功的跳数{vehicle.hop_count}")
            # 总请求量
            all_request = 0
            # 请求成功的数量
            success = 0
            for vehicle in vehicle_list:
                if vehicle.request_status:
                    all_request += 1
                if vehicle.response_status_list[-1] == True:
                    success += 1
            if all_request == 0:
                print("此时没有任何一辆车有请求")
            else:
                print(f"总请求次数{all_request}")
                print(f"总请求成功次数{success}")
                print(f"命中率为{success / all_request}")
            print(env.bs.cache_hit_ration)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    unittest.main()
    # case = 4
    # if case == 1:
    #     test.test_build_tree()
    # elif case == 2:
    #     test.test_print_path()
    # elif case == 3:
    #     test.test_BS_prediction()
    # elif case == 4:
    #     test.test_time_system()
    # elif case == 5:
    #     test.test_BS_classify()
    # elif case == 6:
    #     test.test_judge_area()
    # elif case == 7:
    #     test.test_content_list()
    # elif case == 8:
    #     test.test_vehicle_communication()
    # elif case == 9:
    #     test.test_vehicle_within_area()
    # elif case == 10:
    #     test.test_inform_classify_result()
