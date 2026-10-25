#!/bin/bash
# Dựng phiên bản chi tiết: [CO=1] bash build.sh nam|nu  ⇒ out_male|out_female/ (CO=1 ⇒ out_<male|female>_hold/, tay NẮM + socket cam_*)
# cửa check_lpd.py chạy cuối (+ check_hold.py khi CO>0), trượt ⇒ exit 1
set -e; cd "$(dirname "$0")"; g=$1; T=BODY_M; [ "$g" = nu ] && T=BODY_F
gd=male; [ "$g" = nu ] && gd=female   # folder names are English (Boss 25/10); the --gioi value stays nam|nu
D=out_$gd; [ "${CO:-0}" != 0 ] && D=out_${gd}_hold; [ -n "${HAU_TO:-}" ] && D=${D}_$HAU_TO   # bản thử A/B ra thư mục riêng
mkdir -p $D
GIOI=$g python3 geometry.py $D/geometry.json > $D/geometry.log
GIOI=$g blender -b -P blender_build.py -- $D/geometry.json $D > $D/blender.log 2>&1
python3 check_lpd.py $D/$T.glb $g
if [ "${CO:-0}" != 0 ]; then GIOI=$g python3 check_hold.py; GIOI=$g python3 hair_outfit.py $D > $D/hair_outfit.log; tail -1 $D/hair_outfit.log; fi
