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

====
TODO
====

Here is a short list of things that should be done to make the tool more
versatile and useful.  Contributions are welcome!

* Split src/gapmas/cli/ghrunner.py into separate modules.

  * GitHub API functions should go into a src/gapmas/github package.

  * OpenStack API functions should go into a src/gapmas/provider/openstack
    package.

* Create abstractions for use of cloud provider which allow support for
  multiple providers.

* Add support for multiple providers

  * k8s

  * LXD
