# Copyright 2021 Canonical
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
import unittest

with unittest.mock.patch.dict(
        os.environ,
        {
            'GH_ORG': 'gh_org',
            'GH_REPO': 'gh_repp',
            'GH_USER': 'gh_user',
            'GH_TOKEN': 'gh_token',
            'OS_KEY_NAME': 'os_key_name',
            'OS_NETWORK_NAME': 'os_network_name',
        },
        clear=True):
    import gapmas.cli.ghrunner as ghrunner


class GitHubTests(unittest.TestCase):

    @unittest.mock.patch.object(ghrunner, 'list_run_jobs')
    def test_get_queued_self_hosted_jobs(self, _list_run_jobs):
        _list_run_jobs.return_value = [
            {'id': 1, 'labels': ['self-hosted', 'other-label']}
        ]
        for job in ghrunner.get_queued_self_hosted_jobs(
                'some_owner', 'some_repo', 'auth', 1):
            self.assertEquals(
                job,
                ghrunner.JobLabels(1, ['other-label']))
        _list_run_jobs.assert_called_once_with(
            'some_owner', 'some_repo', 'auth', 1)
