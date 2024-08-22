#!/usr/bin/env python3

import argparse
import pathlib
import os
import tempfile
import json
import sqlite3
import zipfile
import atexit
import shutil
import subprocess
import sys
import selectors
import logging
import platform
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout
)

CACHE_DIR = os.path.join(os.path.expanduser('~'), '.cache', 'mendix-docker-buildpack')

def find_default_file(source_dir, ext):
    files = [x for x in os.listdir(source_dir) if x.endswith(ext)]
    if len(files) == 1:
        return os.path.join(source_dir, files[0])
    if len(files) > 1:
        raise Exception(f"More than one {ext} file found, can not continue")
    return None

def get_metadata_value(source_dir):
    file_name = os.path.join(source_dir, 'model', 'metadata.json')
    try:
        with open(file_name) as file_handle:
            return json.loads(file_handle.read())
    except IOError:
        return None

def extract_mda(mda_file):
    temp_dir = tempfile.TemporaryDirectory(prefix='mendix-docker-buildpack')
    with zipfile.ZipFile(mda_file) as zip_file:
        zip_file.extractall(temp_dir.name)
    return temp_dir

def container_call(args):
    build_executables = ['podman', 'docker']
    build_executable = None
    for builder in build_executables:
        builder = shutil.which(builder)
        if builder is not None:
            build_executable = builder
            break
    if build_executable is None:
        raise Exception('Cannot find Podman or Docker executable')
    proc = subprocess.Popen([build_executable] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    sel = selectors.DefaultSelector()
    sel.register(proc.stdout, selectors.EVENT_READ)
    sel.register(proc.stderr, selectors.EVENT_READ)
    logger = logging.getLogger(build_executable)

    last_line = None
    while proc.poll() is None:
        for key, _ in sel.select():
            data = key.fileobj.readline()
            if data == '':
                continue
            data = data.rstrip()
            if key.fileobj is proc.stdout:
                last_line = data
                logger.info(data)
            elif key.fileobj is proc.stderr:
                logger.error(data)

    sel.close()
    if proc.wait() != 0:
        raise Exception('Builder returned with error')
    return last_line

def download_file(url, destination):
    os.makedirs(CACHE_DIR, mode=0o755, exist_ok=True)
    out_file_path = os.path.join(CACHE_DIR, destination)
    if os.path.isfile(out_file_path):
        return out_file_path
    with urllib.request.urlopen(url) as response, open(out_file_path, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    return out_file_path

def build_mpr_builder(mx_version, java_version):
    prefix = ''
    if platform.machine() == 'arm64':
        prefix = 'arm64-'

    mxbuild_filename = f"{prefix}mxbuild-{mx_version}.tar.gz"
    mxbuild_url = f"https://download.mendix.com/runtimes/{mxbuild_filename}"
    mxbuild_file_path = download_file(mxbuild_url, mxbuild_filename)

    # Docker with Buildkit will cache files and download in parallel
    builder_image = None
    with tempfile.TemporaryDirectory(prefix='mendix-docker-buildpack') as context:
        # Prepare Docker build context
        shutil.copyfile(mxbuild_file_path, os.path.join(context, mxbuild_filename))
        shutil.copyfile(os.path.join('scripts', 'mxbuild'), os.path.join(context, 'mxbuild'))
        builder_image = container_call(['build',
                       '--build-arg', f"MXBUILD_ARCHIVE={mxbuild_filename}",
                       '--build-arg', f"JAVA_VERSION={java_version}",
                       '--file', 'rootfs-mxbuild-dotnet.dockerfile',
                       context])
    # TODO: build image only if it doesn't exist yet
    return builder_image

def build_mpr(source_dir, mpr_file):
    cursor = sqlite3.connect(mpr_file).cursor()
    cursor.execute("SELECT _ProductVersion FROM _MetaData LIMIT 1")
    mx_version = cursor.fetchone()[0]
    mx_version_value = parse_version(mx_version)
    if mx_version_value >= (10, 0, 0, 0):
        builder_image = build_mpr_builder(mx_version, '21')
        build_result = container_call(['run', '--volume', os.path.abspath(source_dir)+':/workdir/project:rw', builder_image])
    raise Exception('TODO')

def parse_version(version):
    return tuple([ int(n) for n in version.split('.') ])

def prepare_mda(source_dir):
    mpr_file = find_default_file(source_dir, '.mpr')
    mda_file = find_default_file(source_dir, '.mda')
    extracted_mda_file = get_metadata_value(source_dir)
    # TODO: pre-download MxRuntime & place into CF Buildpack's cache dir
    if mpr_file is not None:
        return build_mpr(source_dir, mpr_file)
    elif mda_file is not None:
        return extract_mda(mda_file)
    elif extracted_mda_file is not None:
        return source_dir
    else:
        raise Exception('No supported files found in source dir')

def build_image(mda_dir):
    # TODO: build the full image, or just copy MDA into destination?
    mda_path = mda_dir.name if isinstance(mda_dir, tempfile.TemporaryDirectory) else mda_dir
    mda_metadata = get_metadata_value(mda_path)
    mx_version = mda_metadata['RuntimeVersion']
    java_version = mda_metadata.get('JavaVersion', 11)
    print(mda_metadata['RuntimeVersion'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build a Docker image of a Mendix app')
    parser.add_argument('source_dir',  metavar='source_dir', type=pathlib.Path, help='Path to source Mendix app (MDA, MPK or MPR)')

    # TODO: allow to specify Podman args and replace URLs

    args = parser.parse_args()

    mda_dir = prepare_mda(args.source_dir)
    build_image(mda_dir)

