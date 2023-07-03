
class ActivityLevel:
    """
    计算近期车辆在其簇内的活跃度
    """

    # 时间窗口大小,考虑最近8个时间点的请求量
    time_windows = 8

    # 计算活跃度的折现因子
    factor = [0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16]

    # 计算车辆vehicle在簇内的活跃度
    @staticmethod
    def cal_activity_value(vehicle):
        if len(vehicle.request_status_history) < 8:
            pass
            # todo: raise Exception("请求数历史记录不足")
        last_eight_list = vehicle.request_status_history[-8:]
        result_list = []
        for num1, num2 in zip(last_eight_list, ActivityLevel.factor):
            result_list.append(num1 * num2)
        activity_value = 0
        for num in result_list:
            activity_value += num
        return activity_value

    @staticmethod
    def cal_activity_level(vehicle):
        owner_activity_value = ActivityLevel.cal_activity_value(vehicle)
        other_activity_value_within_cluster = []
        for vehicle in vehicle.other_vehicle_within_cluster:
            other_activity_value_within_cluster.append(ActivityLevel.cal_activity_value(vehicle))
        other_activity_value_sum = 0
        for num in other_activity_value_within_cluster:
            other_activity_value_sum += num
        if owner_activity_value == 0:
            return 0
        elif owner_activity_value + other_activity_value_sum == 0:
            return 0
        else:
            return owner_activity_value / (owner_activity_value + other_activity_value_sum)
