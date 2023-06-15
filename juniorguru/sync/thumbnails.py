from pathlib import Path

import click

from juniorguru.cli.sync import main as cli
from juniorguru.lib import loggers
from juniorguru.lib.images import render_image_file
from juniorguru.models.base import db
from juniorguru.models.job import ListedJob
from juniorguru.models.page import LegacyThumbnail, Page
from juniorguru.web_legacy import app, generate_job_pages, get_freezer


logger = loggers.from_path(__file__)


# Generating thumbnails for the legacy Flask app requires jobs data and events
@cli.sync_command(dependencies=['pages', 'jobs-listing', 'events'])
@click.option('--images-path', default='juniorguru/images', type=click.Path(exists=True, path_type=Path))
@click.option('--output-dir', default='thumbnails', type=click.Path(path_type=Path))
@click.option('--width', default=1200, type=int)
@click.option('--height', default=630, type=int)
@click.option('--clear/--no-clear', default=False)
@db.connection_context()
def main(images_path, output_dir, width, height, clear):
    output_path = images_path / output_dir
    output_path.mkdir(exist_ok=True)

    if clear:
        existing_paths = list(output_path.glob('*.png'))
        logger.info(f'Removing {len(existing_paths)} existing thumbnails')
        for existing_path in existing_paths:
            existing_path.unlink()

    pages = list(Page.listing())
    logger.info(f'Generating {len(pages)} thumbnails')
    for page in pages:
        context = dict(title=page.meta.get('thumbnail_title', page.meta['title']),
                       badge=page.meta.get('thumbnail_badge'))
        image_path = render_image_file(width, height, 'thumbnail.html', context, output_path)
        page.thumbnail_path = image_path.relative_to(images_path)
        page.save()
        logger.info(f'Page {page.src_uri}: {image_path}')

    logger.info('Dealing with legacy pages')  # all below can be deleted once Flask is gone
    LegacyThumbnail.drop_table()
    LegacyThumbnail.create_table()

    equivalents = {
        '/club/': 'club.md',
        '/courses/': 'courses.md',
        '/open/': 'open.md',
        '/podcast/': 'podcast.md',
        '/handbook/': 'handbook/index.md',
        '/handbook/candidate/': 'handbook/candidate.md',
        '/hire-juniors/': 'pricing.md',
        '/pricing/': 'pricing.md',
    }
    for url, src_uri in equivalents.items():
        page = Page.get(Page.src_uri == src_uri)
        LegacyThumbnail.create(url=url, image_path=page.thumbnail_path)

    default_image_path = render_image_file(width, height, 'thumbnail_legacy.html', {}, output_path)
    for url in ['/',
                '/404.html',
                '/donate/',
                '/press/',
                '/press/crisis/',
                '/press/handbook/',
                '/press/women/']:
        LegacyThumbnail.create(url=url, image_path=default_image_path.relative_to(images_path))

    for url, title in [('/events/', 'Klubové akce'),
                       ('/membership/', 'Rozcestník pro členy klubu'),
                       ('/jobs/', 'Práce v IT pro začátečníky'),
                       ('/jobs/remote/', 'Práce v IT pro začátečníky — na dálku'),
                       ('/jobs/region/praha/', 'Práce v IT pro začátečníky — Praha'),
                       ('/jobs/region/brno/', 'Práce v IT pro začátečníky — Brno'),
                       ('/jobs/region/ostrava/', 'Práce v IT pro začátečníky — Ostrava'),
                       ('/jobs/region/ceske-budejovice/', 'Práce v IT pro začátečníky — České Budějovice'),
                       ('/jobs/region/hradec-kralove/', 'Práce v IT pro začátečníky — Hradec Králové'),
                       ('/jobs/region/jihlava/', 'Práce v IT pro začátečníky — Jihlava'),
                       ('/jobs/region/karlovy-vary/', 'Práce v IT pro začátečníky — Karlovy Vary'),
                       ('/jobs/region/liberec/', 'Práce v IT pro začátečníky — Liberec'),
                       ('/jobs/region/olomouc/', 'Práce v IT pro začátečníky — Olomouc'),
                       ('/jobs/region/pardubice/', 'Práce v IT pro začátečníky — Pardubice'),
                       ('/jobs/region/plzen/', 'Práce v IT pro začátečníky — Plzeň'),
                       ('/jobs/region/usti-nad-labem/', 'Práce v IT pro začátečníky — Ústí nad Labem'),
                       ('/jobs/region/zlin/', 'Práce v IT pro začátečníky — Zlín'),
                       ('/jobs/region/germany/', 'Práce v IT pro začátečníky — Německo'),
                       ('/jobs/region/poland/', 'Práce v IT pro začátečníky — Polsko'),
                       ('/jobs/region/austria/', 'Práce v IT pro začátečníky — Rakousko'),
                       ('/jobs/region/slovakia/', 'Práce v IT pro začátečníky — Slovensko')]:
        image_path = render_image_file(width, height, 'thumbnail_legacy.html', dict(title=title), output_path)
        LegacyThumbnail.create(url=url, image_path=image_path.relative_to(images_path))

    for _, params in generate_job_pages():
        job = ListedJob.get_by_submitted_id(params['job_id'])
        context = dict(job_title=job.title,
                       job_company=job.company_name,
                       job_location=job.location)
        image_path = render_image_file(width, height, 'thumbnail_legacy.html', context, output_path)
        LegacyThumbnail.create(url=f"/jobs/{params['job_id']}/", image_path=image_path.relative_to(images_path))

    expected_urls = frozenset(get_freezer(app).all_urls())
    urls = frozenset(thumbnail.url for thumbnail in LegacyThumbnail.select())
    missing_urls = expected_urls - urls
    if missing_urls:
        logger.error(f'Missing legacy pages: {", ".join(sorted(missing_urls))}')
        raise click.Abort()