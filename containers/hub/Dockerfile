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

# enable installation of gettext message objects
RUN rm /etc/rpm/macros.image-language-conf

RUN dnf -y --setopt=tsflags=nodocs install \
    /usr/bin/pg_isready \
    csdiff \
    gzip \
    python3-bugzilla \
    python3-csdiff \
    python3-django3 \
    python3-gssapi \
    python3-jira \
    python3-psycopg2 \
    python3-qpid-proton \
    xz

EXPOSE 8000

RUN adduser --system --no-create-home osh

COPY containers/hub/run.sh /run.sh
RUN chmod +x /run.sh

USER osh
CMD /run.sh
