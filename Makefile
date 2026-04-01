REGISTRY=registry.jadeuc.com/gap/dune/multiav-scan-aws-ec2-objects/multiav-scan
# REGISTRY=registry.master.forcenex.us/gap/data-movement/multiav-scan-aws-ec2-objects/multiav-scan
VERSION=v7.0.2
IMAGE_NAME=local/mvs
CREDS_SERVICE_IMAGE=amazon/amazon-ecs-local-container-endpoints
REGISTRY_SERVICE=registry.jadeuc.com/gap/dune/multiav-scan-aws-ec2-objects/multiav-scan:v7.0.2
CLAMDIR=/srv/mvs-log2/clamav
MCAFEEDIR=/srv/mvs-log2/mcafee
SCAN_HOST_NAME="scan-service01"

build:
	DOCKER_BUILDKIT=1 docker build -f Dockerfile-mvs \
		-t $(IMAGE_NAME):latest .

build-version:
	DOCKER_BUILDKIT=1 docker build -f Dockerfile-mvs \
		-t $(IMAGE_NAME):$(VERSION) .

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker logs -f mvs

all: down build up logs

into:
	docker exec -u root -ti mvs /bin/bash

tag:
	docker tag $(IMAGE_NAME) $(REGISTRY)

register:
	docker push $(REGISTRY):latest

latest-version: build tag register

run-latest:
	[ -d ${CLAMDIR} ] || mkdir -p ${CLAMDIR} && \
	chown clamav:clamav ${CLAMDIR} && \
	[ -d ${CLAMDIR} ] || mkdir -p ${CLAMDIR} && \
	docker run --privileged -v ${HOME}/.aws:/root/.aws:ro -v /srv/mvs-log2:/var/log/:rw  -v /srv/scan:/var/scan/:rw --restart unless-stopped --cpus=$(cpu) --memory=$(mem) --memory-swap=$(swapmem) -p 8009:8009 -p 2812:2812 -d -h ${SCAN_HOST_NAME}  --name mvs $(REGISTRY)

login:
	docker login -u $(u) -p $(p) registry.master.forcenex.us

tag-version:
	docker tag $(IMAGE_NAME):$(VERSION) $(REGISTRY):$(VERSION)

register-version:
	docker push $(REGISTRY):$(VERSION)

version: build-version tag-version register-version

monit:
	open http://localhost:2812

volumes:
	docker volume create --driver local --opt type=none --opt device=/root/.aws --opt o=bind aws
	docker volume create --driver local --opt type=none --opt device=/var/log --opt o=bind logs
	docker volume create --driver local --opt type=none --opt device=/var/scan --opt o=bind scan

kill-all:
	docker kill $$(docker ps -q)

remove-container:
	docker rm mvs
