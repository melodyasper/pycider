import threading
import time
import uuid

import grpc
from grpc_server.aggregate import VERSION_LIST_TO_DATA
from grpc_server.proto import updater_pb2, updater_pb2_grpc
from grpc_server.server import serve


def test_update_server():
    server_thread = threading.Thread(target=serve, daemon=True)
    server_thread.start()
    time.sleep(2)

    client_id = uuid.uuid4().hex
    channel = grpc.insecure_channel("localhost:50051")
    stub = updater_pb2_grpc.UpdaterServiceStub(channel)

    # Fetch and verify version list
    request_list = updater_pb2.ListAvailableUpdatesRequest(client_id=client_id)
    response_list = stub.ListAvailableUpdates(request_list)
    assert response_list.versions == list(VERSION_LIST_TO_DATA.keys())

    # Lets make sure we can fetch each version
    for version in response_list.versions:
        request_update = updater_pb2.RequestUpdateRequest(
            client_id=client_id, version=version
        )
        response_update = stub.RequestUpdate(request_update)
        assert response_update.version == version
        assert response_update.data == VERSION_LIST_TO_DATA[version]
        assert response_update.error_code == 0
        assert response_update.error_message == ""

    # Lets try a bad update
    request_update = updater_pb2.RequestUpdateRequest(
        client_id=client_id, version="9.9.9"
    )
    response_update = stub.RequestUpdate(request_update)
    assert response_update.version == ""
    assert response_update.data == b""
    assert response_update.error_code == -1
    assert response_update.error_message == "Version 9.9.9 does not exist."
