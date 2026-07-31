# generated in `event_model/generate`

from typing import Generic, Literal, TypeVar

# TODO: import from typing when Python 3.10 support is dropped, where a
# NamedTuple cannot yet be generic.
from typing_extensions import NamedTuple

from event_model.document_names import DocumentNames

from .datum import *  # noqa: F403
from .datum_page import *  # noqa: F403
from .event import *  # noqa: F403
from .event_descriptor import *  # noqa: F403
from .event_page import *  # noqa: F403
from .resource import *  # noqa: F403
from .run_start import *  # noqa: F403
from .run_stop import *  # noqa: F403
from .stream_datum import *  # noqa: F403
from .stream_resource import *  # noqa: F403

NameT = TypeVar("NameT")
DocT = TypeVar("DocT")


class DocWrapper(Generic[NameT, DocT], NamedTuple):
    """Named document wrapper."""

    name: NameT
    """The name each document is emitted under."""

    doc: DocT
    """The document itself."""


DocumentType = (
    type[Datum]  # noqa: F405
    | type[DatumPage]  # noqa: F405
    | type[Event]  # noqa: F405
    | type[EventDescriptor]  # noqa: F405
    | type[EventPage]  # noqa: F405
    | type[Resource]  # noqa: F405
    | type[RunStart]  # noqa: F405
    | type[RunStop]  # noqa: F405
    | type[StreamDatum]  # noqa: F405
    | type[StreamResource]  # noqa: F405
)

Document = (
    Datum  # noqa: F405
    | DatumPage  # noqa: F405
    | Event  # noqa: F405
    | EventDescriptor  # noqa: F405
    | EventPage  # noqa: F405
    | Resource  # noqa: F405
    | RunStart  # noqa: F405
    | RunStop  # noqa: F405
    | StreamDatum  # noqa: F405
    | StreamResource  # noqa: F405
)

NamedDatum = DocWrapper[Literal[DocumentNames.datum], Datum]  # noqa: F405
NamedDatumPage = DocWrapper[Literal[DocumentNames.datum_page], DatumPage]  # noqa: F405
NamedEvent = DocWrapper[Literal[DocumentNames.event], Event]  # noqa: F405
NamedEventDescriptor = DocWrapper[Literal[DocumentNames.descriptor], EventDescriptor]  # noqa: F405
NamedEventPage = DocWrapper[Literal[DocumentNames.event_page], EventPage]  # noqa: F405
NamedResource = DocWrapper[Literal[DocumentNames.resource], Resource]  # noqa: F405
NamedRunStart = DocWrapper[Literal[DocumentNames.start], RunStart]  # noqa: F405
NamedRunStop = DocWrapper[Literal[DocumentNames.stop], RunStop]  # noqa: F405
NamedStreamDatum = DocWrapper[Literal[DocumentNames.stream_datum], StreamDatum]  # noqa: F405
NamedStreamResource = DocWrapper[Literal[DocumentNames.stream_resource], StreamResource]  # noqa: F405

NamedDocument = (
    NamedDatum  # noqa: F405
    | NamedDatumPage  # noqa: F405
    | NamedEvent  # noqa: F405
    | NamedEventDescriptor  # noqa: F405
    | NamedEventPage  # noqa: F405
    | NamedResource  # noqa: F405
    | NamedRunStart  # noqa: F405
    | NamedRunStop  # noqa: F405
    | NamedStreamDatum  # noqa: F405
    | NamedStreamResource  # noqa: F405
)

ALL_DOCUMENTS: tuple[DocumentType, ...] = (
    Datum,  # noqa: F405
    DatumPage,  # noqa: F405
    Event,  # noqa: F405
    EventDescriptor,  # noqa: F405
    EventPage,  # noqa: F405
    Resource,  # noqa: F405
    RunStart,  # noqa: F405
    RunStop,  # noqa: F405
    StreamDatum,  # noqa: F405
    StreamResource,  # noqa: F405
)
