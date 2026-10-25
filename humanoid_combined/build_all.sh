#!/bin/bash
# build the 5 test variants; each build runs hm_check.py and returns its rc
# output names are English (Boss 25/10): --tier rut_gon|chi_tiet → simplified|detailed, --gioi nam|nu → male|female
cd "$(dirname "$0")"; mkdir -p out
for t in rut_gon chi_tiet; do for g in nam nu; do
  h=$([ $g = nam ] && echo short || echo bob)
  tn=$([ $t = rut_gon ] && echo simplified || echo detailed); gn=$([ $g = nam ] && echo male || echo female)
  python3 -W ignore hm.py --tier $t --gioi $g --out out/${tn}_$gn --hair $h > out/${tn}_$gn.log 2>&1; echo "$tn $gn rc=$?"
done; done
python3 -W ignore hm.py --tier rut_gon --gioi nam --faceless --out out/simplified_male_faceless > out/simplified_male_faceless.log 2>&1; echo "simplified male faceless rc=$?"
