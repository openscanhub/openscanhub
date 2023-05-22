FROM quay.io/centos/centos:stream8

EXPOSE 8000

RUN dnf install -y dnf-plugins-core https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
RUN dnf config-manager --set-enabled powertools

WORKDIR /src

ENV PYTHONPATH=.:kobo

RUN echo -e "max_parallel_downloads=20\nfastestmirror=True" >> /etc/dnf/dnf.conf

# enable installation of gettext message objects
RUN rm /etc/rpm/macros.image-language-conf

RUN dnf -y --setopt=tsflags=nodocs install \
    /usr/bin/krb5-config \
    cpio \
    csdiff \
    csmock \
    gcc \
    glibc-langpack-en \
    gzip \
    koji \
    python3-bugzilla \
    python3-coverage \
    python3-csdiff \
    python3-devel \
    python3-django3 \
    python3-gssapi \
    python3-jira \
    python3-koji \
    python3-psycopg2 \
    python3-qpid-proton \
    python36 \
    postgresql{,-libs} \
    xz

COPY containers/hub/run.sh /run.sh
RUN chmod +x /run.sh

CMD /run.sh
