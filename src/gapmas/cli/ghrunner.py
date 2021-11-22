# Copyright 2021 Frode Nordahl
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import typing


# GitHub
import json
import requests


GH_BASE_URL = 'https://api.github.com'
GH_ORG = os.environ['GH_ORG']
GH_REPO = os.environ['GH_REPO']
GH_AUTH = requests.auth.HTTPBasicAuth(
    os.environ['GH_USER'],
    os.environ['GH_TOKEN'])


def get_download_urls(
        owner: str,
        repo: str,
        auth: requests.auth.HTTPBasicAuth,
        ) -> typing.List[typing.Dict[str, str]]:
    """Get download urls for GitHub Actions runner binaries."""
    url = GH_BASE_URL + f'/repos/{owner}/{repo}/actions/runners/downloads'
    r = requests.get(url, auth=auth)
    return json.loads(r.text)


def get_download_url(
        owner: str,
        repo: str,
        auth: requests.auth.HTTPBasicAuth,
        os: str,
        arch: str,
        ) -> typing.Optional[str]:
    """Get download URL for specific OS and architecture combination."""
    for runner_url_data in get_download_urls(
            GH_ORG, GH_REPO, GH_AUTH):
        if (runner_url_data['architecture'] == arch
                and runner_url_data['os'] == os):
            return runner_url_data['download_url']


def list_runners(
        owner: str,
        repo: str,
        auth: requests.auth.HTTPBasicAuth,
        ) -> typing.List[typing.Optional[typing.Dict[str, any]]]:
    """List self-hosted runners for a repository."""
    url = GH_BASE_URL + f'/repos/{owner}/{repo}/actions/runners'
    r = requests.get(url, auth=auth)
    data = json.loads(r.text)
    return data.get('runners', [])


def create_token(
        owner: str,
        repo: str,
        auth: requests.auth.HTTPBasicAuth,
        ) -> typing.Dict[str, str]:
    """Create registration token."""
    url = GH_BASE_URL
    url += f'/repos/{owner}/{repo}/actions/runners/registration-token'
    r = requests.post(url, auth=auth)
    return json.loads(r.text)


def list_runs(
        owner: str,
        repo: str,
        auth: requests.auth.HTTPBasicAuth,
        status: typing.Optional[str] = None,
        ) -> typing.List[typing.Dict[str, any]]:
    """List workflow runs."""
    url = GH_BASE_URL
    url += f'/repos/{owner}/{repo}/actions/runs'
    if status:
        url += f'?status={status}'
    r = requests.get(url, auth=auth)
    data = json.loads(r.text)
    return data.get('workflow_runs', [])


def list_run_jobs(
        owner: str,
        repo: str,
        auth: requests.auth.HTTPBasicAuth,
        run_id: int,
        ) -> typing.List[typing.Dict[str, any]]:
    """List jobs for a workflow run."""
    url = GH_BASE_URL
    url += f'/repos/{owner}/{repo}/actions/runs/{run_id}/jobs'
    r = requests.get(url, auth=auth)
    data = json.loads(r.text)
    return data.get('jobs', [])


class JobLabels(typing.NamedTuple):
    id: int
    labels: typing.List[str]


def get_queued_self_hosted_jobs(
        owner: str,
        repo: str,
        auth: requests.auth.HTTPBasicAuth,
        run_id: int,
        ) -> typing.Generator[JobLabels, None, None]:
    """Get queued jobs destined for self-hosted runners.

    Provides tuple with job_id and a list of labels.
    """
    for job in list_run_jobs(owner, repo, auth, run_id):
        if 'self-hosted' in job['labels']:
            yield JobLabels(
                    job['id'],
                    [label
                     for label in job['labels']
                     if label != 'self-hosted'])  # filter 'self-hosted' label.


# OpenStack
import base64     # noqa - pending split into separate module.
import openstack  # noqa - pending split into separate module.
import textwrap   # noqa - pending split into separate module.


