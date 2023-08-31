FROM quay.io/centos/centos:stream8

RUN dnf install -y dnf-plugins-core https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
RUN dnf config-manager --set-enabled powertools

WORKDIR /src

ENV PYTHONPATH=.:kobo
ENV OSH_WORKER_CONFIG_FILE=osh/worker/worker-local.conf

RUN dnf -y --setopt=tsflags=nodocs install \
    csmock \
    file \
    koji \
    python3-coverage \
    python3

RUN adduser csmock -G mock

# store coverage to a separate volume
RUN printf '[run]\ndata_file = /cov/coverage\n' > /coveragerc

RUN touch /WORKER_IS_READY

CMD coverage-3 run --parallel-mode --omit="*site-packages*,*kobo*," --rcfile=/coveragerc osh/worker/osh-worker -f
