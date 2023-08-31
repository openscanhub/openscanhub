FROM quay.io/centos/centos:stream8

RUN dnf install -y dnf-plugins-core https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
RUN dnf config-manager --set-enabled powertools

WORKDIR /src

ENV PYTHONPATH=.:kobo

RUN dnf -y --setopt=tsflags=nodocs install \
    koji \
    python3-coverage \
    python3

# store coverage to a separate volume
RUN printf '[run]\ndata_file = /cov/coverage\n' > /coveragerc

### END OF COMMON PART

ENV OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf
RUN touch /CLIENT_IS_READY

CMD sleep inf
