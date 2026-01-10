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
import logging
from pathlib import Path
from unittest import mock
from unittest.mock import Mock

from requests import HTTPError

from toto_backup.card import Card
from toto_backup.toto_backup import create_card_directory, download_and_move_content

logger = logging.getLogger(__name__)


def test_create_card_directory_should_create_card_directory(tmp_path: Path):
    parent_directory = tmp_path

    card = Card('title', 'author', 'https://example.com/cover.png')
    card_directory = create_card_directory(parent_directory, card)

    assert card_directory.is_dir()
    assert card_directory.name == 'author - title'
    assert card_directory.parent == parent_directory


def test_create_card_directory_should_sanitize_card_directory_name(tmp_path: Path):
    parent_directory = tmp_path

    card = Card('Therapy?!:', ' AC/DC', 'https://example.com/cover.png')
    card_directory = create_card_directory(parent_directory, card)

    assert card_directory.is_dir()
    assert card_directory.name == 'ACDC - Therapy!'
    assert card_directory.parent == parent_directory


@mock.patch('toto_backup.toto_backup.should_overwrite_directory')
def test_create_card_directory_may_overwrite_existing_directory(confirm_mock: Mock, tmp_path: Path):
    parent_directory = tmp_path
    card = Card('title', 'author', 'https://example.com/cover.png')
    card_directory = create_card_directory(parent_directory, card)
    file_in_card_directory = card_directory / 'dummy.txt'
    file_in_card_directory.touch()

    # Reject overwriting.
    confirm_mock.reset_mock()
    confirm_mock.return_value = False
    create_card_directory(parent_directory, card)
    confirm_mock.assert_called_once_with(card_directory)
    # Nothing has been deleted.
    assert card_directory.exists() is True
    assert file_in_card_directory.exists() is True

    # Accept overwriting.
    confirm_mock.reset_mock()
    confirm_mock.return_value = True
    create_card_directory(parent_directory, card)
    confirm_mock.assert_called_once_with(card_directory)
    # Directory has been recreated.
    assert card_directory.exists() is True
    # Existing content has been deleted.
    assert file_in_card_directory.exists() is False


@mock.patch('toto_backup.toto_backup.download_content')
def test_download_and_move_content_should_download_and_move_content(download_mock: Mock, tmp_path: Path):
    destination_directory = tmp_path / 'destination'
    destination_directory.mkdir()

    download_mock.reset_mock()
    temp_download_file = tmp_path / 'tmpfile'
    temp_download_file.write_bytes(b'content')
    download_mock.return_value = (temp_download_file, 'audio/mpeg')
    final_file = download_and_move_content('https://example.com/track1.mp3', destination_directory / 'file')
    assert final_file.exists() is True
    assert final_file.read_bytes() == b'content'
    assert final_file.name == 'file.mp3'
    assert final_file.parent == destination_directory
    download_mock.assert_called_once_with('https://example.com/track1.mp3')


@mock.patch('toto_backup.toto_backup.download_content')
def test_download_and_move_content_should_return_none_in_case_of_error(download_mock: Mock, tmp_path: Path):
    destination_directory = tmp_path / 'destination'
    destination_directory.mkdir()

    download_mock.reset_mock()
    download_mock.side_effect = HTTPError()
    final_file = download_and_move_content('https://example.com/track1.mp3', destination_directory / 'file')
    assert final_file is None
    download_mock.assert_called_once_with('https://example.com/track1.mp3')
