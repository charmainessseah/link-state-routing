import argparse
from enum import Enum
import pickle
import socket
import sys
import struct
import time

class Packet_Type(Enum):
    HELLO_MESSAGE = 'H'
    LINK_STATE_MESSAGE = 'L'
    ROUTE_TRACE = 'T'

def parse_command_line_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--port', help='the port that the emulator listens to for incoming packets', required=True, type=int)
    parser.add_argument('-f', '--filename', help='the name of the topology file', required=True, type=str)

    args = parser.parse_args()
    return args

# read topology file and build the network structure in a dict
# key: node
# value: list of neighboring nodes
# all nodes are in string format "ip:port"
# {
#   "ip:port": ["ip:port", "ip:port"]
# }
def read_topology(filename):
    try:
        file = open(filename, 'r')
    except:
        print('ERROR: Reading topology file')
        return
    
    network_topology = {}
    file_lines = file.readlines()

    for line in file_lines:
        nodes_in_line = line.split()
        source_node = nodes_in_line[0].replace(",", ":")
        network_topology[source_node] = []
        for index in range(1, len(nodes_in_line)):
            node = nodes_in_line[index].replace(",", ":")
            if node not in network_topology[source_node]:
                network_topology[source_node].append(node)

    print(network_topology)
    return network_topology

paths = []
path = []
# prints out source and dest as well as the distance
def print_solution(start_node, distances, parents, index_to_node_map):
    num_nodes = len(distances)
    print("         node\t\t\t      Distance\t\t\t Path")
    
    start_addr = index_to_node_map[start_node]
    for node_index in range(num_nodes):
        if node_index != start_node:
            dest_addr = index_to_node_map[node_index]

            print("\n", start_addr, "->", dest_addr, "\t\t", distances[node_index], "\t\t", end="")
            print_path(node_index, parents, index_to_node_map)

            global path
            paths.append(path)
            path = []
    
    return paths

NO_PARENT = -1
# prints shortest path between source and dest node using parents array
def print_path(current_node, parents, index_to_node_map):
    if current_node == NO_PARENT:
        return
    
    print_path(parents[current_node], parents, index_to_node_map)

    curr_addr = index_to_node_map[current_node]
    path.append(curr_addr)
    print(curr_addr, end=" ")

def dijkstra(adjacency_matrix, start_node, index_to_node_map):
    num_nodes = len(adjacency_matrix)

    # min_distance[i] holds the min distance from start node to i
    min_distance = [sys.maxsize] * num_nodes
    visited = [False] * num_nodes
 
    for node_index in range(num_nodes):
        min_distance[node_index] = sys.maxsize
        visited[node_index] = False
         
    min_distance[start_node] = 0
 
    # parent array to store shortest path
    parents = [-1] * num_nodes
    parents[start_node] = NO_PARENT
 
    # picking the curr source node
    for i in range(0, num_nodes - 1):
        nearest_node = -1 # holds the index of the picked/source node
        shortest_distance = sys.maxsize
        for node_index in range(num_nodes):
            if not visited[node_index] and min_distance[node_index] < shortest_distance:
                nearest_node = node_index
                shortest_distance = min_distance[node_index]
 
        visited[nearest_node] = True

        # exploring and updating adjacent nodes to picked source node
        for node_index in range(num_nodes):
            edge_distance = adjacency_matrix[nearest_node][node_index]
            # shortest dist refers to the shortest dist to reach the curr node at node_index from the starting node
            if edge_distance > 0 and shortest_distance + edge_distance < min_distance[node_index]:
                parents[node_index] = nearest_node
                min_distance[node_index] = shortest_distance + edge_distance
 
    all_paths = print_solution(start_node, min_distance, parents, index_to_node_map)
    print('\nALL PATHS:')
    print(all_paths)

    forwarding_table = construct_forwarding_table(all_paths)
    print('FORWARDING TABLE:')
    print(forwarding_table)
    return forwarding_table

