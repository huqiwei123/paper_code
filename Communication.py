import threading


# 请求类和响应类

# 请求类
class Request(threading.Thread):
    """
    Methods:
        run: 重写线程的run方法,执行请求,也就是调用响应者对请求的处理方法
    """
    def __init__(self, content_no, request, response):
        super().__init__()
        # 请求的内容号
        self.content_no = content_no
        # 请求的对象
        self.request = request
        # 响应的对象
        self.response = response

    def run(self):
        # 发起请求,调用响应者对请求的处理方法
        self.response.request_process(self.request)


# 响应类
class Response(threading.Thread):
    """
    Methods:
        run: 重写线程的run方法,执行响应,也就是调用请求者对响应的处理方法
    """
    def __init__(self, content_no, response, request):
        super().__init__()
        # 响应的内容
        self.content_no = content_no
        # 响应的对象
        self.response = response
        # 请求的对象
        self.request = request

    def run(self):
        self.request.response_process()
