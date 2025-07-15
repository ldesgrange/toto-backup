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
import shutil
from pathlib import Path

from mutagen import File
from mutagen.mp4 import MP4Cover

from toto_backup.tag import tag_track, Metadata
from utils import get_dummy_m4a_file, get_dummy_png_file

logger = logging.getLogger(__name__)


def test_tag_track_should_add_tags_to_track(tmp_path: Path):
    track_file = tmp_path / 'empty_1.m4a'
    shutil.copy(get_dummy_m4a_file(), track_file)

    track_metadata = Metadata()
    track_metadata.author = 'Author'
    track_metadata.title = 'Title'
    track_metadata.track_name = 'Track Name'
    track_metadata.track_number = 1
    track_metadata.track_total = 1
    track_metadata.disc_number = 1
    track_metadata.disc_total = 1
    track_metadata.card_url = 'https://example.com/card'
    track_metadata.cover_file = get_dummy_png_file()

    tag_track(track_file, track_metadata)

    actual_tags = File(track_file).tags
    assert actual_tags['\xa9ART'][0] == 'Author'
    assert actual_tags['aART'][0] == 'Author'
    assert actual_tags['\xa9alb'][0] == 'Title'
    assert actual_tags['\xa9nam'][0] == 'Track Name'
    assert actual_tags['\xa9gen'][0] == 'Audiobook'
    assert actual_tags['\xa9cmt'][0] == 'https://example.com/card'
    assert actual_tags['trkn'][0] == (1, 1)
    assert actual_tags['disk'][0] == (1, 1)
    cover: MP4Cover = actual_tags['covr'][0]
    assert cover.imageformat == MP4Cover.FORMAT_PNG


def test_tag_track_should_ignore_empty_tags(tmp_path: Path):
    track_file = tmp_path / 'empty_2.m4a'
    shutil.copy(get_dummy_m4a_file(), track_file)

    track_metadata = Metadata()

    tag_track(track_file, track_metadata)

    actual_tags = File(track_file).tags
    assert actual_tags == {
        '\xa9gen': ['Audiobook'],
    }
