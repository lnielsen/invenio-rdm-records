# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Graz University of Technology.
# Copyright (C) 2021 TU Wien.
#
# Invenio-RDM-Records is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.

"""Service level tests for Invenio RDM Records."""

from collections import namedtuple

import pytest
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_vocabularies.proxies import current_service as vocabulary_service
from marshmallow import ValidationError

from invenio_rdm_records.proxies import current_rdm_records

RunningApp = namedtuple("RunningApp", [
    "app", "location", "superuser_identity", "resource_type_item"
])


@pytest.fixture
def running_app(app, location, superuser_identity, resource_type_item):
    """This fixture provides an app with the typically needed db data loaded.

    All of these fixtures are often needed together, so collecting them
    under a semantic umbrella makes sense.
    """
    return RunningApp(app, location, superuser_identity, resource_type_item)


#
# PIDs
#
def test_resolve_pid(running_app, es_clear, minimal_record):
    """Test the reserve function with client logged in."""
    service = current_rdm_records.records_service
    superuser_identity = running_app.superuser_identity
    # create the draft
    draft = service.create(superuser_identity, minimal_record)
    # publish the record
    record = service.publish(draft.id, superuser_identity)
    doi = record.to_dict()["pids"]["doi"]["identifier"]

    # test resolution
    resolved_record = service.resolve_pid(
        id_=doi,
        identity=superuser_identity,
        pid_type="doi"
    )
    assert resolved_record.id == record.id
    assert resolved_record.to_dict()["pids"]["doi"]["identifier"] == doi


def test_resolve_non_existing_pid(running_app, es_clear, minimal_record):
    """Test the reserve function with client logged in."""
    service = current_rdm_records.records_service
    superuser_identity = running_app.superuser_identity
    # create the draft
    draft = service.create(superuser_identity, minimal_record)
    # publish the record
    record = service.publish(draft.id, superuser_identity)
    doi = record.to_dict()["pids"]["doi"]["identifier"]

    # test resolution
    fake_doi = "10.1234/client.12345-abdce"
    with pytest.raises(PIDDoesNotExistError):
        service.resolve_pid(
            id_=fake_doi,
            identity=superuser_identity,
            pid_type="doi"
        )


def test_pid_creation_default_required(running_app, es_clear, minimal_record):
    superuser_identity = running_app.superuser_identity
    service = current_rdm_records.records_service
    minimal_record["pids"] = {}
    # create the draft
    draft = service.create(superuser_identity, minimal_record)
    # publish the record
    record = service.publish(draft.id, superuser_identity)
    published_doi = record.to_dict()["pids"]["doi"]

    assert published_doi["identifier"]
    assert published_doi["provider"] == "datacite"  # default
    assert published_doi["client"] == "datacite"  # default


def test_pid_creation_invalid_format_value_managed(
    running_app, es_clear, minimal_record
):
    superuser_identity = running_app.superuser_identity
    service = current_rdm_records.records_service
    # set the pids field
    doi = {
        "identifier": "loremipsum",
        "provider": "datacite",
        "client": "datacite"
    }
    pids = {"doi": doi}
    minimal_record["pids"] = pids
    # create the draft
    # will pass creation since validation is just reported, not hard fail
    # but it will be removed (not saved)
    draft = service.create(superuser_identity, minimal_record)
    assert draft.to_dict()["pids"] == {}


def test_pid_creation_invalid_no_value_managed(
    running_app, es_clear, minimal_record
):
    # NOTE: This use case is tricky because it will spawn two exceptions
    # Because a value is missing and is also invalid. Should consider only
    # second case.
    # {
    #   'field': 'pids.doi.value.identifier',
    #   'messages': ['Missing data for required field.']
    # }
    # {
    #   'field': 'pids._schema',
    #   'messages': [l'Invalid value for scheme doi']
    # }
    superuser_identity = running_app.superuser_identity
    service = current_rdm_records.records_service
    # set the pids field
    # no value, to get a value from the system it should not send the pid_type
    doi = {
        "provider": "datacite",
        "client": "datacite"
    }
    pids = {"doi": doi}
    minimal_record["pids"] = pids
    # create the draft
    # will pass creation since validation is just reported, not hard fail
    # but it will be removed (not saved)
    draft = service.create(superuser_identity, minimal_record)
    assert draft.to_dict()["pids"] == {}


def test_pid_creation_invalid_scheme_managed(
    running_app, es_clear, minimal_record
):
    superuser_identity = running_app.superuser_identity
    service = current_rdm_records.records_service
    # set the pids field
    lorem = {
        "identifier": "10.1234/datacite.12345",
        "provider": "datacite",
        "client": "datacite"
    }
    pids = {"lorem": lorem}
    minimal_record["pids"] = pids
    # create the draft
    # won't reach publish
    with pytest.raises(ValidationError):
        service.create(superuser_identity, minimal_record)


def test_pid_creation_valid_unmanaged(running_app, es_clear, minimal_record):
    superuser_identity = running_app.superuser_identity
    service = current_rdm_records.records_service
    # set the pids field
    doi = {
        "identifier": "10.1234/datacite.12345",
        "provider": "unmanaged",
    }
    pids = {"doi": doi}
    minimal_record["pids"] = pids
    # create the draft
    draft = service.create(superuser_identity, minimal_record)
    # publish the record
    record = service.publish(draft.id, superuser_identity)
    published_doi = record.to_dict()["pids"]["doi"]

    assert doi["identifier"] == published_doi["identifier"]
    assert doi["provider"] == published_doi["provider"]


def test_pid_creation_invalid_format_unmanaged(
    running_app, es_clear, minimal_record
):
    superuser_identity = running_app.superuser_identity
    service = current_rdm_records.records_service
    # set the pids field
    doi = {
        "identifier": "loremipsum",
        "provider": "unmanaged",
    }
    pids = {"doi": doi}
    minimal_record["pids"] = pids
    # create the draft
    # will pass creation since validation is just reported, not hard fail
    # but it will be removed (not saved)
    draft = service.create(superuser_identity, minimal_record)
    assert draft.to_dict()["pids"] == {}


def test_pid_creation_invalid_scheme_unmanaged(
    running_app, es_clear, minimal_record
):
    superuser_identity = running_app.superuser_identity
    service = current_rdm_records.records_service
    # set the pids field
    lorem = {
        "identifier": "10.1234/datacite.12345",
        "provider": "unmanaged",
    }
    pids = {"lorem": lorem}
    minimal_record["pids"] = pids
    # create the draft
    # won't reach publish
    with pytest.raises(ValidationError):
        service.create(superuser_identity, minimal_record)


def test_minimal_draft_creation(running_app, es_clear, minimal_record):
    superuser_identity = running_app.superuser_identity
    service = current_rdm_records.records_service

    record_item = service.create(superuser_identity, minimal_record)
    record_dict = record_item.to_dict()

    assert record_dict["metadata"]["resource_type"] == {
        'id': 'image-photo',
        'title': {'en': 'Photo'}
    }


def test_draft_w_languages_creation(
        running_app, es_clear, minimal_record, lang):
    superuser_identity = running_app.superuser_identity
    service = current_rdm_records.records_service
    minimal_record["metadata"]["languages"] = [{
        "id": "eng",
    }]

    record_item = service.create(superuser_identity, minimal_record)
    record_dict = record_item.to_dict()

    assert record_dict["metadata"]["languages"] == [{
        'id': 'eng',
        'title': {'en': 'English', 'da': 'Engelsk'}
    }]
