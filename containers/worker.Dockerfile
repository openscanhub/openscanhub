ARG CENTOS_RELEASE=8

FROM quay.io/centos/centos:stream${CENTOS_RELEASE}

# See https://docs.docker.com/engine/reference/builder/#understand-how-arg-and-from-interact
ARG CENTOS_RELEASE
RUN dnf install -y dnf-plugins-core epel-release
RUN if [ $CENTOS_RELEASE == 8 ]; then dnf config-manager --set-enabled powertools; else dnf config-manager --set-enabled crb; fi

WORKDIR /src

ENV PYTHONPATH=.:kobo

RUN dnf -y --setopt=tsflags=nodocs install \
    koji \
    python3-coverage \
    python3

# store coverage to a separate volume
RUN printf '[run]\ndata_file = /cov/coverage\n' > /coveragerc

### END OF COMMON PART

RUN dnf -y --setopt=tsflags=nodocs install \
    csmock \
    file

RUN adduser osh-worker --uid 1000 --system -G mock

ENV OSH_WORKER_CONFIG_FILE=osh/worker/worker-local.conf

USER osh-worker
CMD coverage-3 run --parallel-mode --omit="*site-packages*,*kobo*," --rcfile=/coveragerc osh/worker/osh-worker -f
