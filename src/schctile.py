from base_import import *

import schcmsg
from math import floor

#---------------------------------------------------------------------------

class TileList():

    # XXX it is almost about the sender side, should be moved into schcsend.py.
    # XXX may it be used in NO-ACK ?
    def __init__(self, rule, packet):
        self.rule = rule
        t_size = rule.tile_size
        t_init_num = schcmsg.get_MAX_WIND_FCN(rule)
        self.tile_list = []
        w_num = 0
        t_num = t_init_num
        # make tiles
        bb = BitBuffer(packet)
        num_full_size_tiles = floor(bb.count_added_bits()/rule.tile_size)
        last_tile_size = bb.count_added_bits() - (rule.tile_size *
                                                  num_full_size_tiles)
        assert last_tile_size >= 0
        tiles = [ bb.get_bits_as_buffer(rule.tile_size)
                 for _ in range(num_full_size_tiles) ]
        if last_tile_size > 0:
            tiles.append(bb.get_bits_as_buffer(last_tile_size))
        # make a tile_list
        for t in tiles:
            tile_obj = {
                    "w-num": w_num,
                    "t-num": t_num,
                    "tile": t,
                    "sent": False,
                    "ready_to_be_sent": False,
                }
            self.tile_list.append(tile_obj)
            if t_num == 0:
                t_num = t_init_num
                w_num += 1
            else:
                t_num -= 1
        print("DEBUG: tile_list:")
        for i in self.tile_list:
            print("DEBUG:  ", i)

    def get_tiles(self, mtu_size):
        '''
        return the tiles containing the contiguous tiles fitting in mtu_size.
        And, remaiing nb_tiles to be sent in tile_list.
        '''
        max_tiles = int((mtu_size - schcmsg.get_header_size(self.rule)) /
                     self.rule.tile_size)
        tiles = []
        t_prev = None
        for i in range(len(self.tile_list)):
            t = self.tile_list[i]
            if t_prev and t_prev["t-num"] + 1 < t["t-num"]:
                break
            if t["sent"] == False:
                tiles.append(t)
                assert t["ready_to_be_sent"] == False
                t["ready_to_be_sent"] = True
                t_prev = t
            if len(tiles) == max_tiles:
                break
        if len(tiles) == 0:
            return None, 0
        # return tiles and the remaining bits
        nb_remaining_tiles = len(
                [ _ for _ in self.tile_list if _["ready_to_be_sent"] == False ])
        return tiles, nb_remaining_tiles

    def get_all_tiles(self):
        return self.tile_list

    def update_sent_flag(self):
        for t in self.tile_list:
            if t["ready_to_be_sent"] == True:
                t["sent"] = True

    @staticmethod
    def get_bytearray(tiles):
        buf = BitBuffer()
        for t in tiles:
            buf += t["tile"]
        return buf.get_content()

