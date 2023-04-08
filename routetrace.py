import argparse
import socket

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

def send_packet(t, time_to_live, routetrace_ip, routetrace_port, dest_ip, dest_port, source_hostname, source_port, debug_option):
    print('--------------------------------------')
    print('SENDING PACKET:')
    print('routetrace ip: ', routetrace_ip, ', routetrace port: ', routetrace_port)
    print('dest hostname: ', dest_hostname, ', dest port: ', dest_port)
    print('source hostname: ', source_hostname, ', source port: ', source_port)
    print('debug option: ', debug_option)
    print('--------------------------------------')

# parse the packet and return the responder's ip and port
def parse_packet(packet):
    print('--------------------------')
    print('PARSING PACKET:')
    print('--------------------------')
    
    return '123.123.123.123', 2000

args = parse_command_line_args()
routetrace_port = args.routetrace_port
source_hostname = args.source_hostname
source_port = args.source_port
dest_hostname = args.dest_hostname
dest_ip = socket.gethostbyname(dest_hostname)
dest_port = args.dest_port
debug_option = args.debug_option

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
routetrace_hostname = socket.gethostname()
routetrace_ip = socket.gethostbyname(routetrace_hostname)
sock.bind((routetrace_hostname, routetrace_port))

while True:
    t = 0 # what is t?????!!
    time_to_live = 0
    send_packet(t, time_to_live, routetrace_ip, routetrace_port, dest_ip, dest_port, source_hostname, source_port, debug_option)
    packet_with_header, sender_address = sock.recvfrom(1024)

    responder_ip, responder_port = parse_packet(packet_with_header)
    
    if responder_ip == dest_ip and responder_port == dest_port:
        break
    else:
        time_to_live += 1

print('routetrace END')