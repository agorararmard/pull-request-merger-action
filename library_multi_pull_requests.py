#!/usr/bin/env python3
# Copyright 2020 SkyWater PDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

# Originally written by Ahmed Ghazy (ax3ghazy) & Amr Gouhar (agorararmard)

import datetime
import os
import pprint
import shutil
import subprocess
import sys
import tempfile
import time
import requests
import json

from library_submodules import *
from library_patch_submodules import *

__dir__ = os.path.dirname(__file__)


def header(l, s, *args, **kw):
    s1 = s.format(*args, **kw)
    s2 = l*len(s1)
    return '{}\n{}\n'.format(s1, s2)



def handle_pull_requests(args):
    print(args)
    assert len(args) == 6
    dmp = args.pop(0)
    repo_name = args.pop(0)
    dmp = args.pop(0)
    access_token = args.pop(0)
    dmp = args.pop(0)
    external_path = args.pop(0)

    print()
    print()

    git_root = get_git_root()

    git_fetch(git_root)

    all_open_pull_requests = subprocess.check_output("curl -sS 'https://api.github.com/repos/{0}/pulls?state=open' | grep -o -E 'pull/[[:digit:]]+' | sed 's/pull\///g'| sort | uniq".format(repo_name) , shell=True).decode('utf-8').split()
    print ("All Open Pull Requests: ", all_open_pull_requests)
    library_clean_submodules(all_open_pull_requests)
    for pull_request_id in all_open_pull_requests:
        print()
        print("Processing:", str(pull_request_id))
        print('-'*20, flush=True)
        commit_hash = subprocess.check_output("git ls-remote origin 'pull/*/head' | grep 'pull/{0}/head'".format(pull_request_id) + " | tail -1 | awk '{ print $1F }'" , shell=True).decode('utf-8')
        git_sequence = get_sequence_number(pull_request_id)
        print()
        print("Getting Patch")
        print()
        run('wget https://github.com/{0}/pull/{1}.patch'.format(repo_name,pull_request_id))
        run('mv {0}.patch {1}/'.format(pull_request_id,external_path))
        patchfile='{0}/{1}.patch'.format(external_path,pull_request_id)
        print("Will try to apply: ", patchfile)
        if library_patch_submodules(patchfile, pull_request_id, repo_name,access_token,commit_hash):
            print()
            print("Pull Request Handled: ", str(pull_request_id))
            print('-'*20, flush=True)
            if label_exists(repo_name,pull_request_id,'ready-to-merge'):
                print("PR {0} is now ready to be merged..".format(pull_request_id))
                library_merge_submodules(pull_request_id,repo_name,access_token)
        print("Resetting Branches")
        reset_branches(git_root)
        print("Reset Branches Done!")

    print('-'*20, flush=True)
    print("Done Creating PR branches!")
    print('-'*20, flush=True)

if __name__ == "__main__":
    sys.exit(handle_pull_requests(sys.argv[1:]))
