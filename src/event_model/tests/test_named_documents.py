from typing import get_args

import pytest

import event_model
from event_model import DocumentNames
from event_model.documents import (
    ALL_DOCUMENTS,
    Datum,
    DatumPage,
    DocWrapper,
    Event,
    EventDescriptor,
    EventPage,
    NamedDocument,
    Resource,
    RunStart,
    RunStop,
    StreamDatum,
    StreamResource,
)
from event_model.documents.stream_datum import StreamRange

# Written out independently of the generator so that a misaligned name would be
# caught rather than reproduced.
EXPECTED_PAIRS = {
    DocumentNames.datum: Datum,
    DocumentNames.datum_page: DatumPage,
    DocumentNames.descriptor: EventDescriptor,
    DocumentNames.event: Event,
    DocumentNames.event_page: EventPage,
    DocumentNames.resource: Resource,
    DocumentNames.start: RunStart,
    DocumentNames.stop: RunStop,
    DocumentNames.stream_datum: StreamDatum,
    DocumentNames.stream_resource: StreamResource,
}


def named_document_pairs() -> dict[DocumentNames, type]:
    """Document class keyed by name, taken apart from ``NamedDocument``."""
    pairs = {}
    for named_document in get_args(NamedDocument):
        name_literal, document_class = get_args(named_document)
        (name,) = get_args(name_literal)
        pairs[name] = document_class
    return pairs


def compose_all_documents(tmp_path) -> list:
    """One ``(name, doc)`` pair for every kind of document a run can emit."""
    run_bundle = event_model.compose_run()
    descriptor_bundle = run_bundle.compose_descriptor(
        data_keys={
            "motor": {"shape": [], "dtype": "number", "source": "..."},
            "image": {
                "shape": [512, 512],
                "dtype": "number",
                "source": "...",
                "external": "FILESTORE:",
            },
        },
        name="primary",
    )
    resource_bundle = run_bundle.compose_resource(
        spec="TIFF", root=str(tmp_path), resource_path="stack.tiff", resource_kwargs={}
    )
    assert run_bundle.compose_stream_resource is not None
    stream_resource_bundle = run_bundle.compose_stream_resource(
        mimetype="image/tiff",
        uri="file://localhost" + str(tmp_path) + "/test_streams",
        data_key="det1",
        parameters={},
    )
    datum_doc = resource_bundle.compose_datum(datum_kwargs={"slice": 5})
    event_doc = descriptor_bundle.compose_event(
        data={"motor": 0, "image": datum_doc["datum_id"]},
        timestamps={"motor": 0, "image": 0},
        filled={"image": False},
        seq_num=1,
    )
    stream_datum_doc = stream_resource_bundle.compose_stream_datum(
        StreamRange(start=0, stop=1), StreamRange(start=0, stop=1)
    )
    return [
        (DocumentNames.start, run_bundle.start_doc),
        (DocumentNames.descriptor, descriptor_bundle.descriptor_doc),
        (DocumentNames.resource, resource_bundle.resource_doc),
        (DocumentNames.stream_resource, stream_resource_bundle.stream_resource_doc),
        (DocumentNames.datum, datum_doc),
        (DocumentNames.datum_page, event_model.pack_datum_page(datum_doc)),
        (DocumentNames.event, event_doc),
        (DocumentNames.event_page, event_model.pack_event_page(event_doc)),
        (DocumentNames.stream_datum, stream_datum_doc),
        (DocumentNames.stop, run_bundle.compose_stop()),
    ]


def expected_routing(composed: list) -> dict:
    """The field each routing branch reads, keyed by the name that selects it.

    Taken from the composed documents themselves so that a branch reading the
    right field off the wrong document fails.
    """
    docs = dict(composed)
    return {
        DocumentNames.start: docs[DocumentNames.start]["uid"],
        DocumentNames.descriptor: sorted(docs[DocumentNames.descriptor]["data_keys"]),
        DocumentNames.resource: docs[DocumentNames.resource]["resource_path"],
        DocumentNames.stream_resource: docs[DocumentNames.stream_resource]["uri"],
        DocumentNames.datum: docs[DocumentNames.datum]["datum_id"],
        DocumentNames.datum_page: docs[DocumentNames.datum_page]["datum_id"],
        DocumentNames.event: docs[DocumentNames.event]["seq_num"],
        DocumentNames.event_page: docs[DocumentNames.event_page]["seq_num"],
        DocumentNames.stream_datum: docs[DocumentNames.stream_datum]["seq_nums"],
        DocumentNames.stop: docs[DocumentNames.stop]["exit_status"],
    }


