# DUGSeis
# Copyright (C) 2021 DUGSeis Authors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Utility functionality for the waveform handler class.
"""

import hashlib
import pathlib
import typing


def compute_sha256_hash_for_file(
    filename: pathlib.Path,
    max_bytes: typing.Optional[int] = None,
) -> str:
    """
    Compute the sha256 hash for a file.

    Args:
        filename: Path to the file.
        max_bytes: Only use the first X bytes if specified. Useful when
            hashing really large files and when it is reasonable to expect
            the the first few MB uniquely identify the file.
    """
    h = hashlib.sha256()
    checked_bytes = 0
    with open(filename, "rb") as fh:
        while True:
            d = fh.read(65536)
            checked_bytes += len(d)
            if not d:
                break
            h.update(d)
            # Early break.
            if max_bytes is not None and checked_bytes >= max_bytes:
                break
    return str(h.hexdigest())
