from collections import namedtuple
from datetime import datetime, date

import pytest

from juniorguru.lib import club


StubReaction = namedtuple('Reaction', ['emoji', 'count'])
StubEmoji = namedtuple('Emoji', ['name'])


def test_count_upvotes():
    reactions = [StubReaction(StubEmoji('plus_one'), 4), StubReaction('👍', 1), StubReaction('🐣', 3)]
    assert club.count_upvotes(reactions) == 5


def test_count_downvotes():
    reactions = [StubReaction('🙁', 4), StubReaction('👎', 1), StubReaction('🐣', 3)]
    assert club.count_downvotes(reactions) == 1


def test_count_pins():
    reactions = [StubReaction(StubEmoji('plus_one'), 4), StubReaction('📌', 3), StubReaction('🐣', 3)]
    assert club.count_pins(reactions) == 3


@pytest.mark.parametrize('emoji, expected', [
    ('🆗', '🆗'),
    ('AHOJ', 'AHOJ'),
    (StubEmoji('lolpain'), 'lolpain'),
    (StubEmoji('BabyYoda'), 'babyyoda'),
])
def test_emoji_name(emoji, expected):
    assert club.emoji_name(emoji) == expected


StubUser = namedtuple('User', ['id'])
StubMember = namedtuple('Member', ['id', 'roles'])
StubRole = namedtuple('Role', ['id'])


@pytest.mark.parametrize('member_or_user, expected', [
    (StubUser(1), []),
    (StubMember(1, [StubRole(42), StubRole(38)]), [42, 38]),
])
def test_get_roles(member_or_user, expected):
    assert club.get_roles(member_or_user) == expected


StubClubMessage = namedtuple('ClubMessage', ['created_at'])


@pytest.mark.parametrize('date_, expected', [
    (date(2022, 1, 24), False),
    (date(2022, 1, 25), True),
    (date(2022, 1, 26), True),
])
def test_is_message_older_than(date_, expected):
    created_at = datetime.utcnow().replace(2022, 1, 25)
    message = StubClubMessage(created_at)

    assert club.is_message_older_than(message, date_) is expected


def test_is_message_older_than_no_message():
    assert club.is_message_older_than(None, date(2022, 1, 25)) is True


@pytest.mark.parametrize('today, expected', [
    (date(2022, 1, 24), False),
    (date(2022, 1, 25), True),
    (date(2022, 1, 26), True),
])
def test_is_message_over_week_ago(today, expected):
    created_at = datetime.utcnow().replace(2022, 1, 18)
    message = StubClubMessage(created_at)

    assert club.is_message_over_week_ago(message, today) is expected


@pytest.mark.parametrize('today, expected', [
    (date(2022, 2, 16), False),
    (date(2022, 2, 17), True),
    (date(2022, 2, 18), True),
])
def test_is_message_over_month_ago(today, expected):
    created_at = datetime.utcnow().replace(2022, 1, 18)
    message = StubClubMessage(created_at)

    assert club.is_message_over_month_ago(message, today) is expected