def assert_every_document_was_routed(seen: dict, composed: list) -> None:
    assert set(seen) == set(named_document_pairs())
    assert seen == expected_routing(composed)
    assert seen[DocumentNames.descriptor] == ["image", "motor"]
    assert seen[DocumentNames.resource] == "stack.tiff"
    assert seen[DocumentNames.event] == 1
    assert seen[DocumentNames.event_page] == [1]
    assert seen[DocumentNames.datum_page] == [seen[DocumentNames.datum]]
    assert seen[DocumentNames.stop] == "success"


def test_named_document_pairs_each_name_with_its_document():
    assert named_document_pairs() == EXPECTED_PAIRS


def test_named_document_has_an_alias_per_document():
    pairs = named_document_pairs()
    assert len(get_args(NamedDocument)) == len(ALL_DOCUMENTS)
    for document_class in ALL_DOCUMENTS:
        alias = getattr(event_model.documents, f"Named{document_class.__name__}")
        assert alias in get_args(NamedDocument)
        (name,) = (name for name, paired in pairs.items() if paired is document_class)
        assert get_args(alias) == (get_args(alias)[0], document_class)
        assert name in set(DocumentNames)


def test_composed_documents_match_the_name_they_are_emitted_under(tmp_path):
    """Every composed document validates against the schema its name selects."""
    pairs = named_document_pairs()
    composed = compose_all_documents(tmp_path)

    for name, doc in composed:
        assert name in set(DocumentNames)
        assert set(doc) <= set(pairs[name].__annotations__)
        validator = event_model.schema_validators[event_model.DocumentNames(name)]
        validator.validate(doc)

    assert {name for name, _ in composed} == set(pairs)


def test_named_documents_are_keyed_on_document_names_members():
    """Each alias is keyed on a ``DocumentNames`` member, not a bare string."""
    for name in named_document_pairs():
        assert isinstance(name, DocumentNames)
        assert name == str(name)


def route_by_if_else(named_document: NamedDocument, seen: dict) -> None:
    """Route through an ``if``/``elif`` chain over the wrapped name."""
    if named_document.name == DocumentNames.start:
        seen[DocumentNames.start] = named_document.doc["uid"]
    elif named_document.name == DocumentNames.descriptor:
        seen[DocumentNames.descriptor] = sorted(named_document.doc["data_keys"])
    elif named_document.name == DocumentNames.resource:
        seen[DocumentNames.resource] = named_document.doc["resource_path"]
    elif named_document.name == DocumentNames.stream_resource:
        seen[DocumentNames.stream_resource] = named_document.doc["uri"]
    elif named_document.name == DocumentNames.datum:
        seen[DocumentNames.datum] = named_document.doc["datum_id"]
    elif named_document.name == DocumentNames.datum_page:
        seen[DocumentNames.datum_page] = named_document.doc["datum_id"]
    elif named_document.name == DocumentNames.event:
        seen[DocumentNames.event] = named_document.doc["seq_num"]
    elif named_document.name == DocumentNames.event_page:
        seen[DocumentNames.event_page] = named_document.doc["seq_num"]
    elif named_document.name == DocumentNames.stream_datum:
        seen[DocumentNames.stream_datum] = named_document.doc["seq_nums"]
    elif named_document.name == DocumentNames.stop:
        seen[DocumentNames.stop] = named_document.doc["exit_status"]
    else:
        raise AssertionError(f"{named_document.name} fell through the chain")


def route_by_match_case(named_document: NamedDocument, seen: dict) -> None:
    """Route through match-case value patterns over the wrapped name."""
    match named_document.name:
        case DocumentNames.start:
            seen[DocumentNames.start] = named_document.doc["uid"]
        case DocumentNames.descriptor:
            seen[DocumentNames.descriptor] = sorted(named_document.doc["data_keys"])
        case DocumentNames.resource:
            seen[DocumentNames.resource] = named_document.doc["resource_path"]
        case DocumentNames.stream_resource:
            seen[DocumentNames.stream_resource] = named_document.doc["uri"]
        case DocumentNames.datum:
            seen[DocumentNames.datum] = named_document.doc["datum_id"]
        case DocumentNames.datum_page:
            seen[DocumentNames.datum_page] = named_document.doc["datum_id"]
        case DocumentNames.event:
            seen[DocumentNames.event] = named_document.doc["seq_num"]
        case DocumentNames.event_page:
            seen[DocumentNames.event_page] = named_document.doc["seq_num"]
        case DocumentNames.stream_datum:
            seen[DocumentNames.stream_datum] = named_document.doc["seq_nums"]
        case DocumentNames.stop:
            seen[DocumentNames.stop] = named_document.doc["exit_status"]
        case _:
            raise AssertionError(f"{named_document.name} matched no case")


