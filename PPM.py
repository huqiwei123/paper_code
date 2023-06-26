import numpy as np
import Vehicle
import BS


# 根据车辆历史路径序列构建三层树结构


# 定义树节点
class TreeNode:
    """
    树节点的结构定义
    """

    def __init__(self, value, children=None):
        # 存储位置和统计值 使用np.zeros生产一个长度为2的数组，初始由0填充
        self.value = np.array([value, 1], dtype=object)
        self.value[0] = value
        self.value[1] = 1
        self.children = children if children is not None else []

    def add_child(self, child):
        self.children.append(child)


# 根据车辆历史路径序列构建三层树结构
class BuildTree:
    """
    构建二叉树

    Attributes:
        root: tree root node

    Methods:
        addTree(arr): 将3个连续的路径序列arr加入到路径树中
        createTree(path): 将整个路径序列path构建成一个树结构
    """

    def __init__(self):
        self.root = TreeNode(0)

    # 将3个连续的路径序列arr加入到路径树中
    def addTree(self, arr):
        """
        将3个连续的路径序列arr加入到路径树中
        Args:
            arr (list): 3个连续的路径序列arr

        Returns: None

        """

        curr_node = self.root
        for i in range(len(arr)):
            value = arr[i]
            found_child = False
            # 查找是否已有子节点的值等于当前值
            for child in curr_node.children:
                if child.value[0] == value:
                    child.value[1] += 1
                    curr_node = child
                    found_child = True
                    break
            # 如果不存在，则将当前值作为子节点添加到当前节点
            if not found_child:
                new_node = TreeNode(value)
                curr_node.add_child(new_node)
                curr_node = new_node

    # 将整个路径序列path构建成一个树结构
    def createTree(self, path):
        """
        将整个路径序列path构建成一个树结构
        Args:
            path (list): 路径序列

        Returns: None

        """
        arr = group_element(path)
        for i in range(len(arr)):
            self.addTree(arr[i])


# 预测器,根据当前位置和下一个位置和车辆对应的树结构,预测车辆未来的下一个位置
class Predictor:
    """
    预测器,根据当前位置和下一个位置和车辆对应的树结构,预测车辆未来的下一个位置

    Methods:
        predictor: 根据车辆上一个位置和当前位置预测出车辆的下一个位置
    """

    @staticmethod
    def predictor(vehicle: 'Vehicle'):
        """
        根据车辆上一个位置和当前位置预测出车辆的下一个位置
        Args:
            vehicle (object): 车辆对象

        Returns: 车辆的下一个位置

        """
        bs = BS.BS.get_bs()

        # 如果车辆在BS中注册了才进行预测
        if vehicle not in bs.vehicle_list:
            return "Unregistered vehicle"
            # 获取BS中车辆对应的树结构

        bs_tree = bs.vehicle_tree[vehicle.vehicle_no]

        # 如果车辆的上一个位置不为空,则对车辆的下一个位置进行预测
        if vehicle.last_location is None:
            return "last location is None"

        for last in bs_tree.root.children:
            if last.value[0] == vehicle.last_location:
                for cur in last.children:
                    if cur.value[0] == vehicle.cur_location:
                        helper = {}
                        for next_ in cur.children:
                            helper[next_.value[1]] = next_.value[0]
                        max_key = max(helper.keys())
                        return helper[max_key]
                return "current location is not find in tree"
        return "last location is not find in tree"


# 分簇(分类器),根据每辆车的预测结果,将当前位置和下一位置相同的车辆划分为同一个簇中
class Classifier:
    """
    分簇(分类器),根据每辆车的预测结果,将当前位置和下一位置相同的车辆划分为同一个簇中

    Methods:
        classifier: 根据所有车辆当前位置和下一位置,如果相同,则将车辆划分到同一个簇中
    """

    @staticmethod
    def classifier():
        """
        预测每辆车辆的位置后,将当前位置和下一个位置相同的车辆划分为一个簇
        Returns:
            dict:
                车辆的分类结果集合
        """
        bs = BS.BS.get_bs()

        vehicle_curlocation = bs.vehicle_curlocation
        prediction_result = bs.prediction_result

        classify_result = {}
        for each in bs.vehicle_list:
            key = (vehicle_curlocation[each.vehicle_no], prediction_result[each.vehicle_no])
            if key in classify_result:
                classify_result[key].append(each)
            else:
                classify_result[key] = []
                classify_result[key].append(each)
        return classify_result


# 读取路径序列，返回所有连续3个路径所构成的二维数组
def group_element(my_list):
    """
    读取路径序列，返回所有连续3个路径所构成的二维数组
    Args:
        my_list (list): 路径序列

    Returns:
        list[list]:
            所有连续3个路径序列构成的二维数组result

    """
    result = []

    for i in range(len(my_list) - 2):
        sub_list = my_list[i:i + 3]
        result.append(sub_list)
    return result


# Test: print tree pattern
def print_tree_pattern(node, level=0):
    """
    Test: print tree pattern
    Args:
        node (TreeNode): tree root node
        level (int): tree current depth

    Returns:
        String:
            tree pattern

    """
    indentation = "    " * level
    print(f"{indentation}└── {node.value[0]} ({node.value[1]})")

    children_count = len(node.children)
    for i, child in enumerate(node.children):
        if i == children_count - 1:
            print_tree_pattern(child, level + 1)
        else:
            print_tree_pattern(child, level + 1)
            print(f"{indentation}    │")
