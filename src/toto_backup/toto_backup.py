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
import sys
from pathlib import Path
from uuid import uuid4

import click
import structlog
from pathvalidate import sanitize_filename
from requests import HTTPError

from toto_backup.card import parse_data, InvalidDataError, Card
from toto_backup.tag import tag_track, Metadata
from toto_backup.utils import (
    download_content,
    get_extension,
    fetch_page,
    find_data,
    should_overwrite_directory,
    similar_strings,
    format_base_filename,
)

structlog.stdlib.recreate_defaults(log_level=logging.INFO)
logger = structlog.stdlib.get_logger()

ERROR_INVALID_URL = 10
ERROR_DATA_NOT_FOUND = 11
ERROR_INVALID_DATA = 12
ERROR_DIRECTORY_ALREADY_EXISTS = 13


@click.command()
@click.argument('url')
def main(url: str) -> None:
    """Simple backup tool for your Yoto cards.

    URL is the URL of the Yoto card to back up (e.g., https://yoto.io/XXXXX?ABCDEFGHIJKL=MNOPQRSTUVWXY).
    """
    # Fetch card HTML page.
    print(f'Fetching page at: {url}')
    page_content = fetch_page(url)
    if not page_content:
        sys.exit(ERROR_INVALID_URL)
    # Extract JSON content out of it.
    print('Find data…')
    data = find_data(page_content)
    if not data:
        sys.exit(ERROR_DATA_NOT_FOUND)
    # Convert JSON content to a Card object.
    try:
        card = parse_data(data)
    except InvalidDataError:
        logger.exception('Error while parsing data. This card may not be supported.')
        sys.exit(ERROR_INVALID_DATA)
    # Create a directory to download tracks into.
    card_directory = create_card_directory(Path.cwd(), card)
    if not card_directory:
        logger.warning('Aborted!')
        sys.exit(ERROR_DIRECTORY_ALREADY_EXISTS)
    # Download card cover art.
    print('Downloading card cover…')
    if download_and_move_content(card.cover_url, card_directory / 'cover') is None:
        logger.warning('Failed to download card cover.')
    # Download tracks and their cover arts.
    successful_track_count, failed_track_count = download_tracks(card, card_directory, url)

    # Work is finished, exit.
    print(
        f'Card backup completed, {successful_track_count} tracks backed up successfully, {failed_track_count} failed.'
    )
    sys.exit()


if __name__ == '__main__':
    main()


def create_card_directory(parent_directory: Path, card: Card) -> Path | None:
    print('Creating card directory…')
    card_directory_name = ' - '.join(filter(None, [card.author, card.title]))
    if not card_directory_name:
        card_directory_name = f'card-backup-{uuid4()}'
    sanitized_card_directory_name = sanitize_filename(card_directory_name, validate_after_sanitize=True)
    card_directory = parent_directory / sanitized_card_directory_name
    if card_directory.exists():
        if should_overwrite_directory(card_directory):
            shutil.rmtree(card_directory)
        else:
            return None
    card_directory.mkdir()
    return card_directory


def download_and_move_content(url: str, destination: Path) -> Path | None:
    try:
        temporary_file, mime_type = download_content(url)
        extension = get_extension(mime_type, temporary_file) or ''
        final_destination = destination.with_name(f'{destination.name}{extension}')
        shutil.move(temporary_file, final_destination)
    except HTTPError:
        return None
    else:
        return final_destination


def download_tracks(card, card_directory, url) -> tuple[int, int]:
    successful_track_download_count = 0
    failed_track_download_count = 0
    print('Downloading tracks…')
    disc_number = 1
    disc_total = 1
    track_number = 0
    for chapter in card.chapters:
        for track in chapter.tracks:
            track_number += 1

            if similar_strings(chapter.title, track.title):
                track_name = chapter.title
            else:
                track_name = f'{chapter.title} - {track.title}'

            base_filename = format_base_filename(disc_number, disc_total, track_number, card.track_total, track_name)

            # Download icon.
            icon_file = download_and_move_content(chapter.icon_url, card_directory / base_filename)
            if icon_file is None:
                logger.warning(f'Icon not found for track {track_number}/{card.track_total}.')

            # Download track.
            track_file = download_and_move_content(track.url, card_directory / base_filename)
            if track_file is not None:
                # Tag file.
                track_metadata = Metadata()
                track_metadata.author = card.author
                track_metadata.title = card.title
                track_metadata.track_name = track_name
                track_metadata.track_number = track_number
                track_metadata.track_total = card.track_total
                track_metadata.disc_number = disc_number
                track_metadata.disc_total = disc_total
                track_metadata.cover_file = icon_file
                track_metadata.card_url = url
                tag_track(track_file, track_metadata)

                print(f'Track {track_number}/{card.track_total} successfully downloaded to {track_file}')
                successful_track_download_count += 1
            else:
                logger.exception(f'Failed to download track {track_number}/{card.track_total}')
                failed_track_download_count += 1
    return successful_track_download_count, failed_track_download_count
