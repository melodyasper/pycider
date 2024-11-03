from concurrent import futures

import grpc
from pycider.utils import InMemory

from grpc_server.aggregate import UpdateAggregate
from grpc_server.proto import updater_pb2, updater_pb2_grpc
from grpc_server.types import UpdateCommand as C
from grpc_server.types import UpdateState as S


class UpdateServicer(updater_pb2_grpc.UpdaterServiceServicer):
    def ListAvailableUpdates(
        self, request: updater_pb2.ListAvailableUpdatesRequest, context
    ) -> updater_pb2.ListAvailableUpdatesResponse:

        executor = InMemory(UpdateAggregate())
        executor(C.ListAvailableVersions(client_id=request.client_id))
        state = executor.state

        match state:
            case S.VersionsRetrieved():
                return updater_pb2.ListAvailableUpdatesResponse(versions=state.versions)
            case _:
                # Normally this could have an error condition handler.
                return updater_pb2.ListAvailableUpdatesResponse(versions=[])

    def RequestUpdate(
        self, request: updater_pb2.RequestUpdateRequest, context
    ) -> updater_pb2.RequestUpdateResponse:

        executor = InMemory(UpdateAggregate())
        executor(C.DownloadUpdate(client_id=request.client_id, version=request.version))
        state = executor.state

        match state:
            case S.DownloadReady():
                return updater_pb2.RequestUpdateResponse(
                    version=state.version, data=state.data
                )
            case S.DownloadUnavailable():
                return updater_pb2.RequestUpdateResponse(
                    error_code=state.error_code, error_message=state.error_message
                )
            case _:
                return updater_pb2.RequestUpdateResponse(
                    error_code=-2, error_message="Unknown system state"
                )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    updater_pb2_grpc.add_UpdaterServiceServicer_to_server(UpdateServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()
