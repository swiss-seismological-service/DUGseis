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