# Dockerfile that can convert an MPR project into an MDA file.
FROM --platform=linux/amd64 registry.access.redhat.com/ubi8/ubi-minimal:latest

# Set the locale
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Set the user ID
ARG USER_UID=1001
ENV USER_UID=${USER_UID}

# Add mono repo
COPY --chown=0:0 scripts/mono/xamarin.gpg /etc/pki/rpm-gpg/RPM-GPG-KEY-mono-centos8-stable
COPY --chown=0:0 scripts/mono/mono-centos8-stable.repo /etc/yum.repos.d/mono-centos8-stable.repo

# Install mono and common prerequisites
RUN rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm &&\
    microdnf update -y && \
    microdnf install -y glibc-langpack-en openssl fontconfig tzdata-java mono-core-5.20.1.34 libgdiplus0 libicu && \
    microdnf clean all && rm -rf /var/cache/yum

# Install Java if specified
ARG JAVA_VERSION
RUN if [ ! -z "$JAVA_VERSION" ]; then \
    microdnf update -y && \
    microdnf install -y java-${JAVA_VERSION}-openjdk-headless java-${JAVA_VERSION}-openjdk-devel && \
    microdnf clean all && rm -rf /var/cache/yum \
    ; fi

# Download or copy MxBuild
ARG MXBUILD_ARCHIVE
ADD $MXBUILD_ARCHIVE /opt/mendix/mxbuild/

