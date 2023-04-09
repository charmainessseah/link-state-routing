import argparse
import socket
import sys

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

# implements link-state routing protocol and sets up a shortest path
# forwarding table between nodes in the specified network topology
def create_routes(network_topology):
    # 1) dijkstra's algorithm
    adjacency_matrix, index_to_node_map = construct_adjacency_matrix(network_topology)
    dijkstra(adjacency_matrix, 0, index_to_node_map)

    # 2) construct forwarding table

# creates the forwarding table
def build_route_table():
    pass

args = parse_command_line_args()
emulator_port = args.port
topology_filename = args.filename

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
emulator_hostname = socket.gethostname()
sock.bind((emulator_hostname, emulator_port))

network_topology = read_topology(topology_filename)
create_routes(network_topology)