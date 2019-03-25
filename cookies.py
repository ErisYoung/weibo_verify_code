import time
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from os import listdir
from os.path import abspath, dirname
from chaojiying import Chaojiying

CHAOJIYING_USERNAME = "jerry123456"
CHAOJIYING_PASSWORD = "zxc123456"
CHAOJIYING_SOFT_ID = 898874
CHAOJIYING_KIND_SLIVER = 9101
CHAOJIYING_KIND_CLICK = 9004

TEMPLATES_FOLDER = dirname(abspath(__file__)) + '/templates/'
BORDER = 55

class WeiboCookies():
    def __init__(self, username, password, browser):
        self.url = 'https://passport.weibo.cn/signin/login?entry=mweibo&r=https://m.weibo.cn/'
        self.browser = browser
        self.wait = WebDriverWait(self.browser, 20)
        self.username = username
        self.password = password
        self.chaojiying = Chaojiying(CHAOJIYING_USERNAME, CHAOJIYING_PASSWORD, CHAOJIYING_SOFT_ID)
        self.scale = 1.25
        self.kind = CHAOJIYING_KIND_CLICK
        self.font = ImageFont.truetype("msyh.ttc", 28)
        self.sliver_text = "请点击阴影凹槽左上角"
    
    def open(self):
        """
        打开网页输入用户名密码并点击
        :return: None
        """
        self.browser.delete_all_cookies()
        self.browser.get(self.url)
        username = self.wait.until(EC.presence_of_element_located((By.ID, 'loginName')))
        password = self.wait.until(EC.presence_of_element_located((By.ID, 'loginPassword')))
        submit = self.wait.until(EC.element_to_be_clickable((By.ID, 'loginAction')))
        username.send_keys(self.username)
        password.send_keys(self.password)
        time.sleep(1)
        submit.click()
    
    def password_error(self):
        """
        判断是否密码错误
        :return:
        """
        try:
            return WebDriverWait(self.browser, 5).until(
                EC.text_to_be_present_in_element((By.ID, 'errorMsg'), '用户名或密码错误'))
        except TimeoutException:
            return False
    
    def login_successfully(self):
        """
        判断是否登录成功
        :return:
        """
        try:
            print("enter")
            return bool(
                WebDriverWait(self.browser, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'lite-iconf-profile'))))
        except TimeoutException:
            return False

    def redirect_geetcode(self):
        try:
            geetCode_command=WebDriverWait(self.browser,7).until(EC.element_to_be_clickable((By.CLASS_NAME,'geetest_radar_tip')))
            geetCode_command.click()
            return True
        except TimeoutException:
            print("没有出现极验验证码")
            return False

    def get_geetCode_image(self, name="captcha.png"):
        """
        得到验证码图片
        :param name:
        :return:
        """
        top, bottom, left, right = map(lambda x: x * self.scale, self.get_geetCode_postion())
        screen = self.get_screenshot()
        image = screen.crop((left, top, right, bottom))
        if self.kind == CHAOJIYING_KIND_SLIVER:
            draw = ImageDraw.Draw(image)
            draw.text((10, 160), self.sliver_text, font=self.font, fill=(230, 0, 0))

        image.save(name)
        return image

    def get_geetCode_postion(self):
        """
        获得图片的相对位置
        :return:
        """
        element = self.get_geetCode()
        time.sleep(2)
        location = element.location
        size = element.size
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size[
            'width']

        return top, bottom, left, right

    def get_geetCode(self):
        """
        :return:
        """
        try:
            element_code=None
            elements = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@class='geetest_fullpage_click_box']/descendant::div[contains(@class,'geetest_slider')]")))
            self.kind = (len(elements) ==0 and CHAOJIYING_KIND_CLICK or CHAOJIYING_KIND_SLIVER)

            if self.kind == CHAOJIYING_KIND_SLIVER:
                element_code = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='geetest_window']")))
                print("当前为滑动验证码")
            elif self.kind == CHAOJIYING_KIND_CLICK:
                element_code = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='geetest_fullpage_click_box']")))
                print("当前为点击验证码")

            # // div[ @class ='geetest_fullpage_click_box'] / div / div / div

            return element_code

        except TimeoutException:
            print("无法得到验证码图片box")

    def get_points(self, result):
        """
        得到解析的json文件，解析需要点击的位置
        :param result:
        :return:
        """
        print(self.kind)
        if self.kind == CHAOJIYING_KIND_CLICK:
            groups = result.get('pic_str').split('|')
            locations = [[int(number) for number in group.split(",")] for group in groups]

            return locations

        elif self.kind == CHAOJIYING_KIND_SLIVER:
            locations = [int(i) for i in result.get('pic_str').split(",")]
            return locations

    def click_command(self):
        if self.is_check():
            ele = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@class='ivu-btn ivu-btn-primary-arrow']")))
            ele.click()

    def print_point(self, image, locations, kind):
        draw = ImageDraw.Draw(image)
        if kind == CHAOJIYING_KIND_SLIVER:
            print(locations)
            draw.ellipse((locations[0]-10, locations[1]-10, locations[0]+10, locations[1]+10), fill=(230, 0, 0))
        elif kind == CHAOJIYING_KIND_CLICK:
            for i in locations:
                draw.ellipse((i[0]-10, i[1]-10, i[0]+10, i[1]+10), fill=(230, 0, 0))

        image.save("new_pic.png")

    def touch_click_words(self, locations):
        """
        模拟点击
        :param locations:
        :return:
        """
        for location in locations:
            print(location)
            ActionChains(self.browser).move_to_element_with_offset(self.get_touclick(), location[0],
                                                                   location[1]).click().perform()
            time.sleep(1)

    def click_tou_commit(self):
        """
        点击确认
        :return:
        """
        ele = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@class='geetest_commit']")))
        ele.click()
        time.sleep(2)

    def get_track(self, gap):
        track = []

        v = 0
        t = 0.2
        middle = gap * 4 / 5
        current = 0
        while current < gap:
            if current < middle:
                a = 2
            else:
                a = -5
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))
            # print("current:",current)

        return track

    def get_slider(self):
        slider = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='geetest_slider_button']")))
        return slider

    def move_to_slider(self, slider, track):
        ActionChains(self.browser).click_and_hold(slider).perform()

        for i in track:
            ActionChains(self.browser).move_by_offset(xoffset=i, yoffset=0).perform()

        ActionChains(self.browser).release().perform()

        time.sleep(2)


    def crack_geetCode(self):
        image = self.get_geetCode_image()
        # self.print_point(image, [207,154], CHAOJIYING_KIND_SLIVER)
        bytes_array = BytesIO()
        image.save(bytes_array, format='PNG')

        result = self.chaojiying.post_pic(bytes_array.getvalue(), self.kind)
        print(result)

        locations = self.get_points(result)
        if self.kind == CHAOJIYING_KIND_CLICK:
            self.print_point(image, locations, CHAOJIYING_KIND_CLICK)
            self.touch_click_words(locations)
            self.click_tou_commit()

        elif self.kind == CHAOJIYING_KIND_SLIVER:
            self.print_point(image, locations, CHAOJIYING_KIND_SLIVER)
            gap = locations[0] - BORDER
            track = self.get_track(gap)
            slider = self.get_slider()
            self.move_to_slider(slider, track)

        self.click_command()

    def get_position(self):
        """
        获取验证码位置
        :return: 验证码位置元组
        """
        try:
            img = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'patt-shadow')))
        except TimeoutException:
            print('未出现验证码')
            self.open()
        time.sleep(2)
        location = img.location
        size = img.size
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size[
            'width']
        return (top, bottom, left, right)


    def get_screenshot(self):
        """
        获取网页截图
        :return: 截图对象
        """
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))
        return screenshot
    
    def get_image(self, name='captcha.png'):
        """
        获取验证码图片
        :return: 图片对象
        """
        top, bottom, left, right = self.get_position()
        print('验证码位置', top, bottom, left, right)
        screenshot = self.get_screenshot()
        captcha = screenshot.crop((left, top, right, bottom))
        return captcha
    
    def is_pixel_equal(self, image1, image2, x, y):
        """
        判断两个像素是否相同
        :param image1: 图片1
        :param image2: 图片2
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        # 取两个图片的像素点
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]
        threshold = 20
        if abs(pixel1[0] - pixel2[0]) < threshold and abs(pixel1[1] - pixel2[1]) < threshold and abs(
                pixel1[2] - pixel2[2]) < threshold:
            return True
        else:
            return False
    
    def same_image(self, image, template):
        """
        识别相似验证码
        :param image: 待识别验证码
        :param template: 模板
        :return:
        """
        # 相似度阈值
        threshold = 0.99
        count = 0
        for x in range(image.width):
            for y in range(image.height):
                # 判断像素是否相同
                if self.is_pixel_equal(image, template, x, y):
                    count += 1
        result = float(count) / (image.width * image.height)
        if result > threshold:
            print('成功匹配')
            return True
        return False
    
    def detect_image(self, image):
        """
        匹配图片
        :param image: 图片
        :return: 拖动顺序
        """
        for template_name in listdir(TEMPLATES_FOLDER):
            print('正在匹配', template_name)
            template = Image.open(TEMPLATES_FOLDER + template_name)
            if self.same_image(image, template):
                # 返回顺序
                numbers = [int(number) for number in list(template_name.split('.')[0])]
                print('拖动顺序', numbers)
                return numbers
    
    def move(self, numbers):
        """
        根据顺序拖动
        :param numbers:
        :return:
        """
        # 获得四个按点
        try:
            circles = self.browser.find_elements_by_css_selector('.patt-wrap .patt-circ')
            dx = dy = 0
            for index in range(4):
                circle = circles[numbers[index] - 1]
                # 如果是第一次循环
                if index == 0:
                    # 点击第一个按点
                    ActionChains(self.browser) \
                        .move_to_element_with_offset(circle, circle.size['width'] / 2, circle.size['height'] / 2) \
                        .click_and_hold().perform()
                else:
                    # 小幅移动次数
                    times = 30
                    # 拖动
                    for i in range(times):
                        ActionChains(self.browser).move_by_offset(dx / times, dy / times).perform()
                        time.sleep(1 / times)
                # 如果是最后一次循环
                if index == 3:
                    # 松开鼠标
                    ActionChains(self.browser).release().perform()
                else:
                    # 计算下一次偏移
                    dx = circles[numbers[index + 1] - 1].location['x'] - circle.location['x']
                    dy = circles[numbers[index + 1] - 1].location['y'] - circle.location['y']
        except:
            return False
    
    def get_cookies(self):
        """
        获取Cookies
        :return:
        """
        return self.browser.get_cookies()

    def crack_sudoku_code(self):
        """
        破解九宫格验证码
        :return:
        """
        image = self.get_image('captcha.png')
        numbers = self.detect_image(image)
        self.move(numbers)

    def success_return(self):
        if self.login_successfully():
            cookies = self.get_cookies()
            return {
                'status': 1,
                'content': cookies
            }
    def password_error_return(self):
        if self.password_error():
            return {
                'status': 2,
                'content': '用户名或密码错误'
            }

    def main(self):
        """
        破解入口
        :return:
        """
        self.open()
        self.password_error_return()
        # 如果不需要验证码直接登录成功
        self.success_return()

        if not self.redirect_geetcode():
            #如果为九宫格验证码
            self.crack_sudoku_code()
        else:
            print("1")
            #如果为极验验证码，
            if not self.success_return():
                # 如果点击极验未成功验证
                print("2")
                self.crack_geetCode()

        if not self.success_return():
            print("3")
            return {
                'status': 3,
                'content': '登录失败'
            }


if __name__ == '__main__':
    browser=webdriver.Chrome()
    result = WeiboCookies('18669143725', 'zew3v90snz',browser).main()
    print(result)
