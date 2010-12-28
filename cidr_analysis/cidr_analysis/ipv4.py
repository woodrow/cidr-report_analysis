def dotquad_to_int(ipv4_str):
    """Convert an IPv4 address in dotted quad string representation to 32-bit
    integer representation.

    """
    ipv4_int = 0
    byte_str_list = ipv4_str.split('.')
    if len(byte_str_list) != 4:
        raise ValueError("dotquad_to_int takes address in dotted quad format")
    for pos, byte_str in enumerate(byte_str_list):
        ipv4_int |= int(byte_str) << (3-pos)*8
    return ipv4_int

def int_to_dotquad(ipv4_int):
    """Convert an IPv4 address in 32-bit integer representation to
    dotted quad string representation.

    """
    octets = []
    for i in xrange(4):
        octets.append(str(ipv4_int & 0xFF))
        ipv4_int >>= 8
    octets.reverse()
    return '.'.join(octets)
