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

# Originally written by Tim 'mithro' Ansell
# Slightly modified for Github Actions use by Ahmed Ghazy (ax3ghazy) & Amr Gouhar (agorararmard)

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


__dir__ = os.path.dirname(__file__)


def header(l, s, *args, **kw):
    s1 = s.format(*args, **kw)
    s2 = l*len(s1)
    return '{}\n{}\n'.format(s1, s2)

def library_patch_submodules(patchfile, pull_request_id,repo_name,access_token,commit_hash,sequence_increment):
    assert os.path.exists(patchfile), patchfile
    assert os.path.isfile(patchfile), patchfile
    assert pull_request_id.isdigit(), pull_request_id

    print()
    print()
    git_root = get_git_root()

    git_fetch(git_root)

    versions = get_lib_versions(git_root)

    apply_idx=0
    for i, v in enumerate(versions):
        pv = previous_v(v, versions)
        ov = out_v(v, versions)

        v_branch = "branch-{}.{}.{}".format(*ov)
        v_tag = "v{}.{}.{}".format(*ov)

        print()
        print("Was:", pv, "Now patching", (v_branch, v_tag), "with", patchfile)
        print('-'*20, flush=True)

        # Get us back to a very clean tree.
        # git('reset --hard HEAD', git_root)
        git_clean(git_root)

        # Checkout the right branch
        git('checkout {0}'.format(v_branch), git_root)
        if v in [(0,0,9)]:
            continue
        elif v in [(0, 10, 0), (0, 10, 1), (0, 11, 0), (0, 12, 0), (0, 12, 1), (0, 13, 0)]:
            npatchfile = patchfile.replace('-2', '-1')
        else:
            npatchfile = patchfile

        diff_pos = 'branch-{}.{}.{}'.format(*pv)

        # Update the contents
        if v == versions[apply_idx]:
            if git('am {}'.format(patchfile), git_root, can_fail=True) == False:
                apply_idx+=1
                git('am --abort', git_root)
            continue

        # Create the merge commit
        git('merge {} --no-ff --no-commit --strategy=recursive'.format(diff_pos), git_root)
        git('commit -C HEAD@{1}', git_root)

    git('branch -D master', git_root, can_fail=True)
    git('branch master', git_root)

    print('='*75, flush=True)

    git_sequence = int(get_sequence_number(pull_request_id)) + sequence_increment
    n_branch_links = ""
    for i, v in enumerate(versions):
        ov = out_v(v, versions)
        v_branch = "branch-{}.{}.{}".format(*ov)
        v_tag = "v{}.{}.{}".format(*ov)
        print()
        print("Now Pushing", (v_branch, v_tag))
        print('-'*20, flush=True)

        n_branch = 'pullrequest/temp/{0}/{1}/{2}'.format(pull_request_id,str(git_sequence),v_branch)
        branch_link = "https://github.com/{0}/tree/{1}".format(repo_name,n_branch)
        n_branch_links += "\n- {0}".format(branch_link)
        print("Now Pushing", n_branch)
        if git('push -f origin {0}:{1}'.format(v_branch,n_branch), git_root, can_fail=True) == False:
            print("Pull Request {0} is coming from a fork and trying to update the workflow. We will skip it!!!")
            return False

    print()
    n_branch = 'pullrequest/temp/{0}/{1}/master'.format(pull_request_id,str(git_sequence))
    branch_link = "https://github.com/{0}/tree/{1}".format(repo_name,n_branch)
    n_branch_links += "\n- {0}".format(branch_link)
    print("Now Pushing", n_branch)
    print('-'*20, flush=True)
    if git('push -f origin master:{0}'.format(n_branch), git_root, can_fail=True) == False:
        print("Pull Request {0} is coming from a fork and trying to update the workflow. We will skip it!!!")
        return False
    if sequence_increment:
        comment_body = 'The latest commit of this PR, commit {0} has been applied to the branches, please check the links here:\n {1}'.format( commit_hash, n_branch_links)
        git_issue_comment(repo_name,pull_request_id,comment_body,access_token)
    return True


