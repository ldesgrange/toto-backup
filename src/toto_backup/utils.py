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
import json
import unicodedata
from http import HTTPStatus
from mimetypes import guess_extension
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import click
import requests
import structlog
from bs4 import BeautifulSoup, Tag
from puremagic import magic_file, PureError
from requests.structures import CaseInsensitiveDict

logger = structlog.stdlib.get_logger()


def get_mime_type(headers: CaseInsensitiveDict[str]) -> str | None:
    mime_type = headers.get('Content-Type', '').partition(';')[0].strip()

    if mime_type == 'audio/x-m4a':
        mime_type = 'audio/mp4'

    return mime_type or None


def get_extension(mime_type: str | None, file: Path | None) -> str | None:
    extension = None

    if mime_type:
        extension = guess_extension(mime_type)

    # Some extensions are meaningless, ignore them.
    if extension in ['.bin']:
        extension = None

    if not extension and file:
        try:
            results = magic_file(file)
            logger.debug(f'File {file} has MIME type {results}.')
            if results:
                # Return the first match.
                extension = results[0].extension
        except PureError:
            # Invalid file, ignore it.
            pass

    return extension


def download_content(url: str) -> tuple[Path, str | None]:
    """
    Downloads content from a given URL and saves it to a temporary file. Provides the file
    path and MIME type of the content as output.

    :param url: The URL of the resource to download.
    :return: A tuple containing the path to the downloaded temporary file and the MIME type
        of the resource.
    """
    response = requests.get(url)
    response.raise_for_status()

    with NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(response.content)

    return Path(temp_file.name), get_mime_type(response.headers)


def fetch_page(url: str) -> str | None:
    response = requests.get(url)
    if response.status_code != HTTPStatus.OK:
        logger.error('Error while fetching page: %d', response.status_code)
        return None
    return response.text


def find_data(html: str) -> Any:
    soup = BeautifulSoup(html, 'html.parser')
    tag = soup.find('script', id='__NEXT_DATA__')
    if not tag or not isinstance(tag, Tag) or not tag.string:
        logger.error('Error while parsing HTML data.')
        return None
    try:
        return json.loads(tag.string)
    except TypeError:
        logger.exception('Error while parsing JSON data.')
        return None


def should_overwrite_directory(directory: Path) -> bool:
    """
    Prompt the user to confirm overwriting an existing directory.
    """
    return click.confirm(f'Directory “{directory}” already exists, overwrite?', default=False, abort=False)


def similar_strings(str1: str, str2: str) -> bool:
    return _normalize(str1) == _normalize(str2)


PUNCTUATION_MAP = {
    '‘': "'",  # noqa: RUF001
    '’': "'",  # noqa: RUF001
    '‚': "'",  # noqa: RUF001
    '‛': "'",  # noqa: RUF001
    '“': '"',
    '”': '"',
    '«': '"',
    '»': '"',
    '„': '"',
    '‟': '"',
    '‐': '-',  # noqa: RUF001
    '-': '-',
    '‒': '-',  # noqa: RUF001
    '–': '-',  # noqa: RUF001
    '—': '-',
    '―': '-',
    '…': '...',
}


def _normalize(value: str) -> str:
    # Replace fancy punctuation with ASCII equivalents.
    value = ''.join(PUNCTUATION_MAP.get(character, character) for character in value)
    # Decompose accents (NFKD breaks é into e + diacritic).
    value = unicodedata.normalize('NFKD', value)
    # Remove diacritics (any "combining" mark).
    value = ''.join(character for character in value if not unicodedata.combining(character))
    # Normalize again to recombine (NFKC for compatibility chars like ligatures).
    value = unicodedata.normalize('NFKC', value)
    # Case-fold for case-insensitive comparison.
    return value.casefold()


def format_base_filename(
    disc_number: int, disc_total: int, track_number: int, track_total: int, track_name: str
) -> str:
    formatted_disc_number = str(disc_number).zfill(len(str(disc_total)))
    formatted_track_number = str(track_number).zfill(max([2, len(str(track_total))]))
    return f'{formatted_disc_number}-{formatted_track_number}_{track_name}'
