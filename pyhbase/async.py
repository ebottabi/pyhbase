# TODO(mjrusso): Discuss possibility of inclusion in canonical Avro package,
#     potentially with module name `avro.tornadoipc`.  Note that
#     this module is coded against Avro 1.3.3, the latest Python release
#     available on PyPI as of this writing. Some code changes should be made
#     for integration against Avro trunk, and are indicated with TODO
#     comments in the source, below.

import logging
import uuid

from avro import ipc
from avro import io
from functools import partial

try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO

try:
  from tornado import httpclient
except ImportError:
  # async operations not supported unless Tornado is installed
  httpclient = None


class TornadoRequestor(ipc.Requestor): 
    # TODO: Avro 1.4+: extend `ipc.BaseRequestor` instead of `ipc.Requestor`

    def request(self, message_name, request_datum, callback):
        buffer_writer = StringIO()
        buffer_encoder = io.BinaryEncoder(buffer_writer)
        self.write_handshake_request(buffer_encoder)
        self.write_call_request(message_name, request_datum, buffer_encoder)

        call_request = buffer_writer.getvalue()
        self.issue_request(call_request, message_name, request_datum, callback)

    def issue_request(self, call_request, message_name, request_datum,
                      callback):
        callback = partial(self._on_issue_request, message_name,
                           request_datum, callback)
        self.transceiver.transceive(call_request, callback)

    def _on_issue_request(self, message_name, request_datum, callback,
                          call_response):
        buffer_decoder = io.BinaryDecoder(StringIO(call_response))
        call_response_exists = self.read_handshake_response(buffer_decoder)

        response = None
        if call_response_exists:
            response = self.read_call_response(message_name, buffer_decoder)
        else:
            self.request(message_name, request_datum, callback)

        callback(response)


class TornadoHTTPTransceiver(object):

    def __init__(self, host, port):
        self.url = "http://%s:%d/" % (host, port)
        # use uuid to identify client
        self._remote_name = uuid.uuid4()

    remote_name = property(lambda self: self._remote_name)

    def transceive(self, request, callback):
        callback = partial(self._on_transceive, callback)
        self.write_framed_message(request, callback=callback)

    def _on_transceive(self, callback, response):
        if response.error:
            logging.error(
              "Avro HTTP Error: {error}".format(error=str(response.error)))
            callback(None)
            return
        result = self.read_framed_message(response.buffer)
        callback(result)

    def read_framed_message(self, response):
        response_reader = ipc.FramedReader(response)
        framed_message = response_reader.read_framed_message()
        response.read() # ensure we're ready for subsequent requests
        return framed_message

    def write_framed_message(self, message, callback):
        req_method = 'POST'
        req_headers = {'Content-Type': 'avro/binary'}

        req_body_buffer = ipc.FramedWriter(StringIO())
        req_body_buffer.write_framed_message(message)
        req_body = req_body_buffer.writer.getvalue()

        http_client = httpclient.AsyncHTTPClient()
        http_request = httpclient.HTTPRequest(
            self.url, method=req_method, headers=req_headers, body=req_body)
        http_client.fetch(http_request, callback)

    def close(self):
        pass