def library_merge_submodules(pull_request_id,repo_name,access_token):
    print()
    print()
    git_root = get_git_root()

    git_fetch(git_root)

    versions = get_lib_versions(git_root)
    for i, v in enumerate(versions):
        pv = previous_v(v, versions)
        ov = out_v(v, versions)

        v_branch = "branch-{}.{}.{}".format(*ov)
        v_tag = "v{}.{}.{}".format(*ov)
        git_sequence = int(get_sequence_number(pull_request_id))
        n_branch = 'pullrequest/temp/{0}/{1}/{2}'.format(pull_request_id,str(git_sequence),v_branch)
        print()
        print("Was:", pv, "Now updating", (v_branch, v_tag), "with", n_branch)
        print('-'*20, flush=True)

        # Get us back to a very clean tree.
        # git('reset --hard HEAD', git_root)
        git_clean(git_root)

        # Checkout the right branch
        git('checkout {0}'.format(v_branch), git_root)
        print("Now reseting ", v_branch, " to ", n_branch)
        git('reset --hard origin/{0}'.format(n_branch),git_root)
        print("Now Pushing", v_branch)
        git('push -f origin {0}:{0}'.format(v_branch,v_branch), git_root)
        for i in range(git_sequence + 1):
            git('push origin --delete pullrequest/temp/{0}/{1}/{2}'.format(pull_request_id,str(i),v_branch), git_root)

    git_clean(git_root)
    n_branch = 'pullrequest/temp/{0}/{1}/master'.format(pull_request_id,str(git_sequence))
    git('checkout master', git_root)
    print("Now reseting master to ", n_branch)
    git('reset --hard origin/{0}'.format(n_branch),git_root)
    print("Now Pushing", v_branch)
    git('push -f origin master:master', git_root)
    for i in range(git_sequence + 1):
            git('push origin --delete pullrequest/temp/{0}/{1}/master'.format(pull_request_id,str(i)), git_root)
    git_issue_close(repo_name,pull_request_id, access_token)
    comment_body = 'Thank you for your pull request. This pull request will be closed, because the Pull-Request Merger has successfully applied it internally to all branches.'
    git_issue_comment(repo_name,pull_request_id,comment_body,access_token)

def library_rebase_submodules(pull_request_id):
    print()
    print()
    git_root = get_git_root()

    git_fetch(git_root)

    versions = get_lib_versions(git_root)
    for i, v in enumerate(versions):
        pv = previous_v(v, versions)
        ov = out_v(v, versions)

        v_branch = "branch-{}.{}.{}".format(*ov)
        v_tag = "v{}.{}.{}".format(*ov)
        git_sequence = int(get_sequence_number(pull_request_id))
        n_branch = 'pullrequest/temp/{0}/{1}/{2}'.format(pull_request_id,str(git_sequence),v_branch)
        print()
        print("Was:", pv, "Now rebasing ", n_branch , " with ", (v_branch, v_tag))
        print('-'*20, flush=True)

        # Get us back to a very clean tree.
        # git('reset --hard HEAD', git_root)
        git_clean(git_root)

        # Checkout the right branch
        git('checkout {0}'.format(n_branch), git_root)
        git('rebase origin/{0}'.format(v_branch), git_root)
        print("Now Pushing", n_branch)
        git('push -f origin {0}:{0}'.format(n_branch,n_branch), git_root)

    git_clean(git_root)
    n_branch = 'pullrequest/temp/{0}/{1}/master'.format(pull_request_id,str(git_sequence))
    git('checkout {0}'.format(n_branch), git_root)
    git('rebase origin/master', git_root)
    print("Now Pushing", n_branch)
    git('push -f origin {0}:{0}'.format(n_branch,n_branch), git_root)

def library_clean_submodules(all_open_pull_requests):
    print()
    print()
    print("Cleaning up pull request branches for closed pull requests.")
    git_root = get_git_root()

    git_fetch(git_root)

    all_branches = subprocess.check_output('git branch -r' , shell=True).decode('utf-8').split()
    print("All branchs:", all_branches)
    for br in all_branches:
         if "origin/pullrequest/temp/" in br and br.split('/')[3] not in all_open_pull_requests:
            print('Deleting ', br)
            git('push origin --delete {0}'.format(br), git_root)

def main(args):
    assert len(args) == 5
    patchfile = os.path.abspath(args.pop(0))
    pull_request_id = args.pop(0)
    repo_name = args.pop(0)
    access_token = args.pop(0)
    commit_hash = args.pop(0)
    library_patch_submodules(patchfile, pull_request_id,repo_name,access_token,commit_hash,1)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
