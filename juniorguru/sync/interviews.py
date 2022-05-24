from datetime import timedelta

from discord import Embed, Colour

from juniorguru.lib import loggers
from juniorguru.lib.club import (DISCORD_MUTATIONS_ENABLED, is_message_over_period_ago,
                                 run_discord_task, MENTORING_CHANNEL)
from juniorguru.lib.tasks import sync_task
from juniorguru.models.base import db
from juniorguru.models.club import ClubMessage
from juniorguru.models.mentor import Mentor
from juniorguru.sync.club_content import main as club_content_task
from juniorguru.sync.mentoring import main as mentoring_task


INTERVIEWS_CHANNEL = 789107031939481641

INTERVIEWS_EMOJI = '💁'


logger = loggers.get(__name__)


@sync_task(club_content_task, mentoring_task)
def main():
    run_discord_task('juniorguru.sync.interviews.discord_task')


@db.connection_context()
async def discord_task(client):
    last_message = ClubMessage.last_bot_message(INTERVIEWS_CHANNEL, INTERVIEWS_EMOJI, 'xyz')
    if is_message_over_period_ago(last_message, timedelta(days=30)):
        logger.info('Last message is more than one month old!')
        if DISCORD_MUTATIONS_ENABLED:
            channel = await client.fetch_channel(INTERVIEWS_CHANNEL)

            embed_mentors_description = '\n'.join([
                f'[{mentor.user.display_name}]({mentor.message_url}) – {mentor.topics}'
                for mentor in Mentor.interviews_listing()
            ])
            embed_mentors = Embed(colour=Colour.orange(),
                                  description=embed_mentors_description)

            embed_handbook = Embed(description=(
                '📖 Než se pustíš do pohovorů, přečti si '
                '[příručku na junior.guru](https://junior.guru/candidate-handbook/) o tom, '
                'jak správně hledat první práci v IT.'
            ))

            await channel.send(content=(
                f"{INTERVIEWS_EMOJI} Pomohla by ti soustavnější příprava na přijímací řízení? "
                "Chceš si jednorázově vyzkoušet pohovor nanečisto, česky nebo anglicky? "
                f"Někteří členové se v <#{MENTORING_CHANNEL}> k takovým konzultacím nabídli!"
            ), embeds=[embed_mentors, embed_handbook])
        else:
            logger.warning('Discord mutations not enabled')