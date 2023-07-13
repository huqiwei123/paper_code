import Content


class UserPreference:

    def __init__(self):
        self.user_preference_for_theme = [0 for i in Content.content_theme]
        self.probability_distribution_for_theme = [0 for i in Content.content_theme]
        self.user_preference_for_form = [0 for i in Content.content_form]
        self.probability_distribution_for_form = [0 for i in Content.content_form]

    def update_user_preference_for_theme(self, request_content):
        # 更新用户对内容主题的兴趣偏好
        self.user_preference_for_theme = [0.9 * x + y for x, y in zip(self.user_preference_for_theme, request_content.
                                                                      theme_arr)]
        # 将当前兴趣偏好转换为概率分布
        all_sum = 0
        for i in range(0, len(self.user_preference_for_theme)):
            all_sum += self.user_preference_for_theme[i]
        if all_sum == 0:
            return
        else:
            probability_distribution_for_theme = [x / all_sum for x in self.user_preference_for_theme]
        self.probability_distribution_for_theme = probability_distribution_for_theme

    def update_user_preference_for_form(self, request_content):
        # 更新用户对内容格式的兴趣偏好
        self.user_preference_for_form = [0.9 * x + y for x, y in zip(self.user_preference_for_form, request_content.
                                                                     form_arr)]
        # 将当前兴趣偏好转换为概率分布
        all_sum = 0
        for i in range(0, len(self.user_preference_for_form)):
            all_sum += self.user_preference_for_form[i]
        if all_sum == 0:
            return
        else:
            probability_distribution_for_form = [x / all_sum for x in self.user_preference_for_form]
        self.probability_distribution_for_form = probability_distribution_for_form
