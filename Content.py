import random

# 定义系统中所有缓存的内容

content_theme = ["金融", "科技", "教育", "体育", "娱乐", "交通", "政治", "军事", "国际", "历史", "地理"]
content_form = ["文本", "视频", "音频", "图片"]
# 存储内容集
content_list = []


class Content:
    """
    内容类
    Attributes:
        content_no: 内容的内容号,唯一标识符
        size: 内容的大小
        theme: 内容所属于的主题
        self.form: 内容所属的格式
        theme_arr: 内容所属主题的向量表示
        form_arr: 内容所属格式的向量表示
    """
    content_no = 1

    def __init__(self):
        # 内容唯一识别号
        self.content_no = Content.content_no
        Content.content_no += 1
        # 内容名称
        # self.content_name = name
        # todo: 内容大小
        self.size = 20
        # 内容主题类型,内容主题暂时在内容生成的时候随机给定
        self.theme = random.choice(content_theme)
        # 内容格式,内容格式暂时在内容生成的时候随机给定
        self.form = random.choice(content_form)
        self.theme_arr = Content.theme2arr(self.theme)
        self.form_arr = Content.form2arr(self.form)

    # 将内容主题转变为相应的数组表示
    @staticmethod
    def theme2arr(theme):
        """
        将内容的主题转变为向量表示
        Args:
            theme: 内容所属的主题

        Returns:
            主题的向量表示

        """
        theme_arr = []
        for each in content_theme:
            if theme == each:
                theme_arr.append(1)
            else:
                theme_arr.append(0)
        return theme_arr

    # 将内容格式转变为相应的数组表示
    @staticmethod
    def form2arr(form):
        """
        将内容的格式转变为向量表示
        Args:
            form: 内容所属的格式

        Returns:
            格式的向量表示
        """
        form_arr = []
        for each in content_form:
            if form == each:
                form_arr.append(1)
            else:
                form_arr.append(0)
        return form_arr
