#
# SPDX-License-Identifier: MPL-2.0
#
# Copyright (c) 2025-2025 "Laurent Desgrange".
#
# This file is part of "toto-backup".
# See "https://github.com/ldesgrange/toto-backup") for further information.
#
# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL
# was not distributed with this file, You can obtain one
# at https://mozilla.org/MPL/2.0/.
#
import logging

import pytest

from toto_backup.card import (
    Card,
    Chapter,
    EmptyChapterError,
    Track,
    DuplicateTrackError,
    DuplicateChapterError,
    parse_data,
    InvalidDataError,
    parse_string,
)

logger = logging.getLogger(__name__)


def test_chapter_add_track_should_raise_error_when_track_number_already_exists():
    track_1 = Track(1, 'Track 1', 'url_1')
    track_2 = Track(1, 'Track 2', 'url_2')
    chapter = Chapter(1, 'Chapter 1', 'icon_url')

    chapter.add_track(track_1)
    with pytest.raises(DuplicateTrackError) as e:
        chapter.add_track(track_2)
    assert str(e.value) == 'Track 1 already exists in chapter 1.'


def test_card_add_chapter_should_raise_error_when_chapter_has_no_tracks():
    chapter = Chapter(1, 'Chapter 1', 'icon_url')
    card = Card('title', 'author', 'cover_url')

    with pytest.raises(EmptyChapterError) as e:
        card.add_chapter(chapter)
    assert str(e.value) == 'Chapter 1 “Chapter 1” has no tracks.'


def test_card_add_chapter_should_raise_error_when_chapter_number_already_exists():
    track_1 = Track(1, 'Track 1', 'url_1')
    chapter_1 = Chapter(1, 'Chapter 1', 'icon_url')
    chapter_1.add_track(track_1)
    chapter_2 = Chapter(1, 'Chapter 2', 'icon_url')
    chapter_2.add_track(track_1)
    card = Card('title', 'author', 'cover_url')

    card.add_chapter(chapter_1)
    with pytest.raises(DuplicateChapterError) as e:
        card.add_chapter(chapter_2)
    assert str(e.value) == 'Chapter 1 already exists.'


def test_card_track_total_should_return_track_count():
    track_1 = Track(1, 'Track 1', 'url_1')
    track_2 = Track(2, 'Track 2', 'url_2')

    chapter_1 = Chapter(1, 'Chapter 1', 'icon_url')
    chapter_1.add_track(track_1)
    chapter_1.add_track(track_2)

    card = Card('title', 'author', 'cover_url')
    assert card.track_total == 0

    card.add_chapter(chapter_1)
    assert card.track_total == 2  # noqa: PLR2004

    chapter_2 = Chapter(2, 'Chapter 2', 'icon_url')
    chapter_2.add_track(track_1)
    chapter_2.add_track(track_2)
    card.add_chapter(chapter_2)
    assert card.track_total == 4  # noqa: PLR2004


def test_parse_data_should_raise_error_when_invalid_data_provided():
    with pytest.raises(InvalidDataError) as e:
        parse_data(None)
    assert str(e.value) == 'Invalid data.'
    assert str(e.value.__cause__) == "'NoneType' object is not subscriptable"
    assert type(e.value.__cause__) is TypeError

    with pytest.raises(InvalidDataError) as e:
        parse_data([])
    assert str(e.value) == 'Invalid data.'
    assert str(e.value.__cause__) == 'list indices must be integers or slices, not str'
    assert type(e.value.__cause__) is TypeError

    with pytest.raises(InvalidDataError) as e:
        parse_data({'props': {'pageProps': {'card': {}}}})
    assert str(e.value) == 'Invalid data.'
    assert str(e.value.__cause__) == "'metadata'"
    assert type(e.value.__cause__) is KeyError


def test_parse_data_should_return_populated_card():
    data = {
        'props': {
            'pageProps': {
                'card': {
                    'metadata': {
                        'cover': {'imageL': ' cover_url '},
                        'author': '\tauthor\n',
                    },
                    'title': ' title ',
                    'content': {
                        'chapters': [
                            {
                                'title': ' Chapter 1 ',
                                'display': {'icon16x16': ' chapter_1_icon_url '},
                                'tracks': [
                                    {'title': ' Track 1 ', 'trackUrl': ' track_1_url '},
                                    {'title': ' Track 2 ', 'trackUrl': ' track_2_url '},
                                ],
                            },
                            {
                                'title': 'Chapter 2',
                                'display': {'icon16x16': ' chapter_2_icon_url '},
                                'tracks': [
                                    {'title': ' Track 3 ', 'trackUrl': ' track_3_url '},
                                    {'title': ' Track 4 ', 'trackUrl': ' track_4_url '},
                                ],
                            },
                        ],
                    },
                }
            }
        }
    }

    card = parse_data(data)
    assert card.title == 'title'
    assert card.author == 'author'
    assert card.cover_url == 'cover_url'
    assert len(card.chapters) == 2  # noqa: PLR2004
    assert card.chapters[0].chapter_number == 1
    assert card.chapters[0].title == 'Chapter 1'
    assert card.chapters[0].icon_url == 'chapter_1_icon_url'
    assert len(card.chapters[0].tracks) == 2  # noqa: PLR2004
    assert card.chapters[0].tracks[0].track_number == 1


def test_parse_string_should_clean_string():
    assert parse_string(None) is None
    assert parse_string('') == ''
    assert parse_string('foo') == 'foo'
    assert parse_string(' \n\t foo \n\t ') == 'foo'  # noqa: RUF001