def route_by_match_sequence(named_document: NamedDocument, seen: dict) -> None:
    """Route by unpacking the wrapper as the two element sequence it is."""
    match named_document:
        case (DocumentNames.start, doc):
            seen[DocumentNames.start] = doc["uid"]
        case (DocumentNames.descriptor, doc):
            seen[DocumentNames.descriptor] = sorted(doc["data_keys"])
        case (DocumentNames.resource, doc):
            seen[DocumentNames.resource] = doc["resource_path"]
        case (DocumentNames.stream_resource, doc):
            seen[DocumentNames.stream_resource] = doc["uri"]
        case (DocumentNames.datum, doc):
            seen[DocumentNames.datum] = doc["datum_id"]
        case (DocumentNames.datum_page, doc):
            seen[DocumentNames.datum_page] = doc["datum_id"]
        case (DocumentNames.event, doc):
            seen[DocumentNames.event] = doc["seq_num"]
        case (DocumentNames.event_page, doc):
            seen[DocumentNames.event_page] = doc["seq_num"]
        case (DocumentNames.stream_datum, doc):
            seen[DocumentNames.stream_datum] = doc["seq_nums"]
        case (DocumentNames.stop, doc):
            seen[DocumentNames.stop] = doc["exit_status"]
        case _:
            raise AssertionError(f"{named_document.name} matched no case")


def route_by_match_guard(named_document: NamedDocument, seen: dict) -> None:
    """Route through match-case guards comparing the wrapped name.

    Each guard reads the name off the wrapper rather than a captured binding,
    which is what lets the guard narrow the document alongside it.
    """
    match named_document:
        case _ if named_document.name == DocumentNames.start:
            seen[DocumentNames.start] = named_document.doc["uid"]
        case _ if named_document.name == DocumentNames.descriptor:
            seen[DocumentNames.descriptor] = sorted(named_document.doc["data_keys"])
        case _ if named_document.name == DocumentNames.resource:
            seen[DocumentNames.resource] = named_document.doc["resource_path"]
        case _ if named_document.name == DocumentNames.stream_resource:
            seen[DocumentNames.stream_resource] = named_document.doc["uri"]
        case _ if named_document.name == DocumentNames.datum:
            seen[DocumentNames.datum] = named_document.doc["datum_id"]
        case _ if named_document.name == DocumentNames.datum_page:
            seen[DocumentNames.datum_page] = named_document.doc["datum_id"]
        case _ if named_document.name == DocumentNames.event:
            seen[DocumentNames.event] = named_document.doc["seq_num"]
        case _ if named_document.name == DocumentNames.event_page:
            seen[DocumentNames.event_page] = named_document.doc["seq_num"]
        case _ if named_document.name == DocumentNames.stream_datum:
            seen[DocumentNames.stream_datum] = named_document.doc["seq_nums"]
        case _ if named_document.name == DocumentNames.stop:
            seen[DocumentNames.stop] = named_document.doc["exit_status"]
        case _:
            raise AssertionError(f"{named_document.name} matched no case")


@pytest.mark.parametrize(
    "route",
    [
        route_by_if_else,
        route_by_match_case,
        route_by_match_sequence,
        route_by_match_guard,
    ],
    ids=["if_else", "match_case", "match_sequence", "match_guard"],
)
def test_callback_routes_named_documents(route, tmp_path):
    """Every way of discriminating on the wrapped name routes every document."""
    seen: dict = {}

    composed = compose_all_documents(tmp_path)
    for name, doc in composed:
        route(DocWrapper(name, doc), seen)

    assert_every_document_was_routed(seen, composed)


def test_document_router_emits_named_documents(tmp_path):
    """An unchanged two-argument callback still receives each document by name.

    The router emits a name and a document as two arguments, so a caller pairs
    them up itself. A wrapper built from the pair compares equal to it.
    """
    pairs = named_document_pairs()
    collected: list = []

    def collect(name, doc):
        collected.append((name, doc))

    router = event_model.DocumentRouter(emit=collect)
    composed = compose_all_documents(tmp_path)
    for name, doc in composed:
        router.emit(name, doc)

    assert len(collected) == len(composed)
    for pair in collected:
        assert len(pair) == 2
        name, doc = pair
        assert DocWrapper(name, doc) == pair
        assert set(doc) <= set(pairs[name].__annotations__)
