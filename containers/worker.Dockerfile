FROM quay.io/centos/centos:stream8

RUN dnf install -y dnf-plugins-core https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
RUN dnf config-manager --set-enabled powertools

WORKDIR /src

ENV PYTHONPATH=.:kobo
ENV OSH_WORKER_CONFIG_FILE=osh/worker/worker-local.conf

RUN echo -e "max_parallel_downloads=20\nfastestmirror=True" >> /etc/dnf/dnf.conf

RUN dnf -y --setopt=tsflags=nodocs install \
    cppcheck \
    csmock \
    csmock-plugin-unicontrol \
    file \
    gzip \
    koji \
    python3-coverage \
    python3-gssapi \
    python36 \
    xz

RUN adduser csmock -G mock

# override config_opts['use_bootstrap'] from mock config to make it work in a container
RUN sed -e 's|print_main_output=True"|&, "--no-bootstrap-chroot"|' -i /usr/bin/csmock

RUN touch /WORKER_IS_READY

CMD coverage-3 run --parallel-mode --omit="*site-packages*,*kobo*," osh/worker/osh-worker -f
