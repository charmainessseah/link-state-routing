import argparse
import copy
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
    HELLO_ACK = 'A'

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

def construct_forwarding_table(all_paths):
    # { dest: next_hop }
    forwarding_table = {}

    for path in all_paths:
        dest = path[len(path) - 1]
        next_hop = path[1]
        forwarding_table[dest] = next_hop

    return forwarding_table

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

    print('ADJACENCY MATRIX: ')
    print(adjacency_matrix)
    return adjacency_matrix, index_to_node_map, node_to_index_map

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

    print('-----------------------------')
    print('INCOMING PACKET:')
    print('packet type: ', packet_type)
    print('source ip: ', source_ip, ', source port: ', source_port)
    print('dest ip: ', dest_ip, ', dest port: ', dest_port)
    print('sequence number: ', sequence_number)
    print('time to live: ', ttl)
    print('data: ', data)
    print('-----------------------------')
    
    return packet_type, source_ip, source_port, sequence_number, time_to_live, dest_ip, dest_port, data

def send_routetrace_packet(packet_type, source_ip, source_port, sequence_number, time_to_live, dest_ip, dest_port, data, emulator_ip, emulator_port):
    print('--------------------------------------')
    print('SENDING ROUTETRACE PACKET:')
    print('packet type: ', packet_type)
    print('emulator ip: ', emulator_ip, ', emulator port: ', emulator_port)
    print('source ip: ', source_ip, ', source port: ', source_port)
    print('dest hostname: ', dest_ip, ', dest port: ', dest_port)
    # print('sequence number: ', sequence_number) unused field in routetrace packets
    print('time to live: ', time_to_live)
    print('--------------------------------------')

    emulator_ip_a = emulator_ip.split('.')[0]
    emulator_ip_b = emulator_ip.split('.')[1]
    emulator_ip_c = emulator_ip.split('.')[2]
    emulator_ip_d = emulator_ip.split('.')[3]

    dest_ip_a = dest_ip.split('.')[0]
    dest_ip_b = dest_ip.split('.')[1]
    dest_ip_c = dest_ip.split('.')[2]
    dest_ip_d = dest_ip.split('.')[3]
   
    header = struct.pack(
        '!cIIIIIIIIIIII',
        Packet_Type.ROUTE_TRACE.value.encode('ascii'),
        emulator_ip_a, emulator_ip_b, emulator_ip_c, emulator_ip_d,
        emulator_port,
        0, # placeholder value
        time_to_live,
        dest_ip_a, dest_ip_b, dest_ip_c, dest_ip_d, 
        dest_port
    )
    data = ''.encode()
    packet = header + data

    global sock
    # send the packet back to where it came from
    sock.sendto(packet, (source_ip, source_port))

def send_hello_ack(my_addr, dest_addr):
    print('SENDING HELLO ACK')
    source_ip = my_addr.split(' ')[0]
    source_ip_a = source_ip.split('.')[0]
    source_ip_b = source_ip.split('.')[1]
    source_ip_c = source_ip.split('.')[2]
    source_ip_d = source_ip.split('.')[3]
    source_port = my_addr.split(' ')[1]  

    dest_ip = dest_addr[0]
    dest_port = dest_addr[1]

    header = struct.pack(
        '!cIIIIIIIIIIII',
        Packet_Type.HELLO_ACK.value.encode('ascii'),
        source_ip_a, source_ip_b, source_ip_c, source_ip_d,
        source_port,
        0, 0, 0, 0, 0, 0, 0, # placeholder values
    )
    data = 'ack'.encode()
    packet = header + data

    global sock
    sock.sendto(packet, (dest_ip, dest_port))

def send_hello_message_to_neighbors(my_addr, neighboring_nodes):
    print('SENDING HELLO MESSAGE')
    source_ip = my_addr.split(' ')[0]
    source_ip_a = source_ip.split('.')[0]
    source_ip_b = source_ip.split('.')[1]
    source_ip_c = source_ip.split('.')[2]
    source_ip_d = source_ip.split('.')[3]
    source_port = my_addr.split(' ')[1] 

    for neighbor in neighboring_nodes:
        # print('neighbor: ', neighbor)
        dest_ip = neighbor.split(' ')[0]
        dest_port = neighbor.split(' ')[1]

        header = struct.pack(
            '!cIIIIIIIIIIII',
            Packet_Type.HELLO_MESSAGE.value.encode('ascii'),
            source_ip_a, source_ip_b, source_ip_c, source_ip_d,
            source_port,
            0, 0, 0, 0, 0, 0, 0, # placeholder values
        )
        data = 'hello'.encode()
        packet = header + data

        global sock
        sock.sendto(packet, (dest_ip, dest_port))

