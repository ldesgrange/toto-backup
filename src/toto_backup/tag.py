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
from pathlib import Path

import structlog
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, Encoding, APIC, PictureType
from mutagen.mp4 import MP4Tags, MP4Cover

logger = structlog.stdlib.get_logger()


class Metadata:
    author: str | None = None
    title: str | None = None
    track_name: str | None = None
    track_number: int | None = None
    track_total: int | None = None
    disc_number: int | None = None
    disc_total: int | None = None
    cover_file: Path | None = None
    card_url: str | None = None


def tag_track(track_file: Path, track_metadata: Metadata) -> None:
    if track_file.suffix == '.m4a':
        add_mp4_tags(track_file, track_metadata)
    elif track_file.suffix == '.mp3':
        add_id3_tags(track_file, track_metadata)


def add_mp4_tags(track_file: Path, track_metadata: Metadata) -> None:
    tags = MP4Tags()
    # See https://mutagen.readthedocs.io/en/latest/api/mp4.html#mutagen.mp4.MP4Tags
    if track_metadata.author:
        tags['\xa9ART'] = track_metadata.author
        tags['aART'] = track_metadata.author
    if track_metadata.title:
        tags['\xa9alb'] = track_metadata.title
    if track_metadata.track_name:
        tags['\xa9nam'] = track_metadata.track_name
    tags['\xa9gen'] = 'Audiobook'
    if track_metadata.card_url:
        tags['\xa9cmt'] = track_metadata.card_url
    if track_metadata.track_number and track_metadata.track_total:
        tags['trkn'] = [(track_metadata.track_number, track_metadata.track_total)]
    if track_metadata.disc_number and track_metadata.disc_total:
        tags['disk'] = [(track_metadata.disc_number, track_metadata.disc_total)]
    if track_metadata.cover_file:
        with open(track_metadata.cover_file, 'rb') as icon_file:
            # Determine file format.
            image_format = None
            if track_metadata.cover_file.suffix == '.png':
                image_format = MP4Cover.FORMAT_PNG
            elif track_metadata.cover_file.suffix == '.jpg':
                image_format = MP4Cover.FORMAT_JPEG
            # Add cover.
            if image_format is not None:
                tags['covr'] = [MP4Cover(icon_file.read(), imageformat=image_format)]
            else:
                logger.warning(f'Unsupported cover file format: {track_metadata.cover_file}')
    # Save tags to file.
    tags.save(track_file)


def add_id3_tags(track_file: Path, track_metadata: Metadata) -> None:
    tags = EasyID3(track_file)
    if track_metadata.author:
        tags['artist'] = track_metadata.author
        tags['albumartist'] = track_metadata.author
    if track_metadata.title:
        tags['album'] = track_metadata.title
    if track_metadata.track_name:
        tags['title'] = track_metadata.track_name
    tags['genre'] = 'Audiobook'
    if track_metadata.card_url:
        tags['website'] = track_metadata.card_url
    if track_metadata.track_number and track_metadata.track_total:
        tags['tracknumber'] = f'{track_metadata.track_number}/{track_metadata.track_total}'
    if track_metadata.disc_number and track_metadata.disc_total:
        tags['discnumber'] = f'{track_metadata.disc_number}/{track_metadata.disc_total}'
    # Save tags to file.
    tags.save()

    # Add cover.
    if track_metadata.cover_file:
        with open(track_metadata.cover_file, 'rb') as icon_file:
            # Determine file format.
            image_format = None
            if track_metadata.cover_file.suffix == '.png':
                image_format = 'image/png'
            elif track_metadata.cover_file.suffix == '.jpg':
                image_format = 'image/jpeg'
            # Add cover.
            if image_format is not None:
                tags_for_cover = ID3(track_file)
                tags_for_cover.add(
                    APIC(
                        encoding=Encoding.UTF8,
                        mime=image_format,
                        type=PictureType.ILLUSTRATION,
                        data=icon_file.read(),
                    )
                )
                tags_for_cover.save()
            else:
                logger.warning(f'Unsupported cover file format: {track_metadata.cover_file}')
