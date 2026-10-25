"""MEAT CUT small variant — flat slab with fat strip + twine (geometry in meat_piece.lat())."""
import os, sys
sys.path.insert(0, os.path.expanduser("~/projects/lpm-faceless-humanoid/lpms/assets"))
import meat_piece

META = dict(ten="meat_piece_small", dat=True, ngan_sach=80)


def build():
    return meat_piece.lat()
