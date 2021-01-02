DOCKER_REPO_NAME ?= shadowreaver/
DOCKER_CONTAINER_NAME ?= crypto-signal
DOCKER_IMAGE_NAME ?= ${DOCKER_REPO_NAME}${DOCKER_CONTAINER_NAME}
GIT_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
INSTALLDIR ?= /opt/cryptosignal

build:
	docker build -t ${DOCKER_IMAGE_NAME}:${GIT_BRANCH} .
	docker tag ${DOCKER_IMAGE_NAME}:${GIT_BRANCH} ${DOCKER_IMAGE_NAME}:latest

run:
	docker run -it --rm -v $PWD/config.yml:/app/config.yml ${DOCKER_IMAGE_NAME}

install:
	install -m0644 -D config.yml ${INSTALLDIR}/config.yml
	install -m0644 -D docker-compose.yml ${INSTALLDIR}/docker-compose.yml
	install -m0644 -D systemd.service /etc/systemd/system/${DOCKER_CONTAINER_NAME}.service
	sed -i "s|WORKINGDIR|${INSTALLDIR}|" /etc/systemd/system/${DOCKER_CONTAINER_NAME}.service
	systemctl daemon-reload
