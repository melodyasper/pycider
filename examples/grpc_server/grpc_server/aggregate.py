from typing import Sequence

from grpc_server.types import UpdateCommand as C
from grpc_server.types import UpdateEvent as E
from grpc_server.types import UpdateState as S

from pycider.deciders import Decider

VERSION_LIST_TO_DATA: dict[str, bytes] = {
    "0.10.41": b"download_data",
    "0.6.27": b"download_data",
    "2.5.1": b"download_data",
    "3.3.12": b"download_data",
    "4.13.45": b"download_data",
    "6.18.30": b"download_data",
    "6.20.21": b"download_data",
    "6.5.3": b"download_data",
    "6.8.9": b"download_data",
    "8.9.38": b"download_data",
}


class UpdateAggregate(Decider[E.Base, C.Base, S.Base]):
    def initial_state(self) -> S.Base:
        return S.NewConnection()

    def is_terminal(self, state: S.Base) -> bool:
        match state:
            case S.VersionsRetrieved():
                return True
            case S.DownloadReady():
                return True
            case S.DownloadUnavailable():
                return True
            case _:
                return False

    def evolve(self, state: S.Base, event: E.Base) -> S.Base:
        match state, event:
            case S.NewConnection(), E.VersionListRetrieval():
                return S.VersionsRetrieved(versions=event.versions)

            case S.NewConnection(), E.RequestedDownloadValid():
                return S.DownloadReady(
                    version=event.version, data=VERSION_LIST_TO_DATA[event.version]
                )

            case S.NewConnection(), E.RequestedDownloadInvalid():
                return S.DownloadUnavailable(
                    error_code=-1,
                    error_message=f"Version {event.version} does not exist.",
                )

            case _:
                return state

    def decide(self, command: C.Base, state: S.Base) -> Sequence[E.Base]:
        match command, state:
            case C.ListAvailableVersions(), S.NewConnection():
                """Requesting a list of versions."""
                return command(list(VERSION_LIST_TO_DATA.keys()))

            case (
                C.DownloadUpdate(),
                S.NewConnection(),
            ):
                """ "Requesting a download of a particular version"""
                return command(list(VERSION_LIST_TO_DATA.keys()))

            case _:
                return []
