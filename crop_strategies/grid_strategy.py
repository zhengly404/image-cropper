from PIL import Image
import os
from .base_strategy import BaseCropStrategy
from utils.image_utils import ImageUtils


class GridStrategy(BaseCropStrategy):
    """网格裁剪策略 - 将图片裁剪成网格状"""

    def get_preview_info(self, image_path):
        """获取预览信息"""
        with Image.open(image_path) as img:
            width, height = img.size
            rows = self.config.get('rows', 3)
            cols = self.config.get('cols', 3)
            crop_size = min(width // cols, height // rows)

            return {
                'original_width': width,
                'original_height': height,
                'crop_size': crop_size,
                'rows': rows,
                'cols': cols,
                'total_pieces': rows * cols,
                'strategy_name': self.name
            }

    def crop(self, image_path, output_dir, keep_original_quality=True):
        """
        执行网格裁剪
        :param image_path: 原始图片路径
        :param output_dir: 输出目录
        :param keep_original_quality: 是否保持原始画质
        :return: 裁剪后的图片路径列表
        """
        # 获取原始文件信息
        original_ext = ImageUtils.get_file_extension(image_path)
        base_name = os.path.splitext(os.path.basename(image_path))[0]

        # 打开图片
        with Image.open(image_path) as img:
            # 转换为RGB如果是RGBA模式（处理PNG透明通道）
            if img.mode == 'RGBA':
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # 使用alpha通道作为mask
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            width, height = img.size
            rows = self.config.get('rows', 3)
            cols = self.config.get('cols', 3)

            # 计算裁剪尺寸
            crop_size = min(width // cols, height // rows)

            # 计算起始位置（居中对齐）
            start_x = (width - crop_size * cols) // 2
            start_y = (height - crop_size * rows) // 2

            cropped_paths = []

            # 执行裁剪
            for row in range(rows):
                for col in range(cols):
                    # 计算裁剪区域
                    left = start_x + col * crop_size
                    top = start_y + row * crop_size
                    right = left + crop_size
                    bottom = top + crop_size

                    # 裁剪图片
                    cropped = img.crop((left, top, right, bottom))

                    # 生成输出文件名
                    output_filename = f"{base_name}_{row + 1}x{col + 1}.{original_ext}"
                    output_path = os.path.join(output_dir, output_filename)

                    # 保存裁剪后的图片（保持高质量）
                    if keep_original_quality:
                        ImageUtils.save_image_with_quality(cropped, output_path, quality=100)
                    else:
                        cropped.save(output_path)

                    cropped_paths.append(output_filename)

        return cropped_paths