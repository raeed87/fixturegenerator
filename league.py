"""League Tournament Views"""
from django.shortcuts import render, redirect
from django.http import HttpResponse
import json
import os
import random

TEAMS_FILE = 'teams.json'
LEAGUE_FILE = 'league_data.json'

def load_teams():
    if os.path.exists(TEAMS_FILE):
        with open(TEAMS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_teams(teams):
    with open(TEAMS_FILE, 'w') as f:
        json.dump(teams, f)

def load_league():
    if os.path.exists(LEAGUE_FILE):
        with open(LEAGUE_FILE, 'r') as f:
            return json.load(f)
    return None

def save_league(data):
    with open(LEAGUE_FILE, 'w') as f:
        json.dump(data, f)

def league_home(request):
    teams = load_teams()
    return render(request, 'home.html', {'teams': teams})

def add_team(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip().title()
        if name and len(name) <= 25:
            teams = load_teams()
            if name not in teams:
                teams.append(name)
                save_teams(teams)
    return redirect('home')

def delete_team(request, team_id):
    teams = load_teams()
    if 0 <= team_id < len(teams):
        teams.pop(team_id)
        save_teams(teams)
    return redirect('home')

def clear_teams(request):
    save_teams([])
    return redirect('home')

def start_league_tournament(request):
    if request.method == 'POST':
        teams = load_teams()
        if len(teams) < 2:
            return redirect('home')
        
        num_rounds = int(request.POST.get('num_rounds', 1))
        
        # Initialize stats
        stats = {team: {'P': 0, 'W': 0, 'D': 0, 'L': 0, 'GF': 0, 'GA': 0, 'GD': 0, 'Pts': 0} for team in teams}
        
        # Generate fixtures
        base = [(teams[i], teams[j]) for i in range(len(teams)) for j in range(i+1, len(teams))]
        all_matches = []
        for _ in range(num_rounds):
            r = base.copy()
            random.shuffle(r)
            all_matches.extend(r)
        
        league_data = {
            'stats': stats,
            'matches': all_matches,
            'current_match': 0
        }
        save_league(league_data)
        return redirect('league_match')
    return redirect('home')

def league_match(request):
    league_data = load_league()
    if not league_data:
        return redirect('home')
    
    if request.method == 'POST':
        score1 = int(request.POST.get('score1', 0))
        score2 = int(request.POST.get('score2', 0))
        
        match = league_data['matches'][league_data['current_match']]
        team1, team2 = match
        
        # Update stats
        stats = league_data['stats']
        stats[team1]['P'] += 1
        stats[team2]['P'] += 1
        stats[team1]['GF'] += score1
        stats[team1]['GA'] += score2
        stats[team2]['GF'] += score2
        stats[team2]['GA'] += score1
        
        if score1 > score2:
            stats[team1]['W'] += 1
            stats[team2]['L'] += 1
            stats[team1]['Pts'] += 3
        elif score2 > score1:
            stats[team2]['W'] += 1
            stats[team1]['L'] += 1
            stats[team2]['Pts'] += 3
        else:
            stats[team1]['D'] += 1
            stats[team2]['D'] += 1
            stats[team1]['Pts'] += 1
            stats[team2]['Pts'] += 1
        
        stats[team1]['GD'] = stats[team1]['GF'] - stats[team1]['GA']
        stats[team2]['GD'] = stats[team2]['GF'] - stats[team2]['GA']
        
        league_data['current_match'] += 1
        save_league(league_data)
        return redirect('league_match')
    
    # Sort standings
    sorted_stats = sorted(league_data['stats'].items(), key=lambda x: (x[1]['Pts'], x[1]['GD'], x[1]['GF']), reverse=True)
    
    current_match = None
    if league_data['current_match'] < len(league_data['matches']):
        current_match = league_data['matches'][league_data['current_match']]
    
    # Calculate match progress
    total_matches = len(league_data['matches'])
    played_matches = league_data['current_match']
    
    return render(request, 'league.html', {
        'stats': sorted_stats, 
        'match': current_match,
        'played_matches': played_matches,
        'total_matches': total_matches
    })

def start_league(teams):
    pass