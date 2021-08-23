import os
from pathlib import Path

from juniorguru.lib.images import render_image_file


FLUSH_THUMBNAILS = bool(int(os.getenv('FLUSH_THUMBNAILS', 0)))
THUMBNAILS_DIR = Path(__file__).parent.parent / 'web' / 'static' / 'images' / 'thumbnails'
THUMBNAIL_WIDTH = 1200
THUMBNAIL_HEIGHT = 630


def thumbnail(title):
    context = dict(title=title)
    image_path = render_image_file(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT,
                                   'thumbnail.html', context, THUMBNAILS_DIR)
    return f'images/thumbnails/{image_path.name}'


def thumbnail_logo():
    image_path = render_image_file(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT,
                                   'thumbnail_logo.html', {}, THUMBNAILS_DIR)
    return f'images/thumbnails/{image_path.name}'
