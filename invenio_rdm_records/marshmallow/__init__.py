# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Schemas for marshmallow."""

# TODO:
# - Integrate into schemas package
# - Update mappings
# - Change doc type to "_doc"

from .json import BibliographicRecordSchemaV1, MetadataSchemaV1

__all__ = ('BibliographicRecordSchemaV1', 'MetadataSchemaV1')
