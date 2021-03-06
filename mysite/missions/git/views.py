# This file is part of OpenHatch.
# Copyright (C) 2010, 2011 OpenHatch, Inc.
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

from mysite.missions.base.views import *
from mysite.missions.git import controllers, forms


### POST handlers
###
### Forms submit to this, and we use these to validate input and/or
### modify the information stored about the user, such as recording
### that a mission was successfully completed.

@login_required
def resetrepo(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    controllers.GitRepository(request.user.username).reset()
    controllers.unset_mission_completed(request.user.get_profile(), 'git_checkout')
    controllers.unset_mission_completed(request.user.get_profile(), 'git_diff')
    controllers.unset_mission_completed(request.user.get_profile(), 'git_rebase')
    if 'stay_on_this_page' in request.GET:
        return HttpResponseRedirect(reverse(main_page))
    else:
        return HttpResponseRedirect(reverse(checkout))

@login_required
def checkout_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['git_checkout_form'] = forms.CheckoutForm()
    data['git_checkout_error_message'] = ''
    if request.method == 'POST':
        form = forms.CheckoutForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['secret_word'].lower() == 'the brain':
                controllers.set_mission_completed(request.user.get_profile(), 'git_checkout')
                return HttpResponseRedirect(reverse(checkout))
            else:
                data['git_checkout_error_message'] = "The author's name is incorrect."
        data['git_checkout_form'] = form
    return checkout(request, data)

@login_required
def diff_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['git_diff_form'] = forms.DiffForm()
    data['git_diff_error_message'] = ''
    if request.method == 'POST':
        form = forms.DiffForm(request.POST)
        if form.is_valid():
                if controllers.GitDiffMission.validate_diff_and_commit_if_ok(request.user.username, form.cleaned_data['diff']):
                    controllers.set_mission_completed(request.user.get_profile(), 'git_diff')
                    return HttpResponseRedirect(reverse(diff))
                else:
                    data['git_diff_error_message'] = "The patch file is incorrect.  Give it another try!"
        data['git_diff_form'] = form
    return diff(request, data)

@login_required
def rebase_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['git_rebase_form'] = forms.RebaseForm()
    data['git_rebase_error_message'] = ''
    if request.method == 'POST':
        form = forms.RebaseForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['secret_word'].lower() == 'pinky':
                controllers.set_mission_completed(request.user.get_profile(), 'git_rebase')
                return HttpResponseRedirect(reverse(rebase))
            else:
                data['git_rebase_error_message'] = "The author's name is incorrect."
        data['git_rebase_form'] = form
    return rebase(request, data)

### State manager
class GitMissionPageState(MissionPageState):
    def __init__(self, request, passed_data):
        super(GitMissionPageState, self).__init__(request, passed_data, 'Using Git')

    def as_dict_for_template_context(self):
        (data, person) = self.get_base_data_dict_and_person()
        if person:
            repo = controllers.GitRepository(self.request.user.username)
            data.update({
                'repository_exists': repo.exists(),
                'git_checkout_done': controllers.mission_completed(person, 'git_checkout'),
                'git_diff_done': controllers.mission_completed(person, 'git_diff'),
                'git_rebase_done': controllers.mission_completed(person, 'git_rebase'),
            })
            if data['repository_exists']:
              data.update({
                'checkout_url': repo.public_url,
              })
        return data



### Normal GET handlers. These are usually pretty short.

@view
def main_page(request, passed_data = None):
    state = GitMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Start page'
    return (request, 'missions/git/main_page.html',
            state.as_dict_for_template_context())

@view
def long_description(request, passed_data = None):
    state = GitMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'About Git'
    return (request, 'missions/git/about_git.html',
            state.as_dict_for_template_context())

@login_required
@view
def checkout(request, passed_data = None):
    state = GitMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Cloning'
    data = state.as_dict_for_template_context()
    data['git_checkout_form'] = forms.CheckoutForm()
    return (request, 'missions/git/checkout.html', data)

@login_required
@view
def diff(request, passed_data = None):
    state = GitMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Diffing your changes'
    state.mission_step_prerequisite = 'git_checkout'
    data = state.as_dict_for_template_context()
    data['git_diff_form'] = forms.DiffForm()
    return (request, 'missions/git/diff.html', data)

@login_required
@view
def rebase(request, passed_data = None):
    state = GitMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Rebase'
    state.mission_step_prerequisite = 'git_diff'
    data = state.as_dict_for_template_context()
    data['git_rebase_form'] = forms.RebaseForm()
    return (request, 'missions/git/rebase.html', data)
