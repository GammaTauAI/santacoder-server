# The SantaCoder Server for OpenTau

A socket for the Rust Core in [OpenTau](https://github.com/GammaTauAI/opentau) for type prediction using [SantaCoder](https://huggingface.co/bigcode/santacoder)
and [SantaCoder-FIT](https://huggingface.co/gammatau/santacoder-ts-fim).
The server open an unix socket
which is used by OpenTau to make requests to the model. A SantaCoder model needs to
be trained and saved before this server can be used (HuggingFace models can also be
used by just pointing to the HuggingFace name, e.g. `bigcode/santacoder`).
SantaCoder-FIT and SantaCoder-TS can be fine-tuned using the training scripts provided in the
artifact. We will provide pre-trained SantaCoder-FT and SantaCoder-TS models once
we can de-anonymize our data.

To set the model being used, change the `MODEL_NAME` environment variable when running the
server.

The code for the inference part of the server was originally written by @arjunguha and later
adapted by @mhyee, in his TypeWeaver project: https://github.com/nuprl/TypeWeaver

### To run:

#### install dependencies

```bash
pip install -r ./requirements.txt
```

#### start the socket server

```bash
MODEL_NAME=<model name> python main.py \
  --socket_path <socket path> \
  --device <gpu device id, or 'cpu'> \
  --max_length <max context window size> \
```

The command will start the socket server and wait for requests. You could run this in
another terminal or in a tmux/screen session.

Example usage:

```bash
MODEL_NAME='bigcode/santacoder' python main.py \
  --socket_path /tmp/santa.sock \
  --device 0 \
  --max_length 2048 \
```

#### test the socket with a request

```bash
python ./test_socket.py <socket path>
```

If following the above example, this would be:

```bash
python ./test_socket.py /tmp/santa.sock
```
