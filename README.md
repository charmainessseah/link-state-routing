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