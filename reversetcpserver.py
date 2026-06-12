import argparse
import socket
import struct
import threading
from datetime import datetime
from pathlib import Path


TYPE_INITIALIZATION = 1
TYPE_AGREE = 2
TYPE_REVERSE_REQUEST = 3
TYPE_REVERSE_ANSWER = 4

HEADER_TYPE = struct.Struct("!H")
HEADER_TYPE_UINT = struct.Struct("!HI")

LOG_LOCK = threading.Lock()
LOG_PATH = Path(__file__).with_name("run_log.txt")


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def write_log(message):
    with LOG_LOCK:
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


def recv_initialization(sock):
    packet = recv_exact(sock, HEADER_TYPE_UINT.size)
    packet_type, block_count = HEADER_TYPE_UINT.unpack(packet)
    if packet_type != TYPE_INITIALIZATION:
        raise ValueError(f"expected Initialization(type=1), got type={packet_type}")
    return block_count


def recv_reverse_request(sock):
    header = recv_exact(sock, HEADER_TYPE_UINT.size)
    packet_type, length = HEADER_TYPE_UINT.unpack(header)
    if packet_type != TYPE_REVERSE_REQUEST:
        raise ValueError(f"expected reverseRequest(type=3), got type={packet_type}")
    data = recv_exact(sock, length)
    return data


def send_agree(sock):
    sock.sendall(HEADER_TYPE.pack(TYPE_AGREE))


def send_reverse_answer(sock, data):
    packet = HEADER_TYPE_UINT.pack(TYPE_REVERSE_ANSWER, len(data)) + data
    sock.sendall(packet)


def handle_client(conn, address):
    peer = f"{address[0]}:{address[1]}"
    write_log(f"client connected peer={peer}")
    try:
        block_count = recv_initialization(conn)
        write_log(f"recv Initialization peer={peer} type=1 N={block_count}")

        send_agree(conn)
        write_log(f"send agree peer={peer} type=2")

        for index in range(1, block_count + 1):
            data = recv_reverse_request(conn)
            preview = data[:40].decode("ascii", errors="replace")
            write_log(
                f"recv reverseRequest peer={peer} type=3 block={index} "
                f"length={len(data)} data_preview={preview!r}"
            )

            reversed_data = data[::-1]
            send_reverse_answer(conn, reversed_data)
            answer_preview = reversed_data[:40].decode("ascii", errors="replace")
            write_log(
                f"send reverseAnswer peer={peer} type=4 block={index} "
                f"length={len(reversed_data)} data_preview={answer_preview!r}"
            )
    except Exception as exc:
        write_log(f"client error peer={peer} error={exc}")
    finally:
        conn.close()
        write_log(f"client disconnected peer={peer}")


def run_server(host, port):
    LOG_PATH.write_text("", encoding="utf-8")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((host, port))
        server_sock.listen()
        write_log(f"server listening host={host} port={port}")
        print(f"TCP reverse server listening on {host}:{port}")

        while True:
            conn, address = server_sock.accept()
            worker = threading.Thread(target=handle_client, args=(conn, address), daemon=True)
            worker.start()


def parse_args():
    parser = argparse.ArgumentParser(description="TCP reverse server for task1.")
    parser.add_argument("--host", default="0.0.0.0", help="Address to bind. Default: 0.0.0.0")
    parser.add_argument("--port", type=int, required=True, help="TCP port to listen on.")
    parser.add_argument("--log", default=str(LOG_PATH), help="Path of run log. Default: run_log.txt")
    return parser.parse_args()


def main():
    global LOG_PATH
    args = parse_args()
    LOG_PATH = Path(args.log)
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
