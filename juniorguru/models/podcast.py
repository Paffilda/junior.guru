from datetime import date

import arrow
from peewee import CharField, IntegerField, DateTimeField

from juniorguru.models.base import BaseModel


class PodcastEpisode(BaseModel):
    id = CharField()
    publish_on = DateTimeField(index=True)
    title = CharField()
    media_url = CharField()
    media_size = IntegerField()
    media_type = CharField()
    media_duration_s = IntegerField()
    description = CharField()

    @property
    def global_id(self):
        return f'podcast.junior.guru#{self.id}'

    @property
    def number(self):
        return int(self.id)

    @property
    def title_numbered(self):
        return f"#{self.number} {self.title}"

    @property
    def slug(self):
        return f'episode{self.id}'

    @property
    def url(self):
        return f'https://junior.guru/podcast/#{self.slug}'

    @property
    def publish_at_prg(self):
        return arrow.get(self.publish_on) \
            .replace(minute=42, second=42) \
            .to('Europe/Prague') \
            .datetime

    @classmethod
    def listing(cls, today=None):
        today = today or date.today()
        return cls.select() \
            .where(cls.publish_on <= today) \
            .order_by(cls.publish_on.desc())

    @classmethod
    def api_listing(cls, today=None):
        today = today or date.today()
        return cls.select() \
            .where(cls.publish_on <= today) \
            .order_by(cls.publish_on)

    @classmethod
    def copyright_year(cls, today=None):
        today = today or date.today()
        last_episode = cls.select() \
            .order_by(cls.publish_on.desc()) \
            .first()
        if last_episode:
            return last_episode.publish_on.year
        return today.year