from PIL import Image, ImageDraw
import os
import math
from .base_strategy import BaseCropStrategy
from utils.image_utils import ImageUtils


class CustomCropStrategy(BaseCropStrategy):
    """自定义裁剪策略 - 支持形状裁剪"""

    def get_preview_info(self, image_path):
        """获取预览信息"""
        with Image.open(image_path) as img:
            width, height = img.size
            return {
                'width': width,
                'height': height
            }

    def crop(self, image_path, output_dir, crop_data):
        """
        执行自定义裁剪
        :param crop_data: 裁剪数据，支持两种模式：
            1. 矩形裁剪: {'crops': [...], 'rows': n, 'cols': m}
            2. 形状裁剪: {'shapes': [...], 'mode': 'shape'}
        """
        original_ext = ImageUtils.get_file_extension(image_path)
        base_name = os.path.splitext(os.path.basename(image_path))[0]

        with Image.open(image_path) as img:
            # 转换为RGBA以支持透明
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            cropped_paths = []
            mode = crop_data.get('mode', 'rectangle')

            if mode == 'shape':
                # 形状裁剪模式
                shapes = crop_data.get('shapes', [])
                for idx, shape_data in enumerate(shapes):
                    shape_type = shape_data.get('type', 'rectangle')
                    x = shape_data.get('x', 0)
                    y = shape_data.get('y', 0)
                    width = shape_data.get('width', 100)
                    height = shape_data.get('height', 100)
                    points = shape_data.get('points', 5)  # 多角星形角数

                    # 创建遮罩
                    mask = self.create_shape_mask(
                        shape_type,
                        int(width),
                        int(height),
                        points
                    )

                    # 裁剪并应用遮罩
                    cropped = img.crop((int(x), int(y), int(x + width), int(y + height)))
                    cropped = self.apply_mask(cropped, mask)

                    output_filename = f"{base_name}_{shape_type}_{idx + 1}.png"
                    output_path = os.path.join(output_dir, output_filename)
                    ImageUtils.save_image_with_quality(cropped, output_path, quality=100)
                    cropped_paths.append(output_filename)
            else:
                # 原有的矩形裁剪模式
                crops = crop_data.get('crops', [])
                rows = crop_data.get('rows', 1)
                cols = crop_data.get('cols', 1)

                if not crops:
                    grid_data = crop_data.get('grid', {})
                    cell_width = grid_data.get('cell_width', img.width // cols)
                    cell_height = grid_data.get('cell_height', img.height // rows)
                    offset_x = grid_data.get('offset_x', 0)
                    offset_y = grid_data.get('offset_y', 0)

                    for row in range(rows):
                        for col in range(cols):
                            x = offset_x + col * cell_width
                            y = offset_y + row * cell_height
                            crops.append({
                                'x': x,
                                'y': y,
                                'width': cell_width,
                                'height': cell_height
                            })

                for idx, crop_rect in enumerate(crops):
                    x = max(0, int(crop_rect['x']))
                    y = max(0, int(crop_rect['y']))
                    w = int(crop_rect['width'])
                    h = int(crop_rect['height'])

                    right = min(x + w, img.width)
                    bottom = min(y + h, img.height)

                    cropped = img.crop((x, y, right, bottom))

                    # 保持原格式
                    if img.mode == 'RGBA':
                        background = Image.new('RGB', cropped.size, (255, 255, 255))
                        background.paste(cropped, mask=cropped.split()[3])
                        cropped = background

                    if rows > 1 or cols > 1:
                        row_idx = idx // cols
                        col_idx = idx % cols
                        output_filename = f"{base_name}_{row_idx + 1}x{col_idx + 1}.{original_ext}"
                    else:
                        output_filename = f"{base_name}_cropped_{idx + 1}.{original_ext}"

                    output_path = os.path.join(output_dir, output_filename)
                    ImageUtils.save_image_with_quality(cropped, output_path, quality=100)
                    cropped_paths.append(output_filename)

        return cropped_paths

    def create_shape_mask(self, shape_type, width, height, points=5):
        """创建形状遮罩"""
        mask = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(mask)

        if shape_type == 'heart':
            self.draw_heart(draw, width, height)
        elif shape_type == 'circle':
            draw.ellipse([0, 0, width, height], fill=255)
        elif shape_type == 'star':
            self.draw_star(draw, width, height, points)
        elif shape_type == 'polygon':
            self.draw_polygon(draw, width, height, points)
        elif shape_type == 'triangle':
            self.draw_triangle(draw, width, height)
        elif shape_type == 'diamond':
            self.draw_diamond(draw, width, height)
        else:
            # 默认矩形
            draw.rectangle([0, 0, width, height], fill=255)

        return mask

    def draw_heart(self, draw, width, height):
        """绘制爱心"""
        # 爱心参数
        cx, cy = width / 2, height / 2
        scale = min(width, height) / 40

        # 绘制爱心路径
        points = []
        for t in range(0, 360, 2):
            rad = math.radians(t)
            x = 16 * math.sin(rad) ** 3
            y = 13 * math.cos(rad) - 5 * math.cos(2 * rad) - 2 * math.cos(3 * rad) - math.cos(4 * rad)
            points.append((cx + x * scale, cy - y * scale))

        draw.polygon(points, fill=255)

    def draw_star(self, draw, width, height, points=5):
        """绘制多角星形"""
        cx, cy = width / 2, height / 2
        outer_r = min(width, height) / 2 - 2
        inner_r = outer_r * 0.4

        vertices = []
        for i in range(points * 2):
            angle = math.radians(i * 360 / (points * 2) - 90)
            r = outer_r if i % 2 == 0 else inner_r
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            vertices.append((x, y))

        draw.polygon(vertices, fill=255)

    def draw_polygon(self, draw, width, height, sides=5):
        """绘制正多边形"""
        cx, cy = width / 2, height / 2
        r = min(width, height) / 2 - 2

        vertices = []
        for i in range(sides):
            angle = math.radians(i * 360 / sides - 90)
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            vertices.append((x, y))

        draw.polygon(vertices, fill=255)

    def draw_triangle(self, draw, width, height):
        """绘制三角形"""
        self.draw_polygon(draw, width, height, 3)

    def draw_diamond(self, draw, width, height):
        """绘制菱形"""
        cx, cy = width / 2, height / 2
        vertices = [
            (cx, 0),
            (width, cy),
            (cx, height),
            (0, cy)
        ]
        draw.polygon(vertices, fill=255)

    def apply_mask(self, image, mask):
        """应用遮罩"""
        # 创建透明背景
        result = Image.new('RGBA', image.size, (0, 0, 0, 0))
        result.paste(image, mask=mask)
        return result