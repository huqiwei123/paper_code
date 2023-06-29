import threading


# 请求类和响应类

# 请求类
# class Request:
#     """
#     Methods:
#         run: 重写线程的run方法,执行请求,也就是调用响应者对请求的处理方法
#     """
#
#     def __init__(self, request):
#         # 请求的内容号
#         self.content_no = request.request_content
#         # 请求的对象
#         self.request = request
#         # 请求次数
#         self.request_num = 1
#         # 请求是否命中的状态
#         self.response_status = False
#
#     def run(self):
#         # 发起请求,找到请求者要请求的响应对象
#         response_vehicle = self.request.select_response_vehicle()
#         # 调用请求类中的Request中的request方法
#         response_result = response_vehicle.find_content(self.content_no)
#         self.response_status = response_result
#         while not self.response_status and self.request_num < 10:
#             # 调用请求车辆的方法,找到下一个需要响应的车辆,向该车辆去请求
#             response_vehicle = response_vehicle.select_response_vehicle()
#             # 对请求的处理结果
#             response_result = response_vehicle.find_content(self.content_no)
#             self.request_num += 1
#             self.response_status = response_result
#         self.request.response_status_list.append(self.response_status)

# 响应类
# class Response(threading.Thread):
#     """
#     Methods:
#         run: 重写线程的run方法,执行响应,也就是调用请求者对响应的处理方法
#     """
#     def __init__(self, content_no, response, request):
#         super().__init__()
#         # 响应的内容
#         self.content_no = content_no
#         # 响应的对象
#         self.response = response
#         # 请求的对象
#         self.request = request
#
#     def run(self):
#         self.request.response_process()
