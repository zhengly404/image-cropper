from abc import ABC, abstractmethod


class BaseCropStrategy(ABC):
    """裁剪策略基类"""

    def __init__(self, config):
        """
        初始化策略
        :param config: 策略配置字典
        """
        self.config = config
        self.name = config.get('name', '未命名策略')
        self.description = config.get('description', '')

    @abstractmethod
    def crop(self, image_path, output_dir, **kwargs):
        """
        执行裁剪操作
        :param image_path: 原始图片路径
        :param output_dir: 输出目录
        :param kwargs: 额外参数
        :return: 裁剪后的图片路径列表
        """
        pass

    @abstractmethod
    def get_preview_info(self, image_path):
        """
        获取预览信息
        :param image_path: 图片路径
        :return: 预览信息字典
        """
        pass