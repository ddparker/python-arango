from __future__ import absolute_import, unicode_literals

from arango.api import api_method
from arango.collections.base import BaseCollection
from arango.exceptions import *
from arango.request import Request
from arango.utils import HTTP_OK


class VertexCollection(BaseCollection):
    """ArangoDB vertex collection.

    A vertex collection consists of vertex documents. It is uniquely identified
    by its name, which must consist only of alphanumeric characters, hyphen and
    the underscore characters. Vertex collections share their namespace with
    other types of collections.

    The documents in a vertex collection are fully accessible from a standard
    collection. Managing documents through a vertex collection, however, adds
    additional guarantees: all modifications are executed in transactions and
    if a vertex is deleted all connected edges are also deleted.

    :param connection: ArangoDB database connection
    :type connection: arango.connection.Connection
    :param graph_name: the name of the graph
    :type graph_name: str
    :param name: the name of the vertex collection
    :type name: str
    """

    def __init__(self, connection, graph_name, name):
        super(VertexCollection, self).__init__(connection, name)
        self._graph_name = graph_name

    def __repr__(self):
        return (
            '<ArangoDB vertex collection "{}" in graph "{}">'
            .format(self._name, self._graph_name)
        )

    @property
    def graph_name(self):
        """Return the name of the graph.

        :returns: the name of the graph
        :rtype: str
        """
        return self._graph_name

    @api_method
    def get(self, key, rev=None):
        """Fetch a document by key from the vertex collection.

        :param key: the document key
        :type key: str
        :param rev: the document revision to be compared against the revision
            of the target document
        :type rev: str | None
        :returns: the vertex document or None if not found
        :rtype: dict | None
        :raises arango.exceptions.DocumentRevisionError: if the given revision
            does not match the revision of the target document
        :raises arango.exceptions.DocumentGetError: if the document cannot
            be fetched from the collection
        """
        request = Request(
            method='get',
            endpoint='/_api/gharial/{}/vertex/{}/{}'.format(
                self._graph_name, self._name, key
            ),
            headers={'If-Match': rev} if rev else {}
        )

        def handler(res):
            if res.status_code == 412:
                raise DocumentRevisionError(res)
            elif res.status_code == 404 and res.error_code == 1202:
                return None
            elif res.status_code not in HTTP_OK:
                raise DocumentGetError(res)
            return res.body['vertex']

        return request, handler

    @api_method
    def insert(self, document, sync=None):
        """Insert a new document into the vertex collection.

        If the ``"_key"`` field is present in **document**, its value is used
        as the key of the new document. Otherwise, the key is auto-generated.

        :param document: the document body
        :type document: dict
        :param sync: wait for the operation to sync to disk
        :type sync: bool | None
        :returns: the ID, revision and key of the document
        :rtype: dict
        :raises arango.exceptions.DocumentInsertError: if the document cannot
            be inserted into the collection
        """
        params = {}
        if sync is not None:
            params['waitForSync'] = sync

        request = Request(
            method='post',
            endpoint='/_api/gharial/{}/vertex/{}'.format(
                self._graph_name, self._name
            ),
            data=document,
            params=params
        )

        def handler(res):
            if res.status_code not in HTTP_OK:
                raise DocumentInsertError(res)
            return res.body['vertex']

        return request, handler

    @api_method
    def update(self, document, keep_none=True, sync=None):
        """Update a document by its key in the vertex collection.

        The ``"_key"`` field must be present in **document**. If the ``"_rev"``
        field is present in **document**, its value is compared against the
        revision of the target document.

        :param document: the partial/full document with the updated values
        :type document: dict
        :param keep_none: if ``True``, the fields with value ``None`` are
            retained in the document, otherwise the fields are removed from
            the document completely
        :type keep_none: bool
        :param sync: wait for the operation to sync to disk
        :type sync: bool | None
        :returns: the ID, revision and key of the updated document
        :rtype: dict
        :raises arango.exceptions.DocumentRevisionError: if the given revision
            does not match the revision of the target document
        :raises arango.exceptions.DocumentUpdateError: if the document cannot
            be updated
        """
        params = {'keepNull': keep_none}
        if sync is not None:
            params['waitForSync'] = sync

        headers = {}
        revision = document.get('_rev')
        if revision is not None:
            headers['If-Match'] = revision

        request = Request(
            method='patch',
            endpoint='/_api/gharial/{}/vertex/{}/{}'.format(
                self._graph_name, self._name, document['_key']
            ),
            data=document,
            params=params,
            headers=headers
        )

        def handler(res):
            if res.status_code == 412:
                raise DocumentRevisionError(res)
            elif res.status_code not in HTTP_OK:
                raise DocumentUpdateError(res)
            vertex = res.body['vertex']
            vertex['_old_rev'] = vertex.pop('_oldRev')
            return vertex

        return request, handler

    @api_method
    def replace(self, document, sync=None):
        """Replace a document by its key in the vertex collection.

        The ``"_key"`` field must be present in **document**.
        If the ``"_rev"`` field is present in **document**, its value is
        compared against the revision of the target document.

        :param document: the new document
        :type document: dict
        :param sync: wait for operation to sync to disk
        :type sync: bool | None
        :returns: the ID, revision and key of the replaced document
        :rtype: dict
        :raises arango.exceptions.DocumentRevisionError: if the given revision
            does not match the revision of the target document
        :raises arango.exceptions.DocumentReplaceError: if the document cannot
            be replaced
        """
        params = {}
        if sync is not None:
            params['waitForSync'] = sync

        headers = {}
        revision = document.get('_rev')
        if revision is not None:
            headers['If-Match'] = revision

        request = Request(
            method='put',
            endpoint='/_api/gharial/{}/vertex/{}/{}'.format(
                self._graph_name, self._name, document['_key']
            ),
            params=params,
            data=document,
            headers=headers
        )

        def handler(res):
            if res.status_code == 412:
                raise DocumentRevisionError(res)
            elif res.status_code not in HTTP_OK:
                raise DocumentReplaceError(res)
            vertex = res.body['vertex']
            vertex['_old_rev'] = vertex.pop('_oldRev')
            return vertex

        return request, handler

    @api_method
    def delete(self, document, ignore_missing=False, sync=None):
        """Delete a document by its key from the vertex collection.

        The ``"_key"`` field must be present in **document**. If the ``"_rev"``
        field is present in **document**, its value is compared against the
        revision of the target document.

        :param document: the document to delete
        :type document: dict
        :param sync: wait for the operation to sync to disk
        :type sync: bool | None
        :param ignore_missing: ignore missing documents
        :type ignore_missing: bool
        :returns: whether the document was deleted successfully
        :rtype: bool
        :raises arango.exceptions.DocumentRevisionError: if the given revision
            does not match the revision of the target document
        :raises arango.exceptions.DocumentDeleteError: if the document cannot
            be deleted from the collection
        """
        params = {}
        if sync is not None:
            params['waitForSync'] = sync

        headers = {}
        revision = document.get('_rev')
        if revision is not None:
            headers['If-Match'] = revision

        request = Request(
            method='delete',
            endpoint='/_api/gharial/{}/vertex/{}/{}'.format(
                self._graph_name, self._name, document['_key']
            ),
            params=params,
            headers=headers
        )

        def handler(res):
            if res.status_code == 412:
                raise DocumentRevisionError(res)
            elif res.status_code == 404 and res.error_code == 1202:
                if ignore_missing:
                    return False
                raise DocumentDeleteError(res)
            if res.status_code not in HTTP_OK:
                raise DocumentDeleteError(res)
            return res.body['removed']

        return request, handler