def construct_forwarding_table(all_paths):
    # { dest: next_hop }
    forwarding_table = {}

    for path in all_paths:
        dest = path[len(path) - 1]
        next_hop = path[1]
        forwarding_table[dest] = next_hop

    return forwarding_table

def construct_adjacency_matrix(network_topology):
    # assign each ip:port node a number for the adjacency matrix
    num_nodes = len(network_topology)
    index_to_node_map = {}
    node_to_index_map = {}
    index = 0
    for node in network_topology:
        node_to_index_map[node] = index
        index_to_node_map[index] = node
        index += 1
    
    adjacency_matrix = [[0 for column in range(num_nodes)]
                      for row in range(num_nodes)]
    
    for node in network_topology:
        node_index = node_to_index_map[node]
        neighboring_nodes = network_topology[node]
        for neighbor in neighboring_nodes:
            neighbor_index = node_to_index_map[neighbor]
            adjacency_matrix[node_index][neighbor_index] = 1
            adjacency_matrix[neighbor_index][node_index] = 1

    print(adjacency_matrix)
    return adjacency_matrix, index_to_node_map

# TODO
def send_message(source_addr, dest_addr, data):
    source_ip = source_addr.split(' ')[0]
    source_port = source_addr.split(' ')[1]
    dest_ip = dest_addr.split(' ')[0]
    dest_port = dest_addr.split(' ')[1]

def parse_packet(packet):
    encapsulation_header = struct.unpack('!BBBBBhBBBBhI', packet[:17]) # first unpack and get encapsulation header

    header = struct.unpack('!cIIIII', packet[:22])
    packet_type = header[0].decode('ascii')
    time_to_live = header[1]
    source_ip = header[2] 
    source_port = header[3]
    dest_ip = header[4]
    dest_port = header[5]

    data = packet[17:].decode()

    print('-----------------------------')
    print('INCOMING PACKET:')
    print('packet type: ', packet_type)
    print('time to live: ', time_to_live)
    print('source ip: ', source_ip, ', source port: ', source_port)
    print('dest ip: ', dest_ip, ', dest port: ', dest_port)
    print('data: ', data)
    print('-----------------------------')
    
    return packet_type, time_to_live, source_ip, source_port, dest_ip, dest_port

def send_routetrace_packet(time_to_live, source_ip, source_port, dest_ip, dest_port):
    print('--------------------------------------')
    print('SENDING PACKET:')
    print('source ip: ', source_ip, ', source port: ', source_port)
    print('dest hostname: ', dest_ip, ', dest port: ', dest_port)
    # print('source hostname: ', source_hostname, ', source port: ', source_port)
    print('--------------------------------------')

    header = struct.pack(
        '!cIIIII',
        Packet_Type.ROUTE_TRACE.value.encode('ascii'),
        time_to_live,
        source_ip, source_port,
        dest_ip, dest_port
    )
    data = ''.encode()
    packet = header + data

    global sock
    sock.sendto(packet, (dest_ip, dest_port))


# TODO
def send_hello_message_to_neighbors(my_addr, neighboring_nodes):
    source_ip = my_addr.split(' ')[0]
    source_port = my_addr.split(' ')[1] 
    for neighbor in neighboring_nodes:
        print('neighbor: ', neighbor)
        dest_ip = neighbor.split(' ')[0]
        dest_port = neighbor.split(' ')[1]

        header = struct.pack(
            '!cIIIII',
            0,
            Packet_Type.HELLO_MESSAGE.value.encode('ascii'),
            0, 0,
            0, 0
        )
        data = 'hello'.encode()
        packet = header + data

        global sock
        sock.sendto(packet, (dest_ip, dest_port))

def send_link_state_message_to_neighbors(my_addr, neighboring_nodes):
    for neighbor in neighboring_nodes:
        print('neighbor: ', neighbor)
        dest_ip = neighbor.split(' ')[0]
        dest_port = neighbor.split(' ')[1]

        # do we need a header?
        # header = struct.pack('!cII', packet_type, sequence_number, window_size)
        data = 'hello'.encode()
        
        global sock
        sock.sendto(data, (dest_ip, dest_port))

