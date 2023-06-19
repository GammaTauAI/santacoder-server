# The SantaCoder Server for OpenTau

A socket for the Rust client in [OpenTau](https://github.com/GammaTauAI/opentau) for type-inference using [SantaCoder](https://huggingface.co/bigcode/santacoder) 
and [SantaCoder-FIT](https://huggingface.co/gammatau/santacoder-ts-fim).

The code for the inference part of the server was originally written by @arjunguha and later adapted by @mhyee, in his TypeWeaver project: https://github.com/nuprl/TypeWeaver

### To run independently:

- clone this repo

```bash
git clone https://github.com/GammaTauAI/santacoder-server && cd santacoder-server
```

- install dependencies

```bash
pip install -r ./requirements.txt
```

- start the socket

```bash
python main.py \
  --socket_path <socket path> \
  --device <gpu> \
  --max_length 2048
```

- test the socket with a request

```bash
python ./test_socket.py <socket path>
```
