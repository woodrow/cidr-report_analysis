#!/usr/bin/env python

# derived from Jon Oberheide's pybgpdump.py

import gzip, bz2
import dpkt

BZ2_MAGIC = '\x42\x5a\x68'
GZIP_MAGIC = dpkt.gzip.GZIP_MAGIC
MRT_HEADER_LEN = dpkt.mrt.MRTHeader.__hdr_len__
#SUPPORTED_AFIS = ( dpkt.mrt.AFI_IPv4, )
#SUPPORTED_TYPES = ( dpkt.bgp.UPDATE, )

class BGPTable:
    def __init__(self, filename):
        f = file(filename, 'rb')
        hdr = f.read(max(len(BZ2_MAGIC), len(GZIP_MAGIC)))
        f.close()

        if filename.endswith('.bz2') and hdr.startswith(BZ2_MAGIC):
            self.fobj = bz2.BZ2File
        elif filename.endswith('.gz') and hdr.startswith(GZIP_MAGIC):
            self.fobj = gzip.GzipFile
        else:
            self.fobj = file
        self.open(filename)

    def open(self, filename):
        self.f = self.fobj(filename, 'rb')

    def close(self):
        self.f.close()
        raise StopIteration

    def __iter__(self):
        return self

    def next(self):
        while True:
            s = self.f.read(MRT_HEADER_LEN)
            if len(s) < MRT_HEADER_LEN:
                self.close()

            mrt_h = dpkt.mrt.MRTHeader(s)
            s = self.f.read(mrt_h.len)
            if len(s) < mrt_h.len:
                self.close()

# This could be optimized by selecting the vantage point of interest from the Peer Index Table and pushing the peer of interest down into the processing of RIBs

            if mrt_h.type == dpkt.mrt.TABLE_DUMP:
                if mrt_h.subtype == dpkt.mrt.AFI_IPv4:
                    td = dpkt.mrt.TableDump(s)
                else:
                    continue
            elif mrt_h.type == dpkt.mrt.TABLE_DUMP_V2:
                if mrt_h.subtype == dpkt.mrt.TABLE_DUMP_V2_PEER_INDEX_TABLE:
                    table_index = dpkt.mrt.TableDump2_Index(s)
                    continue
                elif mrt_h.subtype == dpkt.mrt.TABLE_DUMP_V2_RIB_IPV4_UNICAST:
                    td = dpkt.mrt.TableDump2_RIB(s)
                else:
                    continue
            else:
                continue

            break
        return (mrt_h, td)
