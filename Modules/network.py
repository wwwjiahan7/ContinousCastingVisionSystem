import errno
import os
import select
import sys
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.Qt import QThread, QApplication
import socket
import numpy as np
from Modules.LOG import *
import struct
from collections import namedtuple
PORT = 6667
import queue



class AbstractMsg(QObject):
    # 向绑定用户发送控制字符以及数据，然后接受缓存
    def __init__(self):
        """
        抽象数据包，用于维护接受和发送的数据包解析和发送工作.
        固定数据包为40字节
        """
        super(AbstractMsg, self).__init__()
        self.recCtlBits = np.uint32(0)
        self.recData = 6 * [np.float32(0.0)]
        self.recResBits = [np.float(0.0), np.float(0.0), np.uint32(0)]

        self.codenFormat_ = "I8fI"

        # 解码时使用了大端序，最简单的方法是将接收到的二进制直接逆转，但此时数据结构也会逆转.
        # PLC发送的数据，整形数据可直接解码。
        # 而浮点型数据，发送过来时则是先进行了加码，之后变为逆序，才发送，因此需要对每个浮点型数据先调整顺序，再进行浮点型解码
        self.decodenFormat_ = "I8fI"
        #self.decodenFormat_ = "I6f3I"


    def parse(self, data):
        if data and len(data) == 40:
            #print(data)
            # 因为PLC原因，数据需要颠倒, 但是其中的整型没有颠倒，只有浮点型颠倒，因此有了如下处理
            float_data = data[::-1]
            float_data = list(struct.unpack(self.decodenFormat_, float_data))
            #self.recCtlBits, self.recData, self.recResBits = data[0], data[1:7], data[7:]
            # 没有颠倒的部分，则直接用元数据进行提取
            self.recCtlBits = int.from_bytes(data[:4], 'little')
            self.recResBits[2] = int.from_bytes(data[-4:], 'little')
            #float_lst = float_data[3:-1][::-1]
            # 被颠倒的数据， 只是位置被颠倒，则用大序列颠倒的结果进行处理，此时已经解码，因此只有10个数据
            self.recData, self.recResBits[:2] = float_data[3:9][::-1], float_data[:3][::-1][:2]



            #print('[Info] Recv:', self.recCtlBits, self.recData, self.recResBits)
            return self.recCtlBits, self.recData, self.recResBits

    # 数据解码的另一种写法
    def parse2(self, data):
        if data and len(data) == 40:
            # int型的直接解码
            self.recCtlBits = int.from_bytes(data[:4], 'little')
            self.recResBits[2] = int.from_bytes(data[-4:], 'little')
            # float型的需要先逆序，再解码
            self.recData = np.array([struct.unpack('f', data[4:8][::-1])[0], struct.unpack('f', data[8:12][::-1])[0],
                                     struct.unpack('f', data[12:16][::-1])[0], struct.unpack('f', data[16:20][::-1])[0],
                                     struct.unpack('f', data[20:24][::-1])[0], struct.unpack('f', data[24:28][::-1])][0])
            self.recResBits[:2] = struct.unpack('f', data[28:32][::-1])[0], struct.unpack('f', data[32:36][::-1])[0]

            return self.recCtlBits, self.recData, self.recResBits

    def pack(self, ctl, mov, res):
        if mov is None:
            mov = 6 * [np.float32(0.0)]
        if ctl is None:
            ctl = np.uint32(0)
        if res is None:
            res = [np.uint32(0), np.float(0.0), np.float(0.0)]
        try:
            #print('[Info] Pack:', ctl, mov, res)
            mov = mov[::-1]
            #res = res[::-1]
            fres = [res[0], res[1]]
            fres = fres[::-1]
            DATA = namedtuple("DATA", "uCtl fData0 fData1 fData2 fData3 fData4 fData5 fRes0 fRes1 uRes2")
            msg_to_send = DATA(uCtl=ctl,
                               fData0=mov[0],
                               fData1=mov[1],
                               fData2=mov[2],
                               fData3=mov[3],
                               fData4=mov[4],
                               fData5=mov[5],
                               fRes0=fres[0],
                               fRes1=fres[1],
                               uRes2=res[2])
            msg_to_send = struct.pack(self.codenFormat_, *msg_to_send._asdict().values())
            #msg_to_send = msg_to_send[::-1]
            msg_to_send = msg_to_send[:4] + msg_to_send[4:28][::-1] + msg_to_send[28:36][::-1] + msg_to_send[36:]
            return msg_to_send
        except Exception as e:
            pass
            print(e)


