from PIL import Image
import io
import os


class ImageUtils:
    """图片处理工具类"""

    @staticmethod
    def allowed_file(filename, allowed_extensions):
        """检查文件扩展名是否允许"""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in allowed_extensions

    @staticmethod
    def get_file_extension(filename):
        """获取文件扩展名"""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    @staticmethod
    def save_image_with_quality(image, filepath, quality=100):
        """保存图片并保持高质量"""
        # 根据原始格式保存
        ext = os.path.splitext(filepath)[1].lower()

        save_params = {'quality': quality, 'optimize': True}

        if ext in ['.jpg', '.jpeg']:
            image = image.convert('RGB')  # JPEG不支持透明度
            image.save(filepath, 'JPEG', **save_params)
        elif ext == '.png':
            image.save(filepath, 'PNG', optimize=True)
        elif ext == '.webp':
            image.save(filepath, 'WEBP', quality=quality)
        else:
            image.save(filepath, quality=quality)

    @staticmethod
    def calculate_crop_size(width, height, strategy_config):
        """根据策略计算裁剪尺寸"""
        rows = strategy_config.get('rows', 3)
        cols = strategy_config.get('cols', 3)

        # 计算每个小块的尺寸（取较小的一边，保持正方形）
        crop_size = min(width // cols, height // rows)

        return crop_size