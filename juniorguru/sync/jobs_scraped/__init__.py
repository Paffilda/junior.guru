import asyncio
import importlib
import itertools
from collections import Counter
from pprint import pformat
from typing import Awaitable, Callable

from peewee import IntegrityError

from juniorguru.cli.sync import Cache, main as cli
from juniorguru.lib import apify, loggers
from juniorguru.lib.cli import async_command
from juniorguru.models.base import db
from juniorguru.models.job import ScrapedJob


ACTORS = [
    "honzajavorek/jobs-jobscz",
    "honzajavorek/jobs-linkedin",
    "honzajavorek/jobs-startupjobs",
    "honzajavorek/jobs-weworkremotely",
]

PIPELINES = [
    "juniorguru.sync.jobs_scraped.pipelines.blocklist",
    "juniorguru.sync.jobs_scraped.pipelines.boards_ids",
    # "juniorguru.sync.jobs_scraped.pipelines.llm_opinion",  WORKS, BUT TOO SLOW
    "juniorguru.sync.jobs_scraped.pipelines.description_parser",
    "juniorguru.sync.jobs_scraped.pipelines.features_parser",
    "juniorguru.sync.jobs_scraped.pipelines.gender_remover",
    "juniorguru.sync.jobs_scraped.pipelines.emoji_remover",
    "juniorguru.sync.jobs_scraped.pipelines.employment_types_cleaner",
    "juniorguru.sync.jobs_scraped.pipelines.juniority_re_score",
]


logger = loggers.from_path(__file__)


class DropItem(Exception):
    pass


@cli.sync_command()
@cli.pass_cache
@async_command
async def main(cache: Cache):
    logger.info(f"Actors:\n{pformat(ACTORS)}")
    items = itertools.chain.from_iterable(
        apify.iter_data(actor, cache=cache) for actor in ACTORS
    )

    logger.info(f"Pipelines:\n{pformat(PIPELINES)}")
    pipelines = [
        (
            pipeline_name.split(".")[-1],
            importlib.import_module(pipeline_name).process,
        )
        for pipeline_name in PIPELINES
    ]

    logger.info("Setting up db table")
    with db.connection_context():
        ScrapedJob.drop_table()
        ScrapedJob.create_table()

    logger.info("Processing items")
    stats = Counter()
    for item in logger.progress(items):
        logger.debug(f"Item {item['url']}")
        try:
            item = await process_item(pipelines, item)
        except DropItem:
            stats["drops"] += 1
        else:
            stats["items"] += 1
            logger.debug(f"Saving {item['url']}")
            await asyncio.get_running_loop().run_in_executor(None, save_item, item)
    logger.info(f"Stats: {stats['items']} items, {stats['drops']} drops")


async def process_item(
    pipelines: list[Callable[..., Awaitable[dict]]],
    item: dict,
) -> dict:
    for pipeline_name, pipeline in pipelines:
        try:
            item = await pipeline(item)
        except DropItem as e:
            logger[pipeline_name].debug(f"Dropping: {e}\n{pformat(item)}")
            raise
        except Exception:
            logger.error(f"Pipeline {pipeline_name!r} failed:\n{pformat(item)}")
            raise
    return item


@db.connection_context()
def save_item(item: dict):
    job = ScrapedJob.from_item(item)
    try:
        job.save()
        logger.debug(f"Created {item['url']} as {job!r}")
    except IntegrityError:
        job = ScrapedJob.get_by_item(item)
        job.merge_item(item)
        job.save()
        logger.debug(f"Merged {item['url']} to {job!r}")
