Task1 TCP Socket Programming 程序运行说明

一、程序文件说明

本目录包含以下文件：

1. reversetcpserver.py
   TCP 服务端程序。服务端监听指定端口，接收客户端连接，并为每个客户端创建一个线程进行处理，因此可以同时处理两个及以上客户端的请求。

2. reversetcpclient.py
   TCP 客户端程序。客户端读取一个全英文可打印 ASCII 文本文件，按照指定的 Lmin、Lmax 随机划分为多个数据块，逐块发送给服务端，请求服务端反转每块数据。客户端收到所有反转结果后，将这些反转块按相反顺序拼接，生成原文件的完整反转文件。

3. sample_input.txt
   测试输入文件，内容为可打印 ASCII 文本。

4. reversed_output.txt
   客户端运行后生成的输出文件，内容为 sample_input.txt 的整体反转结果。

5. run_log_client.txt
   客户端运行日志，记录客户端发送和接收每个应用层报文的时间、类型、块号、长度和部分数据内容。

6. run_log_server.txt
   服务端运行日志，记录服务端接收和发送每个应用层报文的时间、客户端地址、类型、块号、长度和部分数据内容。

二、运行环境

1. 操作系统：Windows
2. Python 版本：Python 3.8 或更高版本
3. 第三方依赖：无
4. 抓包工具：Wireshark
5. 本次测试方式：client 和 server 都运行在 Windows 本机，通信地址为 127.0.0.1

三、应用层报文格式

本实验在 TCP 之上自定义了 4 类应用层报文。所有整数均采用网络字节序，即大端序。

1. Initialization 报文

方向：client -> server

格式：

Type(2 Bytes) + N(4 Bytes)

含义：

Type = 1，N 表示客户端将要发送给服务端进行 reverse 的数据块总数。

2. agree 报文

方向：server -> client

格式：

Type(2 Bytes)

含义：

Type = 2，表示服务端已经收到 Initialization 报文，并同意继续处理后续请求。

3. reverseRequest 报文

方向：client -> server

格式：

Type(2 Bytes) + Length(4 Bytes) + Data

含义：

Type = 3，Length 表示 Data 字段长度，单位为 Byte。Data 是客户端请求服务端反转的数据块。

4. reverseAnswer 报文

方向：server -> client

格式：

Type(2 Bytes) + Length(4 Bytes) + reverseData

含义：

Type = 4，Length 表示 reverseData 字段长度，单位为 Byte。reverseData 是服务端对 Data 反转后的结果。

四、运行方法

本次实验 client 和 server 都运行在 Windows 本机，因此 serverIP 使用 127.0.0.1，端口使用 12000。

1. 启动 Wireshark

在 Wireshark 首页选择：

Adapter for loopback traffic capture

这是抓取 127.0.0.1 本机回环流量的接口。

开始抓包后，在显示过滤器中输入：

tcp.port == 12000 && tcp.len > 0

该过滤器只显示 TCP 端口为 12000 且携带应用层数据的报文，可以过滤掉 TCP 三次握手、ACK 等无应用层数据的报文。

为了让 Wireshark 时间戳与程序日志时间戳对应，需要设置：

视图 -> 时间显示格式 -> 日期和时间

并设置时间精度为：

视图 -> 时间显示格式 -> 毫秒

2. 启动服务端

打开第一个 PowerShell，输入：

Set-Location "D:\课程设计\计算机网络课程设计\task1"
python .\reversetcpserver.py --host 127.0.0.1 --port 12000 --log .\run_log_server.txt

服务端启动后会持续监听 127.0.0.1:12000，不要关闭该窗口。

3. 启动客户端

确认 Wireshark 已经开始抓包后，打开第二个 PowerShell，输入：

Set-Location "D:\课程设计\计算机网络课程设计\task1"
python .\reversetcpclient.py 127.0.0.1 12000 .\sample_input.txt .\reversed_output.txt 20 50 --seed 42 --log .\run_log_client.txt

参数含义如下：