def send_link_state_message_to_neighbors(my_addr, neighboring_nodes, sequence_number):
    print('SENDING LSM TO NEIGHBORS')
    source_ip = my_addr.split(' ')[0]
    source_ip_a = source_ip.split('.')[0]
    source_ip_b = source_ip.split('.')[1]
    source_ip_c = source_ip.split('.')[2]
    source_ip_d = source_ip.split('.')[3]
    source_port = my_addr.split(' ')[1] 

    for neighbor in neighboring_nodes:
        print('sending link state message to neighbor: ', neighbor)
        dest_ip = neighbor.split(' ')[0]
        dest_port = neighbor.split(' ')[1]

        # TODO: what should the ttl be?
        ttl = 0

        header = struct.pack('!cIIIIIIIIIIII', 
        Packet_Type.LINK_STATE_MESSAGE.value.encode('ascii'),
        source_ip_a, source_ip_b, source_ip_c, source_ip_d,
        source_port,
        sequence_number,
        time_to_live,
        0, 0, 0 , 0, 0 # placeholder values
        )
        data = pickle.dumps(neighboring_nodes)

        packet = header + data
        
        global sock
        sock.sendto(packet, (dest_ip, dest_port))

# finds the shortest path between all nodes from source to dest
# and returns an updated forwarding table
def find_shortest_path_and_return_forwarding_table(my_addr, network_topology):
    print('FINDING SHORTEST PATH AND BUILDING FORWARDING TABLE')
    adjacency_matrix, index_to_node_map, node_to_index_map = construct_adjacency_matrix(network_topology)
    starting_node = node_to_index_map[my_addr] # this should be the emulator's node
    forwarding_table = dijkstra(adjacency_matrix, starting_node, index_to_node_map)

    return forwarding_table

def init_dictionaries(network_topology, list_of_neighbors):
    print('INIT DICTIONARIES')
    available_nodes = {}
    received_hello_message = {}

    for node in network_topology:
        available_nodes[node] = True
        
    for node in list_of_neighbors:
        received_hello_message = False

    return available_nodes, received_hello_message

def epoch_time_in_milliseconds_now():
    time_now_in_milliseconds = round(time.time() * 1000)
    # print("Milliseconds since epoch:", time_now_in_milliseconds)
    return time_now_in_milliseconds

def decrement_time_to_live(packet_type, source_ip, source_port, sequence_number, time_to_live, dest_ip, dest_port, data):
    print('decrementing time to live in routetrace packet')
    source_ip_a = source_ip.split('.')[0]
    source_ip_b = source_ip.split('.')[1]
    source_ip_c = source_ip.split('.')[2]
    source_ip_d = source_ip.split('.')[3]

    dest_ip_a = dest_ip.split('.')[0]
    dest_ip_b = dest_ip.split('.')[1]
    dest_ip_c = dest_ip.split('.')[2]
    dest_ip_d = dest_ip.split('.')[3]
   
    header = struct.pack(
        '!cIIIIIIIIIIII',
        Packet_Type.ROUTE_TRACE.value.encode('ascii'),
        source_ip_a, source_ip_b, source_ip_c, source_ip_d,
        source_port,
        sequence_number, # this field is unused 
        time_to_live - 1,
        dest_ip_a, dest_ip_b, dest_ip_c, dest_ip_d, 
        dest_port
    )
    data = ''.encode()
    packet = header + data

    return packet

# key: node
# value: list of neighboring nodes
# all nodes are in string format "ip:port"
# {
#   "ip:port": ["ip:port", "ip:port"]
# }
def update_network_topology(original_network_topology, available_nodes):
    print('UPDATING NETWORK TOPOLOGY')

    updated_network_topology = copy.deepcopy(original_network_topology)
    unavailable_nodes = []

    # remove unavailable node which are keys in the dict
    for node in available_nodes:
        if not available_nodes[node] and node in updated_network_topology:
            updated_network_topology.pop(node)
            unavailable_nodes.append(node)
            
    for node in updated_network_topology:
        neighbors = updated_network_topology[node]
        if node in unavailable_nodes and node in neighbors:
            neighbors.remove(node)

    return updated_network_topology

def forward_link_state_packet_to_neighbors(neighboring_nodes, source_ip, source_port, sequence_number, time_to_live, dest_ip, dest_port, data):
    # we are forwarding the LSM as is that we received from a neighbor
    print('FORWARDING LSM TO NEIGHBORS')

    time_to_live = time_to_live - 1
   
    source_ip_a = source_ip.split('.')[0]
    source_ip_b = source_ip.split('.')[1]
    source_ip_c = source_ip.split('.')[2]
    source_ip_d = source_ip.split('.')[3]

    for neighbor in neighboring_nodes:
        print('forwarding link state message to neighbor: ', neighbor)
        dest_ip = neighbor.split(' ')[0]
        dest_port = neighbor.split(' ')[1]

        header = struct.pack('!cIIIIIIIIIIII', 
        Packet_Type.LINK_STATE_MESSAGE.value.encode('ascii'),
        source_ip_a, source_ip_b, source_ip_c, source_ip_d,
        source_port,
        sequence_number,
        time_to_live,
        0, 0, 0 , 0, 0 # placeholder values
        )
        data = pickle.dumps(neighboring_nodes)

        packet = header + data
        
        global sock
        sock.sendto(packet, (dest_ip, dest_port))

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
my_addr = '1.0.0.0:1' # TODO: remove this

original_network_topology = read_topology(topology_filename)
lsp_sequence_number = -1
link_state_packet_data = None

