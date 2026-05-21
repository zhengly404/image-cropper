import os


class Config:
    """应用配置"""
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 最大上传限制
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

    # 裁剪策略配置
    # 在原有配置基础上添加
    CROP_STRATEGIES = {
        'grid_3x3': {
            'name': '3x3网格裁剪',
            'description': '将图片裁剪成9个相同大小的正方形',
            'rows': 3,
            'cols': 3,
            'module': 'grid_strategy.GridStrategy'
        },
        'grid_3x2': {
            'name': '3x2网格裁剪',
            'description': '将图片裁剪成6个相同大小的正方形',
            'rows': 3,
            'cols': 2,
            'module': 'grid_strategy.GridStrategy'
        },
        'grid_2x3': {
            'name': '2x3网格裁剪',
            'description': '将图片裁剪成6个相同大小的正方形',
            'rows': 2,
            'cols': 3,
            'module': 'grid_strategy.GridStrategy'
        },
        'grid_4x4': {
            'name': '4x4网格裁剪',
            'description': '将图片裁剪成16个相同大小的正方形',
            'rows': 4,
            'cols': 4,
            'module': 'grid_strategy.GridStrategy'
        },
        'grid_5x5': {
            'name': '5x5网格裁剪',
            'description': '将图片裁剪成25个相同大小的正方形',
            'rows': 5,
            'cols': 5,
            'module': 'grid_strategy.GridStrategy'
        },
        'custom': {
            'name': '自定义裁剪',
            'description': '手动拖动裁剪框进行自定义裁剪',
            'rows': 1,
            'cols': 1,
            'module': 'custom_strategy.CustomCropStrategy'
        }
    }

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)