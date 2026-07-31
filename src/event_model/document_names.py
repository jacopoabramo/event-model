import sys

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from ._strenum_backport import StrEnum


class DocumentNames(StrEnum):
    """StrEnum of the names of all documents in the event model."""

    stop = "stop"
    start = "start"
    descriptor = "descriptor"
    event = "event"
    datum = "datum"
    resource = "resource"
    event_page = "event_page"
    datum_page = "datum_page"
    stream_resource = "stream_resource"
    stream_datum = "stream_datum"
    bulk_datum = "bulk_datum"  # deprecated
    bulk_events = "bulk_events"  # deprecated


__all__ = ["DocumentNames"]
