#!/usr/bin/env python2.6

def dotquad_to_int(ipv4_str):
    """Convert an IPv4 address in dotted quad string representation to 32-bit
    integer representation.

    """
    byte_str_list = ipv4_str.split('.')
    if len(byte_str_list) != 4:
        raise ValueError("ipv4_str must be in dotted quad format")
    ipv4_int = 0
    for pos, byte_str in enumerate(byte_str_list):
        if 0 <= int(byte_str) <= 255:
            ipv4_int |= int(byte_str) << (3-pos)*8
        else:
            raise ValueError(
                "ipv4_str octet '{0}' is out of range 0..255".format(
                int(byte_str)))
    return ipv4_int

def int_to_dotquad(ipv4_int):
    """Convert an IPv4 address in 32-bit integer representation to
    dotted quad string representation.

    """
    if ipv4_int < 0 or ipv4_int > 0xFFFFFFFF:
        raise ValueError(
            "ipv4_int '0x{0:X}' is out of range 0..0xFFFFFFFF".format(ipv4_int))
    octets = []
    for i in xrange(4):
        octets.append(str(ipv4_int & 0xFF))
        ipv4_int >>= 8
    octets.reverse()
    return '.'.join(octets)

def cidr_range(ipv4_prefix_str):
    """Returns a tuple containing the minimum and maximum address that lie
    within a the given CIDR address block.
    i.e. cidr_range('192.168.1.0/24') returns ('192.168.1.0', '192.168.1.255')

    """
    (prefix, prefix_len) = ipv4_prefix_str.split('/')
    prefix_len = int(prefix_len)
    if not (0 <= prefix_len <= 32):
        raise ValueError(
            "prefix length '{0}' is out of range 0..32".format(prefix_len))
    prefix = dotquad_to_int(prefix)
    return (int_to_dotquad(prefix & 0xFFFFFFFF << 32 - prefix_len),
        int_to_dotquad(prefix | 0xFFFFFFFF >> prefix_len))
