# link-state-routing

## hello message packet structure

### header - cIIIII
1) packet type - 1 byte
2) ip (source)
- ip part 1 (4 bytes) 
- ip part 2 (4 bytes)
- ip part 3 (4 bytes)
- ip part 4 (4 bytes)
3) port (source) - 4 bytes
4) nothing
5) nothing
6) 'hello' payload

## link state message packet structure

### header
1) packet type - cIIIIIII
2) ip of the node that created the message
- ip part 1 (4 bytes) 
- ip part 2 (4 bytes)
- ip part 3 (4 bytes)
- ip part 4 (4 bytes)
3) port of the node that created the message
4) sequence number
5) time to live
# put this info in the payload
6) list of directly connected neighbors to that node, with the cost of the link to each one

## routetrace message packet structure
1) packet type - cIIIIIIIIII
2) source ip of the node that created the message
- ip part 1 (4 bytes) 
- ip part 2 (4 bytes)
- ip part 3 (4 bytes)
- ip part 4 (4 bytes) 
3) source port of the node that created the message
4) nothing
5) time to live
4) dest ip of the node that created the message
- ip part 1 (4 bytes) 
- ip part 2 (4 bytes)
- ip part 3 (4 bytes)
- ip part 4 (4 bytes) 
5) dest port of the node that created the message

questions:
- what is the ttl when sending a new link state packet
- format for sending neighboring nodes and cost of a link state packet