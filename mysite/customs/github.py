# This file is part of OpenHatch.
# Copyright (C) 2010 OpenHatch, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

### This file is a collection of wrappers around
### the github2.client API.

### If you are writing new code that communicates
### with the github API, you should write a new function
### in here.

### The repos_by_username() function is a good example of
### one to clone.

### By writing a function here, you can easily write a test
### in mysite/customs/tests.py and mock out Github as necessary.

import github2.client
from django.conf import settings
import mysite.customs.mechanize_helpers
import simplejson
import mysite.base.helpers
import urllib
import urllib2

_github = None

# When this file gets imported, we create a Github object
# called _github and connect it to our API key.
# That does make importing a little slow, but that's okay.
_github = github2.client.Github(username=settings.GITHUB_USERNAME,
                               api_token=settings.GITHUB_API_TOKEN)

def _github_repos_list(username):
    return _github.repos.list(mysite.base.unicode_sanity.quote(username))

def repos_by_username(username):
    try:
        if '@' in username:
            # it's doomed. set repos to the empty list
            repos = []
        else:
            repos = _github_repos_list(username)
    except urllib2.HTTPError, e:
        if e.code == 403:
            # Well, Github said 403
            # That seems to mean that there is no such Github user. So,
            # return the empty list.
            return
        else:
            raise # otherwise, wtf
    except RuntimeError, r_e:
        if r_e.message.startswith('unexpected response from github.com 404'):
            return # 404 is, like, whatever
        if r_e.message.startswith('unexpected response from github.com 403'):
            return # 403 is also no big deal
        raise
    for repo in repos:
        yield repo

def find_primary_language_of_repo(github_username, github_reponame):
    # FIXME: Make this handle a few situations
    # * Repo does not exist (or rather, raise ValueError then)
    # * We have hit the Github API limit, in which case, let the caller
    #   know it's safe to retry this later (it'd be nice to know when)
    assert '/' not in github_reponame
    assert '/' not in github_username

    json_url = 'http://github.com/api/v2/json/repos/show/%s/%s/languages' % (
        github_username, github_reponame)
    response = mysite.customs.mechanize_helpers.mechanize_get(json_url).response()
    data = simplejson.load(response)
    if 'languages' in data:
        language_name_count_tuples = data['languages'].items()
        sorted_by_count = sorted(language_name_count_tuples,
                                   lambda x: x[1])
        winning_lang_name, winning_lang_count = sorted_by_count[0]
        return winning_lang_name
    else:
        return '' # No best guess for primary language.

def _pull_data_from_user_activity_feed(github_username):
    json_url = 'http://github.com/%s.json' % mysite.base.unicode_sanity.quote(github_username)
    response = mysite.customs.mechanize_helpers.mechanize_get(json_url).response()
    data = simplejson.load(response)
    return data

def _get_repositories_user_watches(github_username):
    '''Returns a list of repo objects.'''
    json_url = 'http://github.com/api/v2/json/repos/watched/%s' % (
        mysite.base.unicode_sanity.quote(github_username))
    try:
        response = mysite.customs.mechanize_helpers.mechanize_get(json_url).response()
    except urllib2.HTTPError, e:
        if (e.code == 403) or (e.code == 404):
            # Well, Github said 403
            # That seems to mean that there is no such Github user. So,
            # return the empty list.
            return []
        else:
            raise # otherwise, wtf
    data = simplejson.load(response)
    return data['repositories']

def repos_user_collaborates_on(github_username):
    if '@' in github_username:
        watched = []
        not_owned = []
    else:
        # First, make a big set of candidates: all the repos the user watches
        watched = _get_repositories_user_watches(github_username)
        # Now filter that down to just the ones not owned by the user
        not_owned = [r for r in watched if r['owner'] != github_username]
    # Now ask github.com if, for each repo, github_username is a collaborator
    for repo in not_owned:
        collaborators = _github.repos.list_collaborators('%s/%s' % (
                repo['owner'], repo['name']))
        if github_username in collaborators:
            yield mysite.base.helpers.ObjectFromDict(repo)

def repos_by_username_from_activity_feed(github_username):
    repo_urls_emitted = set()
    for event in _pull_data_from_user_activity_feed(github_username):
        if event['type'] == 'PushEvent':
            repo = event['repository']
            if repo['url'] not in repo_urls_emitted:
                if repo['owner'] == github_username:
                    continue # skip the ones owned by this user
                repo_urls_emitted.add(repo['url']) # avoid sending out duplicates
                yield mysite.base.helpers.ObjectFromDict(repo)
    
        
