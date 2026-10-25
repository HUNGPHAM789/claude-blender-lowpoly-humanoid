"""CỤC ĐÁ NHỎ một đơn vị tài nguyên (Boss 23/10: gùi «small rocks ở trong… scaleable cho food, rocks, fishes»). Tâm ở gốc, bán kính bao
≤ kho.R_DA (0,065) ⇒ xếp đống theo settler-storage/storage.py o_chua_dong không chồng. Cảnh nhân bản: trong gùi + trong thùng kho."""
from lpms_helpers import *
META = dict(ten="pebble", dat=False, ngan_sach=60)


def build():
    return {"da": khoi_meo((0, 0, 0), 0.054, "da", seed=91, meo=0.15, n=12, det=(1.0, 0.95, 0.8))}
