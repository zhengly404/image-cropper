from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import os
import zipfile
import io
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config
from utils.image_utils import ImageUtils
from crop_strategies.grid_strategy import GridStrategy
from crop_strategies.custom_strategy import CustomCropStrategy  # 新增自定义裁剪策略
import importlib
import base64
from PIL import Image
import json

app = Flask(__name__)
app.config.from_object(Config)

# 初始化应用
Config.init_app(app)


class CropStrategyManager:
    """裁剪策略管理器"""

    def __init__(self):
        self.strategies = {}
        self._load_strategies()

    def _load_strategies(self):
        """加载所有裁剪策略"""
        for strategy_id, strategy_config in Config.CROP_STRATEGIES.items():
            try:
                # 动态导入策略模块
                module_path, class_name = strategy_config['module'].rsplit('.', 1)
                module = importlib.import_module(f'crop_strategies.{module_path}')
                strategy_class = getattr(module, class_name)

                # 实例化策略
                self.strategies[strategy_id] = strategy_class(strategy_config)
            except Exception as e:
                print(f"加载策略 {strategy_id} 失败: {e}")

    def get_strategy(self, strategy_id):
        """获取策略实例"""
        return self.strategies.get(strategy_id)

    def get_all_strategies(self):
        """获取所有策略信息"""
        return {
            strategy_id: {
                'name': strategy.name,
                'description': strategy.description
            }
            for strategy_id, strategy in self.strategies.items()
        }


# 创建策略管理器
strategy_manager = CropStrategyManager()
# 创建自定义裁剪策略实例
custom_strategy = CustomCropStrategy({'name': '自定义裁剪', 'description': '手动拖动裁剪框'})


@app.route('/')
def index():
    """主页面"""
    strategies = strategy_manager.get_all_strategies()
    return render_template('index.html', strategies=strategies)


@app.route('/upload', methods=['POST'])
def upload_image():
    """上传图片"""
    if 'image' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    if not ImageUtils.allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
        return jsonify({'error': '不支持的文件格式'}), 400

    # 生成安全的文件名（带时间戳避免重名）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = secure_filename(file.filename)
    filename = f"{timestamp}_{filename}"

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    return jsonify({
        'success': True,
        'filename': filename,
        'filepath': filepath
    })


@app.route('/get_image_info/<filename>')
def get_image_info(filename):
    """获取图片信息（尺寸等）"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404

    try:
        with Image.open(filepath) as img:
            width, height = img.size
            return jsonify({
                'width': width,
                'height': height
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/calculate_grid/<filename>', methods=['POST'])
def calculate_grid(filename):
    """计算网格裁剪参数"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404

    try:
        data = request.json
        rows = data.get('rows', 3)
        cols = data.get('cols', 3)

        with Image.open(filepath) as img:
            width, height = img.size

            # 计算每个格子的尺寸
            cell_width = width // cols
            cell_height = height // rows

            # 计算裁剪区域（取正方形，以较小的边为准）
            square_size = min(cell_width, cell_height)

            # 计算总的裁剪区域
            total_width = square_size * cols
            total_height = square_size * rows

            # 居中偏移
            offset_x = (width - total_width) // 2
            offset_y = (height - total_height) // 2

            return jsonify({
                'success': True,
                'cell_size': square_size,
                'total_width': total_width,
                'total_height': total_height,
                'offset_x': offset_x,
                'offset_y': offset_y,
                'rows': rows,
                'cols': cols,
                'image_width': width,
                'image_height': height
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/preview/<strategy_id>/<filename>')
def preview_crop(strategy_id, filename):
    """预览裁剪效果"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404

    strategy = strategy_manager.get_strategy(strategy_id)
    if not strategy:
        return jsonify({'error': '未知的裁剪策略'}), 400

    try:
        preview_info = strategy.get_preview_info(filepath)
        return jsonify(preview_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/crop', methods=['POST'])
def crop_image():
    """执行裁剪"""
    data = request.json
    filename = data.get('filename')
    strategy_id = data.get('strategy_id', 'custom')  # 默认使用自定义策略

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404

    try:
        # 如果是自定义裁剪
        if strategy_id == 'custom':
            crop_data = data.get('crop_data', {})
            cropped_files = custom_strategy.crop(filepath, os.path.dirname(filepath), crop_data)
        else:
            strategy = strategy_manager.get_strategy(strategy_id)
            if not strategy:
                return jsonify({'error': '未知的裁剪策略'}), 400
            cropped_files = strategy.crop(filepath, os.path.dirname(filepath))

        return jsonify({
            'success': True,
            'files': cropped_files,
            'download_url': f'/download/{filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download/<filename>')
def download_zip(filename):
    """打包下载裁剪后的图片"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    base_name = os.path.splitext(filename)[0]

    # 创建ZIP文件
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 查找所有相关的裁剪文件
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            if file.startswith(base_name + '_') and file != filename:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
                zf.write(file_path, file)

    memory_file.seek(0)

    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{base_name}_cropped.zip'
    )


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """提供上传文件访问"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/get_all_images')
def get_all_images():
    """获取uploads文件夹中的所有图片"""
    try:
        images = []
        upload_folder = app.config['UPLOAD_FOLDER']

        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                # 检查是否为图片文件
                if ImageUtils.allowed_file(filename, app.config['ALLOWED_EXTENSIONS']):
                    filepath = os.path.join(upload_folder, filename)
                    # 获取文件信息
                    stat = os.stat(filepath)
                    images.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'url': f'/uploads/{filename}'
                    })

        # 按修改时间倒序排列（最新的在前面）
        images.sort(key=lambda x: x['modified'], reverse=True)

        return jsonify({
            'success': True,
            'images': images,
            'total': len(images)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/delete_image/<filename>', methods=['DELETE'])
def delete_image(filename):
    """删除指定图片"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404

    try:
        os.remove(filepath)
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/gallery')
def gallery_page():
    """图片库页面"""
    return render_template('gallery.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)