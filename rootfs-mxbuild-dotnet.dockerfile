# Dockerfile that can convert an MPR project into an MDA file.
FROM registry.access.redhat.com/ubi9/ubi-minimal:latest

# Set the locale
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Set the user ID
ARG USER_UID=1001
ENV USER_UID=${USER_UID}

# Install common prerequisites
RUN rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm &&\
    microdnf update -y && \
    microdnf install -y glibc-langpack-en openssl fontconfig tzdata-java libgdiplus libicu && \
    microdnf clean all && rm -rf /var/cache/yum

# Install Java if specified
ARG JAVA_VERSION
RUN if [ ! -z "$JAVA_VERSION" ]; then \
    microdnf update -y && \
    microdnf install -y java-${JAVA_VERSION}-openjdk-devel && \
    microdnf clean all && rm -rf /var/cache/yum \
    ; fi

# Download or copy MxBuild
ARG MXBUILD_ARCHIVE
ADD $MXBUILD_ARCHIVE /opt/mendix/

COPY --chmod=0755 mxbuild /opt/mendix/

# Create user (for non-OpenShift clusters)
RUN echo "mendix:x:${USER_UID}:${USER_UID}:mendix user:/workdir:/sbin/nologin" >> /etc/passwd

# Prepare build context
ENV HOME /workdir
RUN mkdir -p /workdir/project &&\
    mkdir -p /workdir/.local/share/Mendix &&\
    chown -R ${USER_UID}:${USER_UID} /workdir &&\
    chmod -R 755 /workdir

USER $USER_UID

ENTRYPOINT ["/opt/mendix/mxbuild"]
