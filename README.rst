..
    Copyright 2021 Frode Nordahl <frode.nordahl@gmail.com>
    
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    
        http://www.apache.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

=============================================
GitHub Actions Poll Mode AutoScaler (GAPMAS)
=============================================

What
----

GitHub Actions Poll Mode AutoScaler, or GAPMAS, is a simple tool that helps
you run ephemeral GitHub Actions self-hosted runners on your own
infrastructure.

Why
---

* Simplicity
  
  Minimal infrastructure is required to use the tool, in its simplest form
  this could be managed from a crontab entry on any Linux machine.

* Poll vs. Push
  
  The tool reaches out to the GitHub API to look for any queued jobs.  The
  benefit of this approach is that you don't need any service exposed to the
  internet for this to work.

How
---

#. Set up Environment variables

   .. list-table:: Environment variables

      * - `GH_ORG`
        - The GitHub organization the repository given in `GH_REPO` resides in.
      * - `GH_REPO`
        - Name of the GitHub repository we operate on.
      * - `GH_USER`
        - Username for authentication to the GitHub API.
      * - `GH_TOKEN`
        - GitHub Personal Access Token.
      * - `OS_KEY_NAME`
        - Name of OpenStack key pair to associate with the instances we create.
      * - `OS_NETWORK_NAME`
        - Name of OpenStack network to attach to the instances we create.
      * - `OS_TAG`
        - Tag to apply to instances.  The tool will manage the life cycle of
          instances and uses this tag to know which instances to operate on.

   * OpenStack client environment

     * The OpenStack provider makes use of the standard OpenStack environment
       variables for authentication.

#. Set up a job manager to run the tool periodically

   * When a change is proposed to a repository with workflows destined to
     self-hosted runners, GitHub will queue the job until a runner consumes
     it.

   * The tool makes use of this behavior to create new runners whenever there
     are jobs queued.

   * As such choose a cadence for the run which is in line with how long you
     would expect to wait before your jobs start.

#. Create workflow in repository

   * Workflow jobs with 'self-hosted' as the first label in `runs-on` will be
     scheduled for self hosted runners.
