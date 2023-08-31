FROM quay.io/centos/centos:stream8

RUN dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm

WORKDIR /src

ENV PYTHONPATH=.:kobo
ENV OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf

RUN dnf -y --setopt=tsflags=nodocs install \
    koji \
    python3-coverage \
    python3

# store coverage to a separate volume
RUN printf '[run]\ndata_file = /cov/coverage\n' > /coveragerc

RUN touch /CLIENT_IS_READY

CMD sleep inf
