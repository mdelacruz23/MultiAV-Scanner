/kaniko/executor \
--cache=true \
--cache-ttl=24h \
--build-arg version_string=$1 \
--build-arg CI_PROJECT_NAME=$2 \
--context dir://./ \
--dockerfile Dockerfile-mvs \
--destination $3