# active_neighbors = { ip:port : True/ False }
# we will init all neighbors to be active initially
# received_hello_message = { ip:port : False }
available_nodes, received_hello_message = init_dictionaries(original_network_topology, original_network_topology[my_addr])
hello_receipt_expiry = None

network_topology = copy.deepcopy(original_network_topology)
while True:
    try:
        forwarding_table = find_shortest_path_and_return_forwarding_table(my_addr, network_topology)

        # send Hello Message every 10 seconds to neighbors
        time_now = epoch_time_in_milliseconds_now()
        if (hello_receipt_expiry is None or time_now > hello_receipt_expiry) and time_now % 10000 == 0:
            hello_receipt_expiry = time_now + 5000 # 5 seconds for neighbors to send an ack
            neighboring_nodes = network_topology[my_addr]
            send_hello_message_to_neighbors(my_addr, neighboring_nodes)

        packet, sender_address = sock.recvfrom(8192) # Buffer size is 8192. Change as needed
        sender_full_address = str(sender_address[0]) + ':' + str(sender_address[1])

        if packet:
            packet_type, source_ip, source_port, sequence_number, time_to_live, dest_ip, dest_port, data = parse_packet(packet)
            
            if packet_type == Packet_Type.HELLO_MESSAGE.value:
                print('received hello ack from: ', sender_full_address)
                send_hello_ack(my_addr, sender_full_address)

                node_came_alive = False
                for node in available_nodes:
                    if not available_nodes[node]:
                        node_came_alive = True # change in node state
                        available_nodes[node] = True
                        
                if node_came_alive:
                    network_topology = update_network_topology(original_network_topology, available_nodes)
                    forwarding_table = find_shortest_path_and_return_forwarding_table(my_addr, network_topology)
                    neighboring_nodes = network_topology[my_addr]

                    send_link_state_message_to_neighbors(my_addr, neighboring_nodes, lsp_sequence_number + 1)
                    lsp_sequence_number += 1

            if packet_type == Packet_Type.HELLO_ACK.value:
                print('received hello packet from: ', sender_full_address)
                available_nodes[sender_full_address] = True
                network_topology = update_network_topology(original_network_topology, available_nodes)
                forwarding_table = find_shortest_path_and_return_forwarding_table(my_addr, network_topology)
                neighboring_nodes = network_topology[my_addr]
                received_hello_message[sender_full_address] = True

            if packet_type == Packet_Type.LINK_STATE_MESSAGE.value:
                print('received link state packet from: ', sender_full_address)
                curr_node = source_ip + ':' + str(source_port)
                print('source of link state packed originally from: ', curr_node)
                if link_state_packet_data is None or sequence_number > lsp_sequence_number:
                    lsp_sequence_number = sequence_number

                    senders_available_neighboring_nodes = pickle.loads(data)
                    original_senders_available_nodes = original_network_topology[curr_node]
                    nodes_that_went_down = [node for node in original_senders_available_nodes if node not in senders_available_neighboring_nodes]
                    
                    for node in nodes_that_went_down:
                        available_nodes[node] = False
                        network_topology = update_network_topology(original_network_topology, available_nodes)
                        forwarding_table = find_shortest_path_and_return_forwarding_table(my_addr, network_topology)
                        # just forward to all original neighbors even though some may be down
                        neighboring_nodes = original_network_topology[my_addr]
                        forward_link_state_packet_to_neighbors(neighboring_nodes, source_ip, source_port, sequence_number, time_to_live, dest_ip, dest_port, data)

                    if time_to_live == 0:
                        link_state_packet_data = None

            if packet_type == Packet_Type.ROUTE_TRACE.value:
                print('received routetrace packet from:', sender_full_address)
                if time_to_live == 0:
                    print('time to live is 0')
                    send_routetrace_packet(packet_type, emulator_ip, emulator_port, sequence_number, time_to_live, dest_ip, dest_port, data, emulator_ip, emulator_port)
                else:
                    packet = decrement_time_to_live(source_ip, source_port, sequence_number, time_to_live, dest_ip, dest_port, data)
                    dest_addr = dest_ip + ':' + str(dest_port)
                    next_hop = forwarding_table[dest_addr]
                    print('TTL is not 0 - forwarding routetrace packet to next hop: ', next_hop)
                    sock.sendto(packet, (next_hop.split(':')[0], next_hop.split(':')[0]))

        if hello_receipt_expiry is not None and epoch_time_in_milliseconds_now() > hello_receipt_expiry:
            node_went_down = False
            for node in available_nodes:
                if available_nodes[node] and not received_hello_message[node]:
                    node_went_down = True # change in node status
                    available_nodes[node] = False

            if node_went_down:
                network_topology = update_network_topology(original_network_topology, available_nodes)
                forwarding_table = find_shortest_path_and_return_forwarding_table(my_addr, network_topology)
                neighboring_nodes = network_topology[my_addr]

                send_link_state_message_to_neighbors(my_addr, neighboring_nodes, lsp_sequence_number + 1)
                lsp_sequence_number += 1

            for node in received_hello_message:
                print('resetting received_hello_messages to all false')
                received_hello_message[node] = False  

    except:
        pass