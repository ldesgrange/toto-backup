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


def get_project_root() -> Path:
    return Path(__file__).parent.parent


def get_dummy_file() -> Path:
    # “empty.bin” was generated using: `touch empty.bin`
    return get_project_root() / 'tests/data/dummy.bin'


def get_dummy_m4a_file() -> Path:
    # “empty.m4a” was generated using: `ffmpeg -f lavfi -t 1 -i anullsrc -c:a aac -shortest empty.m4a`
    return get_project_root() / 'tests/data/empty.m4a'


def get_dummy_mp3_file() -> Path:
    # “empty.mp3” was generated using: `ffmpeg -f lavfi -t 1 -i anullsrc -c:a mp3 -shortest empty.mp3`
    return get_project_root() / 'tests/data/empty.mp3'


def get_dummy_png_file() -> Path:
    # “empty.png” was generated using: `convert -size 16x16 xc:white empty.png`
    return get_project_root() / 'tests/data/empty.png'
