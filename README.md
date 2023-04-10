# link-state-routing

## packet structure

1) ip (source)
- ip part 1 (2 bytes) 'H'
- ip part 2 (2 bytes) 'H'
- ip part 3 (2 bytes) 'H'
- ip part 4 (2 bytes) 'H'
2) port (source) - 4 bytes 'I'
3) sequence number - 4 bytes 'I'
4) time to live - 4 bytes 'I'
5) payload ?