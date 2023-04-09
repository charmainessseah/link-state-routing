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

NO_PARENT = -1

# A utility function to print
# the constructed distances
# array and shortest paths
def print_solution(start_vertex, distances, parents):
    n_vertices = len(distances)
    print("Vertex\t Distance\tPath")
     
    for vertex_index in range(n_vertices):
        if vertex_index != start_vertex:
            print("\n", start_vertex + 1, "->", vertex_index + 1, "\t\t", distances[vertex_index], "\t\t", end="")
            print_path(vertex_index, parents)

# Function to print shortest path
# from source to current_vertex
# using parents array
def print_path(current_vertex, parents):
    # Base case : Source node has
    # been processed
    if current_vertex == NO_PARENT:
        return
    print_path(parents[current_vertex], parents)
    print(current_vertex + 1, end=" ")

def dijkstra(adjacency_matrix, start_vertex):
    n_vertices = len(adjacency_matrix[0])
 
    # shortest_distances[i] will hold the
    # shortest distance from start_vertex to i
    shortest_distances = [sys.maxsize] * n_vertices
 
    # added[i] will true if vertex i is
    # included in shortest path tree
    # or shortest distance from start_vertex to
    # i is finalized
    added = [False] * n_vertices
 
    # Initialize all distances as
    # INFINITE and added[] as false
    for vertex_index in range(n_vertices):
        shortest_distances[vertex_index] = sys.maxsize
        added[vertex_index] = False
         
    # Distance of source vertex from
    # itself is always 0
    shortest_distances[start_vertex] = 0
 
    # Parent array to store shortest
    # path tree
    parents = [-1] * n_vertices
 
    # The starting vertex does not
    # have a parent
    parents[start_vertex] = NO_PARENT
 
    # Find shortest path for all
    # vertices
    for i in range(1, n_vertices):
        # Pick the minimum distance vertex
        # from the set of vertices not yet
        # processed. nearest_vertex is
        # always equal to start_vertex in
        # first iteration.
        nearest_vertex = -1
        shortest_distance = sys.maxsize
        for vertex_index in range(n_vertices):
            if not added[vertex_index] and shortest_distances[vertex_index] < shortest_distance:
                nearest_vertex = vertex_index
                shortest_distance = shortest_distances[vertex_index]
 
        # Mark the picked vertex as
        # processed
        added[nearest_vertex] = True
 
        # Update dist value of the
        # adjacent vertices of the
        # picked vertex.
        for vertex_index in range(n_vertices):
            edge_distance = adjacency_matrix[nearest_vertex][vertex_index]
             
            if edge_distance > 0 and shortest_distance + edge_distance < shortest_distances[vertex_index]:
                parents[vertex_index] = nearest_vertex
                shortest_distances[vertex_index] = shortest_distance + edge_distance
 
    print_solution(start_vertex, shortest_distances, parents)

def construct_adjacency_matrix(network_topology):
    # need to assign each ip:port node a number for the adjacency matrix
    num_nodes = len(network_topology)
    index_to_node = {}
    node_to_index = {}
    index = 0
    for node in network_topology:
        node_to_index[node] = index
        index_to_node[index] = node
        index += 1
    
    adjacency_matrix = [[0 for column in range(num_nodes)]
                      for row in range(num_nodes)]
    
    for node in network_topology:
        node_index = node_to_index[node]
        neighboring_nodes = network_topology[node]
        for neighbor in neighboring_nodes:
            neighbor_index = node_to_index[neighbor]
            adjacency_matrix[node_index][neighbor_index] = 1
            adjacency_matrix[neighbor_index][node_index] = 1

    print(adjacency_matrix)
    return adjacency_matrix



# implements link-state routing protocol and sets up a shortest path
# forwarding table between nodes in the specified network topology
def create_routes(network_topology):
    # 1) dijkstra's algorithm
    adjacency_matrix = construct_adjacency_matrix(network_topology)
    dijkstra(adjacency_matrix, 0)

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