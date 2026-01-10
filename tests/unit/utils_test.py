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
import os
from pathlib import Path

import click
import pytest
import responses
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner
from requests import HTTPError
from requests.structures import CaseInsensitiveDict

from toto_backup.utils import (
    get_extension,
    get_mime_type,
    download_content,
    fetch_page,
    find_data,
    should_overwrite_directory,
    similar_strings,
    format_base_filename,
    deep_get,
)
from utils import get_dummy_m4a_file, get_dummy_file

logger = logging.getLogger(__name__)


def test_get_mime_type_should_return_mime_type_from_http_headers():
    assert get_mime_type(CaseInsensitiveDict({})) is None
    assert get_mime_type(CaseInsensitiveDict({'content-type': ''})) is None
    assert get_mime_type(CaseInsensitiveDict({'content-type': 'foo/bar'})) == 'foo/bar'
    assert get_mime_type(CaseInsensitiveDict({'Content-Type': 'audio/mpeg'})) == 'audio/mpeg'
    assert get_mime_type(CaseInsensitiveDict({'CONTENT-TYPE': 'text/html; charset=utf-8'})) == 'text/html'


def test_get_mime_type_should_fix_known_problematic_mime_types():
    assert get_mime_type(CaseInsensitiveDict({'Content-Type': 'audio/x-m4a'})) == 'audio/mp4'


def test_get_extension_should_return_extension_from_mime_type():
    assert get_extension(None, None) is None
    assert get_extension('', None) is None
    assert get_extension('foo/bar', None) is None
    assert get_extension('application/octet-stream', None) is None
    assert get_extension('audio/mp4', None) == '.m4a'
    assert get_extension('audio/mpeg', None) == '.mp3'
    assert get_extension('audio/mpeg', get_dummy_m4a_file()) == '.mp3'


def test_get_extension_should_return_extension_from_magic_bytes():
    assert get_extension(None, None) is None
    assert get_extension(None, get_dummy_file()) is None
    assert get_extension(None, get_dummy_m4a_file()) == '.m4a'


@responses.activate
def test_download_content_should_create_file():
    url = 'https://example.com/track1.mp3'
    # Mock HTTP response.
    responses.add(
        responses.Response(
            method='GET',
            url=url,
            status=200,
            content_type='audio/mpeg',
            body=b'content',
        )
    )

    downloaded_file, mime_type = download_content(url)
    assert downloaded_file.exists()
    assert downloaded_file.read_bytes() == b'content'
    assert mime_type == 'audio/mpeg'


@responses.activate
def test_download_content_should_raise_on_http_error():
    url = 'https://example.com/track1.mp3'
    # Mock HTTP response.
    responses.add(
        responses.Response(
            method='GET',
            url=url,
            status=404,
            content_type='text/html',
            body='404 Not Found',
        )
    )

    with pytest.raises(HTTPError) as e:
        download_content(url)
    assert str(e.value) == '404 Client Error: Not Found for url: https://example.com/track1.mp3'


@responses.activate
def test_fetch_page_should_return_html_content():
    url = 'https://example.com/card.html'
    # Mock HTTP response.
    responses.add(
        responses.Response(
            method='GET',
            url=url,
            status=200,
            content_type='text/html',
            body='<html><body>content</body></html>',
        )
    )

    assert fetch_page(url) == '<html><body>content</body></html>'


@responses.activate
def test_fetch_page_should_return_none_when_http_error_occurs():
    url = 'https://example.com/card.html'
    # Mock HTTP response.
    responses.add(
        responses.Response(
            method='GET',
            url=url,
            status=404,
            content_type='text/html',
            body='<html><body>404 Not found</body></html>',
        )
    )

    assert fetch_page(url) is None


def test_find_data_should_return_json_data_as_dict():
    assert find_data('<html><script id="__NEXT_DATA__">{"foo": "bar"}</script></html>') == {'foo': 'bar'}


def test_find_data_should_return_none_when_json_not_found():
    assert find_data('') is None
    assert find_data('<html><script id="foo"></script></html>') is None
    assert find_data('<html><script id="__NEXT_DATA__"></script></html>') is None


def test_should_overwrite_directory_should_ask_user(caplog: LogCaptureFixture):
    caplog.set_level(10000)
    runner = CliRunner()

    @click.command()
    def create() -> None:
        if should_overwrite_directory(Path('some') / 'dir'):
            click.echo('Returned True')
        else:
            click.echo('Returned False')

    # Reject overwriting.
    result = runner.invoke(create, input='n')
    assert result.output == f'Directory “some{os.sep}dir” already exists, overwrite? [y/N]: n\nReturned False\n'

    # Accept overwriting.
    result = runner.invoke(create, input='y')
    assert result.output == f'Directory “some{os.sep}dir” already exists, overwrite? [y/N]: y\nReturned True\n'

    caplog.set_level(logging.NOTSET)


def test_similar_strings():
    assert similar_strings('foo', 'bar') is False

    assert similar_strings('', '') is True
    assert similar_strings('foo', 'FOO') is True
    assert similar_strings('FoO', 'fOO') is True
    assert similar_strings('café', 'cafe\u0301') is True
    assert similar_strings('café', 'cafe') is True
    assert similar_strings('ﬁ', 'fi') is True
    assert similar_strings('straße', 'STRASSE') is True
    assert similar_strings('‘foo’', "'foo'") is True  # noqa: RUF001
    assert similar_strings('“foo”', '"foo"') is True
    assert similar_strings('« foo »', '" foo "') is True  # noqa: RUF001
    assert similar_strings('« foo »', '“ foo ”') is True  # noqa: RUF001


def test_format_base_filename():
    assert format_base_filename(1, 1, 1, 1, 'xxx') == '1-01_xxx'
    assert format_base_filename(1, 10, 1, 10, 'xxx') == '01-01_xxx'
    assert format_base_filename(1, 100, 1, 100, 'xxx') == '001-001_xxx'


def test_deep_get():
    assert deep_get({}, []) == {}
    assert deep_get({}, ['foo', 'bar']) is None
    assert deep_get({'foo': 'bar'}, ['foo']) == 'bar'
    assert deep_get({'foo': {'bar': 'baz'}}, ['foo']) == {'bar': 'baz'}
    assert deep_get({'foo': {'bar': 'baz'}}, ['foo', 'bar']) == 'baz'