1. 127.0.0.1：服务端 IP 地址。
2. 12000：服务端 TCP 端口。
3. .\sample_input.txt：客户端读取的原始文本文件。
4. .\reversed_output.txt：客户端生成的完整反转输出文件。
5. 20：每个数据块的最小长度 Lmin。
6. 50：每个数据块的最大长度 Lmax。
7. --seed 42：随机种子，用于复现实验中的随机分块结果。
8. --log .\run_log_client.txt：指定客户端日志文件。

五、程序运行逻辑

客户端首先读取 sample_input.txt，并检查文件内容是否为可打印 ASCII 字符。然后客户端根据 Lmin、Lmax 和随机种子 seed 生成每一块数据的长度。本次测试参数为 Lmin=20，Lmax=50，seed=42，输入文件大小为 186 Bytes，生成的数据块数 N=6。

客户端在发送实际数据前，会先向服务端发送 Initialization 报文，告知服务端后续共有 N 个 reverseRequest 报文。服务端收到后返回 agree 报文。

随后客户端依次发送 reverseRequest 报文。每个 reverseRequest 报文中包含一个数据块，服务端收到后将该数据块按字节反转，并通过 reverseAnswer 报文返回给客户端。

客户端在命令行中打印每一块的反转结果。由于每一块只是在块内反转，要得到整个文件的完整反转结果，客户端需要将收到的反转块按相反顺序拼接。即如果原始分块为 C1、C2、...、Cn，服务端返回 reverse(C1)、reverse(C2)、...、reverse(Cn)，客户端最终写入文件的内容为：

reverse(Cn) + reverse(Cn-1) + ... + reverse(C1)

这样得到的结果就是整个输入文件的完整反转。

六、关键实现说明

1. 使用 TCP socket

client 和 server 均基于 Python socket 模块实现，通信协议为 TCP。

2. 使用 struct 封装和解析报文

程序使用 struct.Struct("!H") 封装 2 Bytes 的 Type 字段，使用 struct.Struct("!HI") 封装 Type + N 或 Type + Length。其中 ! 表示网络字节序，H 表示 2 Bytes 无符号整数，I 表示 4 Bytes 无符号整数。

3. 使用 recv_exact 解决 TCP 字节流问题

TCP 是字节流协议，一次 recv() 不一定刚好收到一个完整应用层报文。因此 client 和 server 都实现了 recv_exact(sock, size)，循环接收直到获得指定字节数，保证报文头和报文体能够被完整读取。

4. 支持随机长度分块

客户端使用 Lmin、Lmax 和 seed 随机生成每块长度。除最后一块外，每块长度均在 [Lmin, Lmax] 范围内。本次运行生成的块长度为：

40, 23, 20, 43, 28, 32

总数据长度为 186 Bytes，因此 N=6。

5. 服务端支持并发客户端

服务端每 accept 一个客户端连接，就创建一个新线程调用 handle_client 处理该客户端。因此服务端可以同时处理两个及以上客户端连接。

6. 运行日志用于和 Wireshark 抓包互相验证

client 和 server 在发送或接收每个应用层报文时都会写入日志，日志包含毫秒级时间戳、报文类型、块号、长度和数据预览。Wireshark 抓包中可以通过时间戳、TCP 端口、TCP payload 长度以及 payload 内容与日志进行对应验证。

七、Wireshark 抓包验证方法

显示过滤器：

tcp.port == 12000 && tcp.len > 0

四类报文在 Wireshark 十六进制 payload 中的识别方式如下：

1. Initialization

示例：

00 01 00 00 00 06

含义：

Type = 1，N = 6。

2. agree

示例：

00 02

含义：

Type = 2。

3. reverseRequest

示例：

00 03 00 00 00 28

含义：

Type = 3，Length = 0x28 = 40 Bytes。

4. reverseAnswer

示例：

00 04 00 00 00 28

含义：

Type = 4，Length = 0x28 = 40 Bytes。

八、Git URL

https://github.com/schrieeeffer/tcp_socket
