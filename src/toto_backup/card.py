#
# SPDX-License-Identifier: MPL-2.0
#
# Copyright (c) 2025-2026 "Laurent Desgrange".
#
# This file is part of "toto-backup".
# See "https://github.com/ldesgrange/toto-backup") for further information.
#
# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL
# was not distributed with this file, You can obtain one
# at https://mozilla.org/MPL/2.0/.
#
from typing import Any

from toto_backup.utils import deep_get


class DuplicateTrackError(Exception):
    def __init__(self, track_number: int, chapter_number: int):
        super().__init__(f'Track {track_number} already exists in chapter {chapter_number}.')


class DuplicateChapterError(Exception):
    def __init__(self, chapter_number: int):
        super().__init__(f'Chapter {chapter_number} already exists.')


class EmptyChapterError(Exception):
    def __init__(self, chapter_number: int, title: str):
        super().__init__(f'Chapter {chapter_number} “{title}” has no tracks.')


class InvalidDataError(Exception):
    def __init__(self):
        super().__init__('Invalid data.')


class Track:
    def __init__(self, track_number: int, title: str, url: str):
        self._track_number: int = track_number
        self._title: str = title
        self._url: str = url

    @property
    def track_number(self) -> int:
        return self._track_number

    @property
    def title(self) -> str:
        return self._title

    @property
    def url(self) -> str:
        return self._url


class Chapter:
    def __init__(self, chapter_number: int, title: str, icon_url: str):
        self._chapter_number: int = chapter_number
        self._title: str = title
        self._icon_url: str = icon_url
        self._tracks: list[Track] = []

    def add_track(self, track: Track) -> None:
        is_duplicate = len([t for t in self._tracks if t.track_number == track.track_number]) > 0
        if is_duplicate:
            raise DuplicateTrackError(track.track_number, self._chapter_number)
        self._tracks.append(track)

    @property
    def chapter_number(self) -> int:
        return self._chapter_number

    @property
    def title(self) -> str:
        return self._title

    @property
    def icon_url(self) -> str:
        return self._icon_url

    @property
    def tracks(self) -> list[Track]:
        return self._tracks


class Card:
    def __init__(self, title: str, author: str, cover_url: str):
        self._title: str = title
        self._author: str = author
        self._cover_url: str = cover_url
        self._chapters: list[Chapter] = []
        self._track_total: int = 0

    def add_chapter(self, chapter: Chapter):
        is_duplicate = len([c for c in self._chapters if c.chapter_number == chapter.chapter_number]) > 0
        if is_duplicate:
            raise DuplicateChapterError(chapter.chapter_number)

        track_count = len(chapter.tracks)
        if track_count == 0:
            raise EmptyChapterError(chapter.chapter_number, chapter.title)

        self._chapters.append(chapter)
        self._track_total += track_count

    @property
    def title(self) -> str:
        return self._title

    @property
    def author(self) -> str:
        return self._author

    @property
    def cover_url(self) -> str:
        return self._cover_url

    @property
    def chapters(self) -> list[Chapter]:
        return self._chapters

    @property
    def track_total(self) -> int:
        return self._track_total


def parse_data(data: Any) -> Card:
    """
    Parses the provided data to construct a `Card` object with its relevant chapters
    and tracks. This function extracts metadata, such as title, author, and cover URL,
    from the input and organizes it hierarchically using `Card`, `Chapter`, and `Track`
    classes.

    :param data: The input data containing card and chapter details.
    :return: A `Card` object populated with its chapters and tracks.
    :raises InvalidDataError: If the input data is of an invalid type or does not
        conform to the expected structure.
    """
    cover_url = parse_string(deep_get(data, ['props', 'pageProps', 'card', 'metadata', 'cover', 'imageL'])) or ''
    author = parse_string(deep_get(data, ['props', 'pageProps', 'card', 'metadata', 'author'])) or ''
    title = parse_string(deep_get(data, ['props', 'pageProps', 'card', 'title'])) or ''
    card = Card(title, author, cover_url)

    chapters = deep_get(data, ['props', 'pageProps', 'card', 'content', 'chapters'], {})
    for chapter_index, chapter_data in enumerate(chapters):
        chapter_number = chapter_index + 1
        chapter_title = parse_string(chapter_data['title']) or ''
        chapter_icon_url = parse_string(chapter_data['display']['icon16x16']) or ''
        chapter = Chapter(chapter_number, chapter_title, chapter_icon_url)

        for track_index, track_data in enumerate(chapter_data['tracks']):
            track_number = track_index + 1
            track_title = parse_string(track_data['title']) or ''
            track_url = parse_string(track_data['trackUrl']) or ''
            track = Track(track_number, track_title, track_url)
            chapter.add_track(track)

        card.add_chapter(chapter)

    if len(card.chapters) == 0:
        raise InvalidDataError()
    else:
        return card


def parse_string(text: str | None) -> str | None:
    if text is None:
        return None
    return text.strip()
