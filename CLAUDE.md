# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言

始终使用中文沟通，包括提问、解释、讨论等所有场景。

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the development server (Flask debug mode on port 5000)
python app.py
```

No test framework or build system is configured. Dependencies: Flask, Pillow, Werkzeug.

## Architecture

Flask web application for image cropping with a plugin-like strategy pattern.

### Backend

- **app.py** — Main Flask app. Routes: upload, crop, preview, download (ZIP), image gallery CRUD. Uses `CropStrategyManager` to dynamically load strategies from config.
- **config.py** — `Config` class with upload folder, allowed extensions (png/jpg/jpeg/gif/bmp/webp), 16MB limit, and crop strategy definitions. Each strategy specifies rows/cols and a module path for dynamic import.
- **utils/image_utils.py** — `ImageUtils` static methods: file extension validation, format-aware image saving (handles JPEG/RGB conversion, PNG optimization, WebP quality), crop size calculation.
- **crop_strategies/** — Strategy pattern directory. Strategies are dynamically imported and registered via `Config.CROP_STRATEGIES`.
  - **base_strategy.py** — Abstract base class `BaseCropStrategy` with `crop()` and `get_preview_info()`.
  - **grid_strategy.py** — `GridStrategy`: crops an image into equal squares arranged in a centered grid (e.g. 3x3, 4x4). Config-driven via rows/cols.
  - **custom_strategy.py** — `CustomCropStrategy`: supports free-form rectangle cropping and shape cropping with masks (heart, star, polygon, diamond, triangle, circle). Shapes are drawn using PIL `ImageDraw` with mathematical coordinate computation.
- **uploads/** — Uploaded and cropped images stored here. Cropped files are named `{original}_{row}x{col}.{ext}`.

### Frontend

- **templates/index.html** — Main cropping UI: upload area, grid controls (rows/cols), crop preview canvas, shape selector, execute/download buttons. Uses canvas-based drag interaction for custom cropping.
- **templates/gallery.html** — Image gallery page to browse, select, and delete uploaded images.
- **static/style.css** (~1350 lines) — Main application styles including crop workspace, toolbar, canvas, shape selector popup.
- **static/gallery.css** (~520 lines) — Gallery-specific styles (grid layout, image cards, modal).

### Flow

1. User uploads image → `/upload` → file saved to `uploads/` with timestamp prefix
2. User configures crop (grid settings or drag custom rectangles / shapes) → all handled client-side via canvas
3. User executes crop → `/crop` with `strategy_id` and crop data → strategy processes image → returns cropped filenames
4. User downloads → `/download/{filename}` → all cropped pieces bundled into ZIP

### Key patterns

- Dynamic module loading: strategies imported via `importlib.import_module` based on config strings
- Strategy pattern: each crop strategy implements `BaseCropStrategy` interface
- Shape masking: custom shapes rendered as PIL `L` mode masks, then composited onto RGBA images
- The `custom` strategy_id is hardcoded as the default in `/crop` and instantiated separately in app.py (not via the strategy manager)
