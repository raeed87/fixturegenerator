"""Knockout Tournament Views"""
from django.shortcuts import render, redirect
import json
import os
import random
import math

TEAMS_FILE = 'teams.json'
KNOCKOUT_FILE = 'knockout_data.json'

def load_teams():
    if os.path.exists(TEAMS_FILE):
        with open(TEAMS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_knockout(data):
    with open(KNOCKOUT_FILE, 'w') as f:
        json.dump(data, f)

def load_knockout():
    if os.path.exists(KNOCKOUT_FILE):
        with open(KNOCKOUT_FILE, 'r') as f:
            return json.load(f)
    return None

def start_knockout_tournament(request):
    if request.method == 'POST':
        teams = load_teams()
        if len(teams) < 2:
            return redirect('home')
        
        # Check if number of teams is power of 2
        if len(teams) & (len(teams) - 1) != 0:
            # Not power of 2, show error
            from league import league_home
            return render(request, 'home.html', {
                'teams': teams,
                'knockout_error': f'Need power of 2 teams (2, 4, 8, 16...). You have {len(teams)} teams.'
            })
        
        # Shuffle teams for random bracket
        random.shuffle(teams)
        
        # Create initial bracket
        bracket = []
        for i in range(0, len(teams), 2):
            bracket.append([teams[i], teams[i+1]])
        
        knockout_data = {
            'bracket': bracket,
            'current_match': 0,
            'round_name': get_round_name(len(teams)),
            'teams_remaining': len(teams)
        }
        save_knockout(knockout_data)
        return redirect('knockout_match')
    return redirect('home')

def get_round_name(teams_count):
    if teams_count == 2:
        return "Final"
    elif teams_count == 4:
        return "Semi-Final"
    elif teams_count == 8:
        return "Quarter-Final"
    elif teams_count == 16:
        return "Round of 16"
    else:
        return f"Round of {teams_count}"

def knockout_match(request):
    knockout_data = load_knockout()
    if not knockout_data:
        return redirect('home')
    
    if request.method == 'POST':
        score1 = int(request.POST.get('score1', 0))
        score2 = int(request.POST.get('score2', 0))
        
        # Determine winner
        if score1 == score2:
            penalty_winner = request.POST.get('penalty_winner')
            if penalty_winner:
                winner = penalty_winner
            else:
                return render(request, 'knockout.html', {
                    'knockout_data': knockout_data,
                    'current_match': knockout_data['bracket'][knockout_data['current_match']] if knockout_data['current_match'] < len(knockout_data['bracket']) else None,
                    'match_number': knockout_data['current_match'] + 1,
                    'total_matches': len(knockout_data['bracket']),
                    'error': 'Please select penalty winner.',
                    'bracket_visualization': generate_bracket_visualization(knockout_data)
                })
        else:
            winner = knockout_data['bracket'][knockout_data['current_match']][0] if score1 > score2 else knockout_data['bracket'][knockout_data['current_match']][1]
        
        # Store match result
        if 'results' not in knockout_data:
            knockout_data['results'] = []
        knockout_data['results'].append({
            'teams': knockout_data['bracket'][knockout_data['current_match']],
            'scores': [score1, score2],
            'winner': winner
        })
        
        # Add winner to next round
        if 'next_round' not in knockout_data:
            knockout_data['next_round'] = []
        knockout_data['next_round'].append(winner)
        
        knockout_data['current_match'] += 1
        
        # Check if current round is complete
        if knockout_data['current_match'] >= len(knockout_data['bracket']):
            if len(knockout_data['next_round']) == 1:
                # Tournament complete - we have a winner
                knockout_data['winner'] = knockout_data['next_round'][0]
            elif len(knockout_data['next_round']) >= 2:
                # Start next round with winners
                next_teams = knockout_data['next_round']
                knockout_data['bracket'] = []
                
                # Create new bracket from winners
                for i in range(0, len(next_teams), 2):
                    if i + 1 < len(next_teams):
                        knockout_data['bracket'].append([next_teams[i], next_teams[i+1]])
                
                knockout_data['current_match'] = 0
                knockout_data['next_round'] = []
                knockout_data['round_name'] = get_round_name(len(next_teams))
                knockout_data['teams_remaining'] = len(next_teams)
        
        save_knockout(knockout_data)
        return redirect('knockout_match')
    
    # Get current match
    current_match = None
    if 'winner' not in knockout_data and knockout_data['current_match'] < len(knockout_data['bracket']):
        current_match = knockout_data['bracket'][knockout_data['current_match']]
    
    return render(request, 'knockout.html', {
        'knockout_data': knockout_data,
        'current_match': current_match,
        'match_number': knockout_data['current_match'] + 1 if current_match else 0,
        'total_matches': len(knockout_data['bracket']),
        'error': request.GET.get('error'),
        'bracket_visualization': generate_bracket_visualization(knockout_data)
    })

def generate_bracket_visualization(knockout_data):
    visualization = []
    
    # Current round
    if knockout_data['bracket']:
        current_round = {
            'name': knockout_data.get('round_name', 'Current Round'),
            'matches': []
        }
        
        for i, match in enumerate(knockout_data['bracket']):
            match_data = {
                'teams': match,
                'completed': i < knockout_data['current_match'],
                'current': i == knockout_data['current_match'],
                'winner': None,
                'score': [0, 0]
            }
            
            # Find result if completed
            if 'results' in knockout_data:
                for result in knockout_data['results']:
                    if result['teams'] == match:
                        match_data['winner'] = result['winner']
                        match_data['score'] = result['scores']
                        break
            
            current_round['matches'].append(match_data)
        
        visualization.append(current_round)
    
    # Winner
    if 'winner' in knockout_data:
        final_round = {
            'name': 'Champion',
            'matches': [{
                'teams': [knockout_data['winner']],
                'completed': True,
                'current': False,
                'winner': knockout_data['winner'],
                'score': []
            }]
        }
        visualization.append(final_round)
    
    return visualization