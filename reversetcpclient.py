import argparse
import random
import socket
import struct
from datetime import datetime
from pathlib import Path


TYPE_INITIALIZATION = 1
TYPE_AGREE = 2
TYPE_REVERSE_REQUEST = 3
TYPE_REVERSE_ANSWER = 4

HEADER_TYPE = struct.Struct("!H")
HEADER_TYPE_UINT = struct.Struct("!HI")
LOG_PATH = Path(__file__).with_name("run_log.txt")


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def write_log(message):
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{now_text()}] {message}\n")


def recv_exact(sock, size):
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("peer closed the connection")
        data.extend(chunk)
    return bytes(data)


def validate_ascii_printable(data):
    for byte in data:
        if byte in (9, 10, 13):
            continue
        if byte < 32 or byte > 126:
            raise ValueError("input file must contain printable ASCII text only")


def split_random_chunks(data, lmin, lmax, seed=None):
    if lmin <= 0 or lmax <= 0 or lmin > lmax:
        raise ValueError("Lmin and Lmax must be positive, and Lmin <= Lmax")
    if not data:
        return []

    rng = random.Random(seed)
    chunks = []
    offset = 0
    while offset < len(data):
        remaining = len(data) - offset
        if remaining <= lmax:
            chunks.append(data[offset:])
            break

        max_length = min(lmax, remaining)
        length = rng.randint(lmin, max_length)
        chunks.append(data[offset:offset + length])
        offset += length
    return chunks


def send_initialization(sock, block_count):
    sock.sendall(HEADER_TYPE_UINT.pack(TYPE_INITIALIZATION, block_count))


def recv_agree(sock):
    packet = recv_exact(sock, HEADER_TYPE.size)
    packet_type, = HEADER_TYPE.unpack(packet)
    if packet_type != TYPE_AGREE:
        raise ValueError(f"expected agree(type=2), got type={packet_type}")


def send_reverse_request(sock, data):
    packet = HEADER_TYPE_UINT.pack(TYPE_REVERSE_REQUEST, len(data)) + data
    sock.sendall(packet)


def recv_reverse_answer(sock):
    header = recv_exact(sock, HEADER_TYPE_UINT.size)
    packet_type, length = HEADER_TYPE_UINT.unpack(header)
    if packet_type != TYPE_REVERSE_ANSWER:
        raise ValueError(f"expected reverseAnswer(type=4), got type={packet_type}")
    return recv_exact(sock, length)


def run_client(server_ip, server_port, input_file, output_file, lmin, lmax, seed):
    data = Path(input_file).read_bytes()
    validate_ascii_printable(data)
    chunks = split_random_chunks(data, lmin, lmax, seed)
    reversed_chunks = []

    LOG_PATH.write_text("", encoding="utf-8")
    write_log(
        f"client start server={server_ip}:{server_port} input={input_file} "
        f"bytes={len(data)} Lmin={lmin} Lmax={lmax} seed={seed} N={len(chunks)}"
    )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_ip, server_port))
        write_log(f"connected server={server_ip}:{server_port}")

        send_initialization(sock, len(chunks))
        write_log(f"send Initialization type=1 N={len(chunks)}")

        recv_agree(sock)
        write_log("recv agree type=2")

        for index, chunk in enumerate(chunks, start=1):
            send_reverse_request(sock, chunk)
            preview = chunk[:40].decode("ascii", errors="replace")
            write_log(
                f"send reverseRequest type=3 block={index} "
                f"length={len(chunk)} data_preview={preview!r}"
            )

            reversed_data = recv_reverse_answer(sock)
            answer_preview = reversed_data[:40].decode("ascii", errors="replace")
            write_log(
                f"recv reverseAnswer type=4 block={index} "
                f"length={len(reversed_data)} data_preview={answer_preview!r}"
            )
            reversed_chunks.append(reversed_data)
            print(f"{index}: {reversed_data.decode('ascii', errors='replace')}")

    whole_reversed = b"".join(reversed(reversed_chunks))
    Path(output_file).write_bytes(whole_reversed)
    write_log(f"output written path={output_file} bytes={len(whole_reversed)}")
    print(f"Reversed file written to {output_file}")


def parse_args():
    parser = argparse.ArgumentParser(description="TCP reverse client for task1.")
    parser.add_argument("server_ip", help="Server IP address.")
    parser.add_argument("server_port", type=int, help="Server TCP port.")
    parser.add_argument("input_file", help="Printable ASCII input file.")
    parser.add_argument("output_file", help="Path for the final fully reversed output file.")
    parser.add_argument("lmin", type=int, help="Minimum chunk length in bytes.")
    parser.add_argument("lmax", type=int, help="Maximum chunk length in bytes.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for repeatable chunking.")
    parser.add_argument("--log", default=str(LOG_PATH), help="Path of run log. Default: run_log.txt")
    return parser.parse_args()


def main():
    global LOG_PATH
    args = parse_args()
    LOG_PATH = Path(args.log)
    run_client(
        args.server_ip,
        args.server_port,
        args.input_file,
        args.output_file,
        args.lmin,
        args.lmax,
        args.seed,
    )


if __name__ == "__main__":
    main()
