#!/usr/bin/env python

############################################# 修改这里的配置即可 ######################################
# 服务端在虚拟局域网中的虚拟IP
SERVER_VIP_IN_VPN = "172.16.0.223"
# 客户端哪在真实局域网中的真实IP
CLIENT_IP = "10.0.0.10"
####################################################################################################
__author__ = 'chenxi65535'
__copyright__ = 'Copyright (c) 2016 chenxi65535'
__license__ = 'MIT'
__version__ = '0.1'

# Respect to Radoslaw Matusiak
import logging
import socket

FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'
logging.basicConfig(format=FORMAT)
LOGGER = logging.getLogger()

LOCAL_DATA_HANDLER = lambda x: x
REMOTE_DATA_HANDLER = lambda x: x

BUFFER_SIZE = 2 ** 12  # 1024. Keep buffer size as power of 2.


def udp_proxy(bind, dst, src):
    """Run UDP proxy.

    Arguments:
    src -- Source IP address and port string. I.e.: '127.0.0.1:8000'
    dst -- Destination IP address and port. I.e.: '127.0.0.1:8888'
    """
    LOGGER.debug('Starting UDP proxy...')
    LOGGER.debug('Src: {}'.format(bind))
    LOGGER.debug('Dst: {}'.format(dst))

    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    proxy_socket.bind(ip_to_tuple(bind))

    client_address = src
    server_address = ip_to_tuple(dst)

    LOGGER.info(f'client:{client_address}, server:{server_address}')

    LOGGER.debug('Looping proxy (press Ctrl-Break to stop)...')

    client_port = 0

    while True:
        data, (ip, port) = proxy_socket.recvfrom(BUFFER_SIZE)
        address = ip_to_tuple(f"{ip}:{port}")

        LOGGER.debug(f"receiving packet from address: {address}")

        if address[0] == client_address:
            LOGGER.debug(f"sending to server: {server_address}")
            data = LOCAL_DATA_HANDLER(data)
            proxy_socket.sendto(data, server_address)
            client_port = port
        elif address[0] == server_address[0]:
            LOGGER.debug(f"sending to client: {(client_address, client_port)}")
            data = REMOTE_DATA_HANDLER(data)
            proxy_socket.sendto(data, (client_address, client_port))
        else:
            LOGGER.warning('Unknown address: {}'.format(str(address)))


def ip_to_tuple(ip):
    """Parse IP string and return (ip, port) tuple.

    Arguments:
    ip -- IP address:port string. I.e.: '127.0.0.1:8000'.
    """
    ip, port = ip.split(':')
    return (ip, int(port))


def main():
    LOGGER.setLevel(logging.NOTSET)

    run_io_tasks_in_parallel([
        lambda: udp_proxy("0.0.0.0:62900", f"{SERVER_VIP_IN_VPN}:62900", f"{CLIENT_IP}"),
        lambda: udp_proxy("0.0.0.0:62056", f"{SERVER_VIP_IN_VPN}:62056", f"{CLIENT_IP}"),
    ])


from concurrent.futures import ThreadPoolExecutor


def run_io_tasks_in_parallel(tasks):
    with ThreadPoolExecutor() as executor:
        running_tasks = [executor.submit(task) for task in tasks]
        for running_task in running_tasks:
            running_task.result()


# end-of-function main


if __name__ == '__main__':
    main()
