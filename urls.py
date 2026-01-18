"""URL Configuration"""
from django.urls import path
from league import league_home, add_team, delete_team, clear_teams, start_league_tournament, league_match
from knockout import start_knockout_tournament, knockout_match
from multistage import start_multistage_tournament, multistage_match, multistage_groups

urlpatterns = [
    path('', league_home, name='home'),
    path('add-team/', add_team, name='add_team'),
    path('delete-team/<int:team_id>/', delete_team, name='delete_team'),
    path('clear-teams/', clear_teams, name='clear_teams'),
    path('start-league/', start_league_tournament, name='start_league'),
    path('league/', league_match, name='league_match'),
    path('start-knockout/', start_knockout_tournament, name='start_knockout'),
    path('knockout/', knockout_match, name='knockout_match'),
    path('start-multistage/', start_multistage_tournament, name='start_multistage'),
    path('multistage/', multistage_match, name='multistage_match'),
    path('multistage/groups/', multistage_groups, name='multistage_groups'),
]