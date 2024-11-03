# Pycider GRPC Demo Server

This is an example to show using a `Decider` to handle an incoming gRPC connection and return a reply. 

This code provides two gRPC endpoints. One of the gRPC endpoints is to list the available versions to download on this fake update server. The other gRPC endpoint allows a client to request a particular version's data.

This includes a test that fetches the available versions and evaluates that the proper list is returned. It then requests each version from the list and verifies that functionality. Finally it queries for a version that doesn't exist and validates that it receives an error message and no data.

## Running & Tests

1. Run `poetry install` in this directory to fetch dependencies of this application.
2. Compile the GRPC proto files with  `poetry run python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. grpc_server/proto/updater.proto`.
3. Run `poetry run python -m grpc_server` to start the server.
4. In another terminal run `poetry run pytest -s` to test the server.
