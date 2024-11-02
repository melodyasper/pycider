# Pycider GRPC Demo Server

Compile the GRPC proto files with  `poetry run python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. grpc_server/proto/updater.proto`


Run the server in one terminal with `poetry run python -m grpc_server` and in another run `poetry run pytest -s`