class Network(QThread):
    robotCommunicationStatusSignal = pyqtSignal(str)
    def __init__(self, ip, port):
        super(Network, self).__init__()
        self.ip = ip
        self.port = port
        # 解析报文内容
        self.msgManager = AbstractMsg()
        # 用于保存PLC连接的套接子，所有相关指令将通过该文件发送。读取并不需要单独管理.
        self.connectSocket = None
        self.ctlBit = None
        self.data = None
        self.resBit = None

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.server:
            self.server.setblocking(0)  # 非阻塞套接字
            self.server.bind((self.ip, self.port))
            self.server.listen(1)
            inputs = [self.server]
            self.outputs = []
            self.message_queues = {}
            while inputs:
                #print('wating for the next event')
                readable, writable, exceptional = select.select(inputs, self.outputs, inputs, 1)
                for s in readable:
                    if s is self.server:
                        connection, client_address = s.accept()
                        print('connect from', client_address)
                        connection.setblocking(0)
                        inputs.append(connection)  # 同时监听这个新的套接子
                        self.message_queues[connection] = queue.Queue()
                        self.connectSocket = connection
                        self.robotCommunicationStatusSignal.emit('OK')
                    else:
                        # 其他可读客户端连接
                        data = s.recv(40)
                        if data:
                            # 一个有数据的可读客户端
                            #print('  received {!r} from {}'.format(
                            #    data, s.getpeername()), file=sys.stderr)
                            #message_queues[s].put(data)
                            # 解析新来的数据，并保存到msgManager中
                            self.ctlBit, self.data, self.resBit = self.msgManager.parse(data)
                            #if s not in outputs:
                            #    outputs.append(s)
                        else: # 没有数据
                            #print('closing', client_address)
                            self.robotCommunicationStatusSignal.emit('Break')
                            if s in self.outputs:
                                self.outputs.remove(s)
                            inputs.remove(s)
                            s.close()

                            del self.message_queues[s]
                for s in writable:
                    try:
                        next_msg = self.message_queues[s].get_nowait()
                    except queue.Empty:
                        #print(' ', s.getpeername(), 'queue empty()')
                        self.outputs.remove(s)  # 该套接子没有要发送的内容，关闭套接子
                    else:
                        #print(' sending {!r} to {}'.format(next_msg, s.getpeername()))
                        s.sendall(next_msg)


                for s in exceptional:
                    print('exception conditon on', s.getpeername())
                    inputs.remove(s)
                    if s in self.outputs:
                        self.outputs.remove(s)
                    s.close()

                    del self.message_queues[s]



    def send(self, ctl, data, res):
        try:
            if self.connectSocket is not None: # 存在PLC链接
                msg_to_send = self.msgManager.pack(ctl, data, res)
                #print('Send:',ctl,data,res)
                self.outputs.append(self.connectSocket)
                self.message_queues[self.connectSocket].put(msg_to_send)
            else:
                LOG(log_types.WARN, self.tr('No connection yet.'))
        except Exception as e:
            print(e.args[0])



from time import sleep
if __name__ == '__main__':
    app = QApplication(sys.argv)
    n = Network(ip='127.0.0.1', port=4600)
    n.start()
    while True:
        n.send(ctl=12,data=None, res=None)
