from collections.abc import Sequence
from dataclasses import dataclass, field


class UpdateState:
    class Base:
        pass

    @dataclass
    class NewConnection(Base):
        pass

    @dataclass
    class VersionsRetrieved(Base):
        versions: list[str] = field(default_factory=list)

    @dataclass
    class DownloadReady(Base):
        data: bytes
        version: str

    @dataclass
    class DownloadUnavailable(Base):
        error_code: int
        error_message: str


class UpdateEvent:
    class Base:
        pass

    @dataclass
    class RequestedDownloadValid(Base):
        version: str

    @dataclass
    class RequestedDownloadInvalid(Base):
        version: str

    @dataclass
    class VersionListRetrieval(Base):
        versions: list[str] = field(default_factory=list)


class UpdateCommand:
    class Base:
        pass

    class ListAvailableVersions(Base):
        def __init__(self, client_id: str) -> None:
            self.client_id = client_id

        def __call__(self, version_list: Sequence[str]) -> Sequence[UpdateEvent.Base]:
            return [UpdateEvent.VersionListRetrieval(versions=list(version_list))]

    class DownloadUpdate(Base):
        def __init__(self, client_id: str, version: str) -> None:
            self.client_id = client_id
            self.version = version

        def __call__(self, version_list: Sequence[str]) -> Sequence[UpdateEvent.Base]:
            if self.version in version_list:
                return [UpdateEvent.RequestedDownloadValid(version=self.version)]
            return [UpdateEvent.RequestedDownloadInvalid(version=self.version)]
