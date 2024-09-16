#!/bin/bash
set -e

WORK_DIR="/lustre/nsarkauskas/stack"

arch=arm
download=1
build_ucx=1
build_ucc=1
build_hcoll=1
build_mpi=1
build_omb=1

BUILD_DIR="$WORK_DIR/build-$arch"



UCX_SRC="$WORK_DIR/ucx"
UCX_DIR="$BUILD_DIR/ucx"
UCX_URL='https://github.com/openucx/ucx.git'
UCX_BRANCH='v1.16.x'
#UCX_BRANCH='master'



UCC_SRC="$WORK_DIR/ucc"
UCC_DIR="$BUILD_DIR/ucc"
#UCC_URL='https://github.com/Mellanox/ucc.git'
#UCC_URL='https://github.com/openucx/ucc.git'
#UCC_URL='https://github.com/nsarka/ucc.git'
UCC_URL='git@github.com:Mellanox-lab/ucc_private.git'
#UCC_BRANCH='v1.2.x'
#UCC_BRANCH='nsarka/doca-cl'
UCC_BRANCH='master'

HCOLL_SRC="$WORK_DIR/hcoll"
HCOLL_DIR="$BUILD_DIR/hcoll"
HCOLL_URL='git@github.com:Mellanox/hcoll.git'
HCOLL_BRANCH='master'


MPI_SRC="$WORK_DIR/ompi"
MPI_DIR="$BUILD_DIR/ompi"
MPI_URL='git@github.com:Mellanox/ompi.git'
#MPI_URL='https://github.com/open-mpi/ompi.git'
MPI_BRANCH='41ba519'



OMB_SRC="$WORK_DIR/omb"
OMB_DIR="$BUILD_DIR/omb"
OMB="osu-micro-benchmarks-7.0.1"
OMB_URL="https://mvapich.cse.ohio-state.edu/download/mvapich"



echo "#### WORK DIR  : $WORK_DIR  ####"
echo "#### BUILD DIR : $BUILD_DIR ####"
cd $WORK_DIR



if [ $download -eq 1 ]; then
    if [ ! -d $UCX_SRC ]; then
        echo "#### Downloading UCX from $UCX_URL:$UCX_BRANCH ####"
        git clone $UCX_URL ucx
	pushd . ; cd ucx ; git checkout $UCX_BRANCH ; popd
    fi
    if [ ! -d $HCOLL_SRC ]; then
        echo "#### Downloading HCOLL from $HCOLL_URL:$HCOLL_BRANCH ####"
        git clone $HCOLL_URL hcoll
	pushd . ; cd hcoll ; git checkout $HCOLL_BRANCH ; popd
    fi
    if [ ! -d $UCC_SRC ]; then
        echo "#### Downloading UCC from $UCC_URL:$UCC_BRANCH ####"
        git clone $UCC_URL ucc
	pushd . ; cd ucc ; git checkout $UCC_BRANCH ; popd
    fi
    if [ ! -d $MPI_SRC ]; then
        echo "#### Downloading MPI from $MPI_URL:$MPI_BRANCH ####"
        git clone $MPI_URL ${MPI_SRC}
        cd ${MPI_SRC}
	git checkout $MPI_BRANCH
        git submodule update --init --recursive
        cd ${WORK_DIR}
    fi
    if [ ! -d $OMB_SRC ]; then
        echo "#### Downloading OMB from $OMB_URL ####"
#git clone -b $OMB_BRANCH $OMB_URL omb
                wget --no-check-certificate ${OMB_URL}/${OMB}.tar.gz
                tar -xvf ${OMB}.tar.gz
                mv ${OMB} ${OMB_SRC}
    fi
fi



if [ $build_ucx -eq 1 ]; then
    echo "#### Building UCX ####"
        cd $UCX_SRC
        git clean -fdx
        ./autogen.sh
        rm -rf ${UCX_DIR}
        mkdir -p ${UCX_DIR}
        cd ${UCX_DIR}



    echo "#### Confguring UCX ####"
    config_opts="--enable-mt --prefix=$UCX_DIR --without-valgrind --without-cuda --with-go=no"
        $UCX_SRC/contrib/configure-opt -C $config_opts



        make -j install
    echo "#### Done Building UCX ####"
fi



if [ $build_ucc -eq 1 ]; then
    echo "#### Building UCC ####"
        cd $UCC_SRC
        git clean -fdx
        ./autogen.sh
        rm -rf ${UCC_DIR}
        mkdir -p ${UCC_DIR}
        cd ${UCC_DIR}



    echo "#### Confguring UCC ####"
    # --enable-debug=yes
    config_opts="--prefix=$UCC_DIR --with-ucx=$UCX_DIR --enable-gtest "
        $UCC_SRC/configure -C $config_opts
        make -j install
    echo "#### Done Building UCC ####"
fi

if [ $build_hcoll -eq 1 ]; then
    echo "#### Building HCOLL ####"
        cd $HCOLL_SRC
        git clean -fdx
        ./autogen.sh
        rm -rf ${HCOLL_DIR}
        mkdir -p ${HCOLL_DIR}
        cd ${HCOLL_DIR}

    echo "#### Confguring HCOLL ####"
    # --enable-debug=yes
    config_opts="--prefix=$HCOLL_DIR --with-ucx=$UCX_DIR "
        $HCOLL_SRC/configure -C $config_opts
        make -j install
    echo "#### Done Building HCOLL ####"
fi


if [ $build_mpi -eq 1 ]; then
    echo "#### Building MPI ####"
        cd $MPI_SRC
        git clean -fdx
        ./autogen.pl
        rm -rf ${MPI_DIR}
        mkdir -p ${MPI_DIR}
        cd ${MPI_DIR}



    echo "#### Confguring MPI ####"
        config_opts="--prefix=$MPI_DIR --with-ucx=$UCX_DIR "
        config_opts+="--with-ucc=$UCC_DIR "
        config_opts+="--with-hcoll=$HCOLL_DIR "
        config_opts+="--without-verbs --with-pmix=internal --with-hwloc=internal "
        $MPI_SRC/configure -C $config_opts



        make -j install
    echo "#### Done Building MPI ####"
fi



if [ $build_omb -eq 1 ]; then
    echo "#### Building OMB ####"
        cd $OMB_SRC
        autoreconf -ivf
        rm -rf ${OMB_DIR}
        mkdir -p ${OMB_DIR}
        cd ${OMB_DIR}



    config_opts="--prefix=$OMB_DIR CC=$MPI_DIR/bin/mpicc CXX=$MPI_DIR/bin/mpicxx"
    $OMB_SRC/configure -C $config_opts



        make -j install
    echo "#### Done Building OMB ####"
fi
