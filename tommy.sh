#!/bin/bash

#mpirun --version
#which ucc_info
#ucc_info -v
#which ucx_info
#ucx_info -v

#env | grep HPCX
#ls ${HPCX_OSU_DIR}

MPIRUN=`which mpirun`
HCA=mlx5_2:1
PML="--mca pml ucx -x UCX_NET_DEVICES=${HCA} "

#COLL_TUNED="--mca coll tuned,basic,libnbc --mca coll_tuned_enable 1 "
COLL_UCC="--mca coll ucc,basic,libnbc --mca coll_ucc_enable 1 "
#COLL_UCC+="-x UCC_TL_SHM_SET_PERF_PARAMS=0 -x UCC_TL_SHM_BASE_TREE_ONLY=0 -x UCC_TL_SHM_REDUCE_BASE_RADIX=16 -x UCC_TL_SHM_REDUCE_TOP_RADIX=8 -x UCC_TL_SHM_BCAST_BASE_RADIX=64 -x UCC_TL_SHM_BCAST_TOP_RADIX=4 -x UCC_TL_SHM_BCAST_ALG=rr "

#COLL_HCOLL="--mca coll hcoll,basic,libnbc --mca coll_hcoll_enable 1 "

#LD_PRELOAD="-x LD_PRELOAD=/home/tomislavj/ucx-v1.18-build/install/lib/libucs.so:/home/tomislavj/ucx-v1.18-build/install/lib/libucm.so:/home/tomislavj/ucx-v1.18-build/install/lib/libuct.so:/home/tomislavj/ucx-v1.18-build/install/lib/libucp.so:/home/tomislavj/ucc_private-build/install/lib/libucc.so "

EXE="/lustre/nsarkauskas/stack/build-arm/omb/libexec/osu-micro-benchmarks/mpi/collective/osu_allreduce -f"

for i in {4..144..4}
do
        NP="--np $i "
        MAP="--map-by ppr:$(($i/2)):socket --rank-by core " #--report-bindings "
        CMD="$MPIRUN ${NP} ${MAP} ${PML} -x UCX_NET_DEVICES=$HCA -x UCX_WARN_UNUSED_ENV_VARS=n ${COLL_TUNED} ${COLL_UCC} ${COLL_HCOLL} ${LD_PRELOAD} ${EXE}"
        echo $CMD
        $CMD
done


