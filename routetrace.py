import argparse
from enum import Enum
import socket
import struct

class Packet_Type(Enum):
    HELLO_MESSAGE = 'H'
    LINK_STATE_MESSAGE = 'L'
    ROUTE_TRACE = 'T'

def parse_command_line_args():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-a', '--routetrace_port', help='port on which the routetrace listens on for packets', required=True, type=int)
    parser.add_argument('-b', '--source_hostname', help='source hostname', required=True, type=str)
    parser.add_argument('-c', '--source_port', help='source port number', required=True, type=int)
    parser.add_argument('-d', '--dest_hostname', help='destination hostname', required=True, type=str)
    parser.add_argument('-e', '--dest_port', help='destination port number', required=True, type=int)
    parser.add_argument('-f', '--debug_option', help="when the debug option is 1, the application will print out the following information about the packets that it sends and receives: TTL of the packet and the src. and dst. IP and port numbers. It will not do so when this option is 0", required=True, type=int)

    args = parser.parse_args()
    return args

def send_packet(source_ip, source_port, time_to_live, routetrace_ip, routetrace_port, dest_ip, dest_port, debug_option):
    #print('--------------------------------------')
    #print('SENDING ROUTETRACE PACKET to:', source_ip, ':', str(source_port))
    #print('routetrace ip: ', routetrace_ip, ', routetrace port: ', routetrace_port)
    #print('dest hostname: ', dest_ip, ', dest port: ', dest_port)
    #print('time to live: ', time_to_live)
    #print('debug option: ', debug_option)
    #print('--------------------------------------')
    routetrace_ip_a = int(routetrace_ip.split('.')[0])
    routetrace_ip_b = int(routetrace_ip.split('.')[1])
    routetrace_ip_c = int(routetrace_ip.split('.')[2])
    routetrace_ip_d = int(routetrace_ip.split('.')[3])

    dest_ip_a = int(dest_ip.split('.')[0])
    dest_ip_b = int(dest_ip.split('.')[1])
    dest_ip_c = int(dest_ip.split('.')[2])
    dest_ip_d = int(dest_ip.split('.')[3])
   
    header = struct.pack(
        '!cIIIIIIIIIIII',
        Packet_Type.ROUTE_TRACE.value.encode('ascii'),
        routetrace_ip_a, routetrace_ip_b, routetrace_ip_c, routetrace_ip_d,
        routetrace_port,
        0, # placeholder values,
        time_to_live,
        dest_ip_a, dest_ip_b, dest_ip_c, dest_ip_d, 
        dest_port
    )
    data = ''.encode()
    packet = header + data

    global sock
    sock.sendto(packet, (source_ip, source_port))

def parse_packet(packet):
    header = struct.unpack('!cIIIIIIIIIIII', packet[:50])
    packet_type = header[0].decode('ascii')
    source_ip = str(header[1]) + '.' + str(header[2]) + '.' + str(header[3]) + '.' + str(header[4])
    source_port = header[5]
    sequence_number = header[6]
    ttl = header[7]

    dest_ip = str(header[8]) + '.' + str(header[9]) + '.' + str(header[10]) + '.' + str(header[11])
    dest_port = header[12]

    data = packet[50:].decode()

    #print('-----------------------------')
    #print('INCOMING PACKET:')
    #print('packet type: ', packet_type)
    #print('source ip: ', source_ip, ', source port: ', source_port)
    #print('dest ip: ', dest_ip, ', dest port: ', dest_port)
    #print('sequence number: ', sequence_number) this field is unused in a routetrace packet
    #print('time to live: ', ttl)
    #print('data: ', data)
    #print('-----------------------------')
    
    return source_ip, source_port

def print_route(route_taken):
    print("Hop#\t IP,Port")
    num_hops = len(route_taken)
    for i in range(0, num_hops):
        hop_number = i + 1
        addr = route_taken[hop_number]["ip"] + ',' + str(route_taken[hop_number]["port"])
        print(hop_number, "\t", addr)

args = parse_command_line_args()
routetrace_port = args.routetrace_port
source_hostname = args.source_hostname
source_ip = socket.gethostbyname(source_hostname)
source_port = args.source_port
dest_hostname = args.dest_hostname
dest_ip = socket.gethostbyname(dest_hostname)
dest_port = args.dest_port
debug_option = args.debug_option

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
routetrace_hostname = socket.gethostname()
routetrace_ip = socket.gethostbyname(routetrace_hostname)
sock.bind((routetrace_hostname, routetrace_port))
#print('MY ADDRESS IS: ', routetrace_hostname, ':', routetrace_port)

hop_number = 1
route_taken = {}

time_to_live = 0
while True:
    send_packet(source_ip, source_port, time_to_live, routetrace_ip, routetrace_port, dest_ip, dest_port, debug_option)

    packet_with_header, sender_address = sock.recvfrom(1024)

    responder_ip, responder_port = parse_packet(packet_with_header)
    
    route_taken[hop_number] = {}
    route_taken[hop_number]["ip"] = responder_ip
    route_taken[hop_number]["port"] = responder_port

    hop_number += 1

    if responder_ip == dest_ip and responder_port == dest_port:
        break
    else:
        time_to_live += 1

print_route(route_taken)
