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
import os
import platform
from pathlib import Path

import pytest
import responses
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from toto_backup.toto_backup import main
from utils import get_dummy_png_file, get_dummy_m4a_file

logger = logging.getLogger(__name__)


@pytest.fixture()
def setup_teardown(caplog: LogCaptureFixture):
    caplog.set_level(10000)
    yield
    caplog.set_level(logging.NOTSET)


def test_main_help(setup_teardown):
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert result.output == (
        'Usage: main [OPTIONS] URL\n'
        '\n'
        '  Simple backup tool for your Yoto cards.\n'
        '\n'
        '  URL is the URL of the Yoto card to back up (e.g.,\n'
        '  https://yoto.io/XXXXX?ABCDEFGHIJKL=MNOPQRSTUVWXY).\n'
        '\nOptions:'
        '\n  --help  Show this message and exit.\n'
    )


@responses.activate
def test_main(caplog: LogCaptureFixture, setup_teardown):
    # Mock HTTP response for card page.
    responses.add(
        responses.Response(
            method='GET',
            url='https://example.url/xxx',
            status=200,
            content_type='text/html',
            body=generate_card_page_body(),
        )
    )
    # Mock HTTP response for card cover.
    responses.add(
        responses.Response(
            method='GET',
            url='https://example.url/card/cover',
            status=200,
            content_type='image/png',
            body=get_dummy_png_file().read_bytes(),
        )
    )
    # Mock HTTP response for tracks/icons.
    for chapter_number in range(1, 3):
        responses.add(
            responses.Response(
                method='GET',
                url=f'https://example.url/card/chapter-{chapter_number}-icon',
                status=200,
                content_type='image/png',
                body=get_dummy_png_file().read_bytes(),
            )
        )
        responses.add(
            responses.Response(
                method='GET',
                url=f'https://example.url/card/chapter-{chapter_number}-track-1',
                status=200,
                content_type='audio/x-m4a',
                body=get_dummy_m4a_file().read_bytes(),
            )
        )

    runner = CliRunner()
    with runner.isolated_filesystem() as tmp_dir:
        expected_tmp_dir = tmp_dir
        # Resolve the real path on macos.
        if platform.system() == 'Darwin':
            expected_tmp_dir = os.path.realpath(tmp_dir)
        result = runner.invoke(main, ['https://example.url/xxx'])
        assert result.exit_code == 0
        assert result.output == (
            'Fetching page at: https://example.url/xxx\n'
            'Find data…\n'
            'Creating card directory…\n'
            'Downloading card cover…\n'
            'Downloading tracks…\n'
            f'Track 1/2 successfully downloaded to {expected_tmp_dir}{os.sep}Author Name - The Card Title{os.sep}'
            '1-01_Chapter 1 - Introduction.m4a\n'
            f'Track 2/2 successfully downloaded to {expected_tmp_dir}{os.sep}Author Name - The Card Title{os.sep}'
            '1-02_Chapter 2.m4a\n'
            'Card backup completed, 2 tracks backed up successfully, 0 failed.\n'
        )
        assert (Path(expected_tmp_dir) / 'Author Name - The Card Title' / 'cover.png').exists()
        assert (Path(expected_tmp_dir) / 'Author Name - The Card Title' / '1-01_Chapter 1 - Introduction.m4a').exists()
        assert (Path(expected_tmp_dir) / 'Author Name - The Card Title' / '1-01_Chapter 1 - Introduction.png').exists()
        assert (Path(expected_tmp_dir) / 'Author Name - The Card Title' / '1-02_Chapter 2.m4a').exists()
        assert (Path(expected_tmp_dir) / 'Author Name - The Card Title' / '1-02_Chapter 2.png').exists()


def generate_card_page_body() -> str:
    return """
        <html><body><script id="__NEXT_DATA__" type="application/json">{
            "props": {
                "pageProps": {
                    "card": {
                        "slug": "the-card-title",
                        "title": "The Card Title",
                        "content": {
                            "chapters": [
                                {
                                    "key": "001",
                                    "title": "Chapter 1",
                                    "display": {
                                        "icon16x16": "https://example.url/card/chapter-1-icon"
                                    },
                                    "tracks": [
                                        {
                                            "key": "001",
                                            "title": "Introduction",
                                            "format": "aac",
                                            "type": "audio",
                                            "trackUrl": "https://example.url/card/chapter-1-track-1"
                                        }
                                    ]
                                },
                                {
                                    "key": "002",
                                    "title": "Chapter 2",
                                    "display": {
                                        "icon16x16": "https://example.url/card/chapter-2-icon"
                                    },
                                    "tracks": [
                                        {
                                            "key": "002",
                                            "title": "Chapter 2",
                                            "format": "aac",
                                            "type": "audio",
                                            "trackUrl": "https://example.url/card/chapter-2-track-1"
                                        }
                                    ]
                                }
                            ]
                        },
                        "metadata": {
                            "category": "stories",
                            "author": "Author Name",
                            "cover": {
                                "imageL": "https://example.url/card/cover"
                            }
                        }
                    }
                }
            }
        }</script></body></html>
    """