# finds the shortest path between all nodes from source to dest
# and returns an updated forwarding table
def find_shortest_path_and_return_forwarding_table(network_topology):
    starting_node = 0
    adjacency_matrix, index_to_node_map = construct_adjacency_matrix(network_topology)
    forwarding_table = dijkstra(adjacency_matrix, starting_node, index_to_node_map)

    return forwarding_table

def init_dictionaries(list_of_neighbors):
    active_neighbors = {}
    received_hello_message = {}

    for neighbor in list_of_neighbors:
        active_neighbors[neighbor] = True
        received_hello_message = False

    return active_neighbors, received_hello_message

def epoch_time_in_milliseconds_now():
    time_now_in_milliseconds = round(time.time() * 1000)
    # print("Milliseconds since epoch:", time_now_in_milliseconds)
    return time_now_in_milliseconds

def decrement_time_to_live(packet_type, time_to_live, source_ip, source_port, dest_ip, dest_port):
    header = struct.pack(
        '!cIIIII',
        packet_type.encode('ascii'),
        time_to_live - 1,
        source_ip, source_port,
        dest_ip, dest_port
    )
    data = ''.encode()
    packet = header + data

    return packet

def update_network_topology(received_hello_message):
    pass

args = parse_command_line_args()
emulator_port = args.port
topology_filename = args.filename

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
emulator_hostname = socket.gethostname()
emulator_ip = socket.gethostbyname(emulator_hostname)
sock.bind((emulator_hostname, emulator_port))
sock.setblocking(0) # receive packets in a non-blocking way

my_addr = emulator_ip + ':' + str(emulator_port)
my_addr = '1.0.0.0:1'

network_topology = read_topology(topology_filename)

# active_neighbors = { ip:port : True/ False }
# we will init all neighbors to be active initially
# received_hello_message = { ip:port : False }
active_neighbors, received_hello_message = init_dictionaries(network_topology[my_addr])
hello_receipt_expiry = None

while True:
    try:
        forwarding_table = find_shortest_path_and_return_forwarding_table(network_topology)

        # send Hello Message every 10 seconds to neighbors
        time_now = epoch_time_in_milliseconds_now()
        if  time_now % 10000 == 0:
            hello_receipt_expiry = time_now + 5000 # 5 seconds for neighbors to send an ack
            neighboring_nodes = network_topology[my_addr]
            send_hello_message_to_neighbors(my_addr, neighboring_nodes)

        packet, sender_address = sock.recvfrom(8192) # Buffer size is 8192. Change as needed
        sender_full_address = str(sender_address[0]) + ':' + str(sender_address[1])
        if packet:
            packet_type, time_to_live, routetrace_ip, routetrace_port, dest_ip, dest_port = parse_packet(packet)
            
            if packet_type == Packet_Type.HELLO_MESSAGE.value:
                received_hello_message[sender_full_address] = True

            if packet_type == Packet_Type.ROUTE_TRACE.value:
                if time_to_live == 0:
                    send_routetrace_packet(time_to_live, emulator_ip, emulator_port, dest_ip, dest_port)
                else:
                    packet = decrement_time_to_live(packet_type, time_to_live, routetrace_ip, routetrace_port, dest_ip, dest_port)
                    dest_addr = dest_ip + ':' + str(dest_port)
                    next_hop = forwarding_table[dest_addr]
                    sock.sendto(packet, (next_hop.split(':')[0], next_hop.split(':')[0]))

        if hello_receipt_expiry is not None and epoch_time_in_milliseconds_now() > hello_receipt_expiry:
            network_topology = update_network_topology(received_hello_message)
            forwarding_table = find_shortest_path_and_return_forwarding_table(network_topology)
            neighboring_nodes = network_topology[my_addr]
            send_link_state_message_to_neighbors(my_addr, neighboring_nodes)

    except:
        pass