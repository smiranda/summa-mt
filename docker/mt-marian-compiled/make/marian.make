# -*- mode: makefile-gmake; indent-tabs-mode: true; tab-width: 4 -*-

# build marian

# NOTE: MARIAN_COMMIT is used only with newly cloned repositories.
# For existing repositories, we use whatever the current state of the
# respective repository is at the time.

MARIAN_COMMIT = ede2932b426f233829a25e715e7c8af11da37ff0
MARIAN_GITHUB_URL = http://github.com/marian-nmt/marian-dev.git
MARIAN_REPO_ROOT = ${PWD}/marian-dev
MARIAN_BUILD_DIR = ${PWD}/build/marian-dev

.PHONY: marian
marian: CMAKE_FLAGS  =-DUSE_STATIC_LIBS=on 
marian: CMAKE_FLAGS +=-DCOMPILE_CUDA=off
marian: CMAKE_FLAGS +=-DBUILD_ARCH=x86-64 
marian: CMAKE_FLAGS +=-DCMAKE_VERBOSE_MAKEFILE=on
marian: CMAKE_FLAGS +=-DCMAKE_INSTALL_PREFIX=${PWD}/engine
marian: ${MARIAN_BUILD_DIR}/marian-server

${MARIAN_BUILD_DIR}/marian-server: ${MARIAN_REPO_ROOT}/CMakeLists.txt
	-rm -r ${@D}
	mkdir -p ${@D}
	cd ${@D} && cmake ${CMAKE_FLAGS} ${MARIAN_REPO_ROOT} && make -j

${MARIAN_REPO_ROOT}/CMakeLists.txt:
	mkdir -p $(dir ${@D})
	[ -d ${@D} ] || git clone ${MARIAN_GITHUB_URL} ${@D}
	cd ${@D} && git fetch && git checkout ${MARIAN_COMMIT}

${INSTALL_PREFIX}/bin/marian-decoder: ${INSTALL_PREFIX}/bin/marian-server
	mkdir -p ${@D}
	cp ${MARIAN_BUILD_DIR}/${@F} $@

${INSTALL_PREFIX}/bin/marian-scorer: ${INSTALL_PREFIX}/bin/marian-server
	mkdir -p ${@D}
	cp ${MARIAN_BUILD_DIR}/${@F} $@

${INSTALL_PREFIX}/bin/marian-server: | marian
	mkdir -p ${@D}
	cp ${MARIAN_BUILD_DIR}/${@F} $@
