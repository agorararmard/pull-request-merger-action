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
    assert len(args) == 3
    repo_name = args.pop(0)
    access_token = args.pop(0)
    external_path = args.pop(0)

    print()
    print()

    git_root = subprocess.check_output('git rev-parse --show-toplevel', shell=True)
    git_root = git_root.decode('utf-8').strip()

    print()

    print()

    git('fetch origin', git_root)

    git('fetch origin --tags', git_root)

    git('status', git_root)

    print('-'*20, flush=True)
    all_open_pull_requests = subprocess.check_output("curl -sS 'https://api.github.com/repos/{0}/pulls?state=open' | grep -o -E 'pull/[[:digit:]]+' | sed 's/pull\///g'| sort | uniq".format(repo_name) , shell=True).decode('utf-8').split()
    print ("All Open Pull Requests: ", all_open_pull_requests)
    for pull_request_id in all_open_pull_requests:
        
        print()
        print("Processing:", str(pull_request_id))
        print('-'*20, flush=True)
        commit_hash = subprocess.check_output("git ls-remote origin 'pull/*/head' | grep 'pull/{0}/head'".format(pull_request_id) + " | tail -1 | awk '{ print $1F }'" , shell=True).decode('utf-8')
        git_sequence = get_sequence_number(pull_request_id)
        if git_sequence != -1:
            if hash_exists(commit_hash,'pullrequest/temp/{0}/{1}/master'.format(pull_request_id,git_sequence),git_root):
                print("hash", commit_hash, "already exists in",'pullrequest/temp/{0}/{1}/master'.format(pull_request_id,git_sequence) )
                continue
        print()
        print("Getting Patch")
        print()
        run('wget https://github.com/{0}/pull/{1}.patch'.format(repo_name,pull_request_id))
        run('mv {0}.patch {1}/'.format(pull_request_id,external_path))
        patchfile='{0}/{1}.patch'.format(external_path,pull_request_id)
        print("Will try to apply: ", patchfile)
        library_patch_submodules(patchfile, pull_request_id, repo_name,access_token,commit_hash)
        print()
        print("Pull Request Handled: ", str(pull_request_id))
        print('-'*20, flush=True)
        print("Resetting Branches")
        reset_branches(git_root)
        print("Reset Branches Done!")

    
if __name__ == "__main__":
    sys.exit(handle_pull_requests(sys.argv[1:]))