OS_KEY_NAME = os.environ['OS_KEY_NAME']
OS_NETWORK_NAME = os.environ['OS_NETWORK_NAME']
OS_TAG = os.environ.get('OS_TAG', 'gapmas')


def find_image(
        conn: openstack.connection.Connection,
        os_version: str,
        architecture: str = 'x86_64',
        os_distro: str = 'ubuntu'
        ) -> openstack.image.v2.image.Image:
    candidates = {image.properties['version_name']: image
                  for image in conn.image.images()
                  if (image.architecture == architecture
                      and image.os_distro == os_distro
                      and image.os_version == os_version
                      and 'version_name' in image.properties)}
    return candidates[max(sorted(candidates))]


def find_flavor(
        conn: openstack.connection.Connection,
        minRam: int = 7168,
        minCores: int = 2
        ) -> openstack.compute.v2.flavor.FlavorDetail:
    candidates = {flavor.ram: flavor
                  for flavor in conn.compute.flavors(minRam=minRam)
                  if flavor.vcpus >= minCores}
    return candidates[min(sorted(candidates))]


def create_runner(
        conn: openstack.connection.Connection,
        key_name: str,
        owner: str,
        repo: str,
        run_id: str,
        token: str,
        download_url: str,
        tag: str = OS_TAG,
        name: typing.Optional[str] = '',
        ) -> openstack.compute.v2.server.Server:
    script = bytes(textwrap.dedent(f"""#!/bin/bash
        echo 'https_proxy=http://squid.internal:3128' >> /etc/environment
        echo 'http_proxy=http://squid.internal:3128' >> /etc/environment

        DIR=$(sudo -u ubuntu mktemp -d)
        cd $DIR
        sudo -u ubuntu wget -O runner.tar.gz {download_url}
        sudo -u ubuntu tar -xvzf runner.tar.gz
        sudo -u ubuntu ./config.sh \
                --url https://github.com/{GH_ORG}/{GH_REPO} \
                --token {token} \
                --ephemeral
        sudo -u ubuntu ./run.sh
        poweroff
        """), encoding='utf-8')
    image = find_image(conn, '21.10')
    flavor = find_flavor(conn)
    network = conn.network.find_network(OS_NETWORK_NAME)
    return conn.compute.create_server(
        name=name or f'{tag}-{owner}-{repo}-{run_id}',
        image_id=image.id,
        flavor_id=flavor.id,
        networks=[{'uuid': network.id}],
        key_name=key_name,
        user_data=base64.b64encode(script).decode('utf-8'),
        tags=[tag])


def main():
    conn = openstack.connect()
    running_servers = {}
    for server in conn.compute.servers(tags=[OS_TAG]):
        if server.status == 'SHUTOFF':
            # Servers tagged by us that are shut off have completed their run,
            # remove them.
            print(f"Removing instance {server.name} in SHUTOFF state.")
            conn.compute.delete_server(server)
            continue
        # Store references to running servers to ensure we do not attempt to
        # re-create them.
        running_servers[server.name] = server
    for run in list_runs(GH_ORG, GH_REPO, GH_AUTH, status='queued'):
        for job in get_queued_self_hosted_jobs(
                GH_ORG, GH_REPO, GH_AUTH, run['id']):
            instance_name = f'{OS_TAG}-{GH_ORG}-{GH_REPO}-{run["id"]}-{job.id}'
            if instance_name in running_servers:
                print(f"Runner {instance_name} already exists, skip.")
                continue
            token = create_token(GH_ORG, GH_REPO, GH_AUTH)['token']
            runner_url = get_download_url(GH_ORG, GH_REPO, GH_AUTH, 'linux',
                                          'x64')
            server = create_runner(conn, OS_KEY_NAME, GH_ORG, GH_REPO,
                                   run['id'], token, runner_url,
                                   name=instance_name, labels=job.labels)
            print(server)
