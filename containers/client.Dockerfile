ARG CENTOS_RELEASE=9

FROM quay.io/centos/centos:stream${CENTOS_RELEASE}

# See https://docs.docker.com/engine/reference/builder/#understand-how-arg-and-from-interact
ARG CENTOS_RELEASE

# See https://techglimpse.com/failed-metadata-repo-appstream-centos-8/ for the sed hack
RUN if [ "$CENTOS_RELEASE" == "8" ]; then \
    sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-* && \
    sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*; \
    fi && \
    dnf install -y dnf-plugins-core epel-release

RUN if [ $CENTOS_RELEASE == 8 ]; then dnf config-manager --set-enabled powertools; else dnf config-manager --set-enabled crb; fi

WORKDIR /src

ENV PYTHONPATH=.:kobo

RUN dnf -y --setopt=tsflags=nodocs install \
    centpkg \
    koji \
    python3-coverage \
    python3

# store coverage to a separate volume
RUN printf '[run]\ndata_file = /cov/coverage\n' > /coveragerc

### END OF COMMON PART

RUN adduser --uid 1000 osh

ENV OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf

USER osh
CMD sleep inf
