"""Multi-Stage Tournament Views"""
from django.shortcuts import render, redirect
import json
import os
import random
import math

TEAMS_FILE = 'teams.json'
MULTISTAGE_FILE = 'multistage_data.json'

def load_teams():
    if os.path.exists(TEAMS_FILE):
        with open(TEAMS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_multistage(data):
    with open(MULTISTAGE_FILE, 'w') as f:
        json.dump(data, f)

def load_multistage():
    if os.path.exists(MULTISTAGE_FILE):
        with open(MULTISTAGE_FILE, 'r') as f:
            return json.load(f)
    return None

def start_multistage_tournament(request):
    if request.method == 'POST':
        teams = load_teams()
        if len(teams) < 4:
            return redirect('home')
        
        # Shuffle teams
        random.shuffle(teams)
        
        # Check if preliminary round needed
        ideal_groups = len(teams) // 4
        teams_for_groups = ideal_groups * 4
        extra_teams = len(teams) - teams_for_groups
        
        multistage_data = {
            'stage': 'preliminary' if extra_teams > 0 else 'group',
            'qualified_teams': []
        }
        
        if extra_teams > 0 and extra_teams % 2 == 0:
            # Preliminary round needed (only if even number of extra teams)
            preliminary_teams = teams[-extra_teams:]  # Last teams go to preliminary
            remaining_teams = teams[:-extra_teams]    # Rest wait for group stage
            
            # Create preliminary matches (pairs of extra teams)
            preliminary_matches = []
            for i in range(0, len(preliminary_teams), 2):
                if i + 1 < len(preliminary_teams):
                    preliminary_matches.append((preliminary_teams[i], preliminary_teams[i+1]))
            
            multistage_data.update({
                'preliminary_matches': preliminary_matches,
                'preliminary_winners': [],
                'current_preliminary': 0,
                'remaining_teams': remaining_teams
            })
        else:
            # Direct to group stage (adjust group sizes if needed)
            multistage_data.update(create_groups(teams))
            multistage_data['stage'] = 'group'
        
        save_multistage(multistage_data)
        return redirect('multistage_match')
    return redirect('home')

def create_groups(teams):
    # Create groups (4 teams per group for optimal balance)
    groups = []
    group_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    
    for i in range(0, len(teams), 4):
        group_teams = teams[i:i+4]
        if len(group_teams) >= 3:  # Minimum 3 teams per group
            group_stats = {}
            group_matches = []
            
            # Initialize stats for all teams in group
            for team in group_teams:
                group_stats[team] = {'P': 0, 'W': 0, 'D': 0, 'L': 0, 'GF': 0, 'GA': 0, 'GD': 0, 'Pts': 0}
            
            # Generate all possible matches in group (round-robin)
            for j in range(len(group_teams)):
                for k in range(j+1, len(group_teams)):
                    group_matches.append((group_teams[j], group_teams[k]))
            
            groups.append({
                'name': group_names[len(groups)],
                'teams': group_teams,
                'stats': group_stats,
                'matches': group_matches,
                'current_match': 0,
                'completed': False
            })
    
    return {
        'groups': groups,
        'current_group': 0
    }

def multistage_match(request):
    multistage_data = load_multistage()
    if not multistage_data:
        return redirect('home')
    
    if multistage_data['stage'] == 'preliminary':
        return handle_preliminary_stage(request, multistage_data)
    elif multistage_data['stage'] == 'group':
        return handle_group_stage(request, multistage_data)
    else:
        return handle_knockout_stage(request, multistage_data)

def handle_preliminary_stage(request, multistage_data):
    if request.method == 'POST':
        score1 = int(request.POST.get('score1', 0))
        score2 = int(request.POST.get('score2', 0))
        
        match = multistage_data['preliminary_matches'][multistage_data['current_preliminary']]
        team1, team2 = match
        
        # Determine winner (no draws in preliminary)
        if score1 == score2:
            penalty_winner = request.POST.get('penalty_winner')
            if penalty_winner:
                winner = penalty_winner
            else:
                return render(request, 'multistage.html', {
                    'multistage_data': multistage_data,
                    'current_match': match,
                    'stage': 'preliminary',
                    'error': 'Please select penalty winner.'
                })
        else:
            winner = team1 if score1 > score2 else team2
        
        multistage_data['preliminary_winners'].append(winner)
        multistage_data['current_preliminary'] += 1
        
        # Check if all preliminary matches done
        if multistage_data['current_preliminary'] >= len(multistage_data['preliminary_matches']):
            # Move to group stage
            all_teams = multistage_data['remaining_teams'] + multistage_data['preliminary_winners']
            random.shuffle(all_teams)
            
            multistage_data.update(create_groups(all_teams))
            multistage_data['stage'] = 'group'
        
        save_multistage(multistage_data)
        return redirect('multistage_match')
    
    # Get current preliminary match
    current_match = None
    if multistage_data['current_preliminary'] < len(multistage_data['preliminary_matches']):
        current_match = multistage_data['preliminary_matches'][multistage_data['current_preliminary']]
    
    return render(request, 'multistage.html', {
        'multistage_data': multistage_data,
        'current_match': current_match,
        'stage': 'preliminary'
    })

def handle_group_stage(request, multistage_data):
    if request.method == 'POST':
        score1 = int(request.POST.get('score1', 0))
        score2 = int(request.POST.get('score2', 0))
        
        current_group = multistage_data['groups'][multistage_data['current_group']]
        match = current_group['matches'][current_group['current_match']]
        team1, team2 = match
        
        # Update stats
        stats = current_group['stats']
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
        
        current_group['current_match'] += 1
        
        # Check if group is complete
        if current_group['current_match'] >= len(current_group['matches']):
            current_group['completed'] = True
            # Get top 2 teams from group (standard qualification)
            sorted_stats = sorted(current_group['stats'].items(), key=lambda x: (x[1]['Pts'], x[1]['GD'], x[1]['GF']), reverse=True)
            
            # Qualify top 2 teams
            for i in range(min(2, len(sorted_stats))):
                if sorted_stats[i][0] not in multistage_data['qualified_teams']:
                    multistage_data['qualified_teams'].append(sorted_stats[i][0])
            
            # Move to next group
            multistage_data['current_group'] += 1
            
            # Check if all groups are complete
            if multistage_data['current_group'] >= len(multistage_data['groups']):
                # Start knockout stage with all qualified teams
                qualified = multistage_data['qualified_teams']
                
                if len(qualified) >= 2:
                    # Create knockout bracket with all qualified teams
                    bracket = []
                    for i in range(0, len(qualified), 2):
                        if i + 1 < len(qualified):
                            bracket.append([qualified[i], qualified[i+1]])
                    
                    multistage_data['stage'] = 'knockout'
                    multistage_data['bracket'] = bracket
                    multistage_data['current_match'] = 0
                    multistage_data['round_name'] = get_round_name(len(qualified))
        
        save_multistage(multistage_data)
        return redirect('multistage_match')
    
    # Get current match
    current_match = None
    current_group = None
    if 'groups' in multistage_data and multistage_data['current_group'] < len(multistage_data['groups']):
        current_group = multistage_data['groups'][multistage_data['current_group']]
        if current_group['current_match'] < len(current_group['matches']):
            current_match = current_group['matches'][current_group['current_match']]
    
    return render(request, 'multistage.html', {
        'multistage_data': multistage_data,
        'current_match': current_match,
        'current_group': current_group,
        'sorted_groups': get_sorted_groups(multistage_data) if 'groups' in multistage_data else []
    })

def get_sorted_groups(multistage_data):
    sorted_groups = []
    if 'groups' in multistage_data:
        for group in multistage_data['groups']:
            # Sort teams by performance (Points, Goal Difference, Goals For)
            sorted_stats = sorted(group['stats'].items(), key=lambda x: (x[1]['Pts'], x[1]['GD'], x[1]['GF']), reverse=True)
            group_copy = group.copy()
            group_copy['sorted_stats'] = sorted_stats
            sorted_groups.append(group_copy)
    return sorted_groups

def handle_knockout_stage(request, multistage_data):
    if request.method == 'POST':
        score1 = int(request.POST.get('score1', 0))
        score2 = int(request.POST.get('score2', 0))
        
        # Handle penalty if needed
        if score1 == score2:
            penalty_winner = request.POST.get('penalty_winner')
            if penalty_winner:
                winner = penalty_winner
            else:
                return render(request, 'multistage.html', {
                    'multistage_data': multistage_data,
                    'current_match': multistage_data['bracket'][multistage_data['current_match']] if multistage_data['current_match'] < len(multistage_data['bracket']) else None,
                    'stage': 'knockout',
                    'error': 'Please select penalty winner.'
                })
        else:
            winner = multistage_data['bracket'][multistage_data['current_match']][0] if score1 > score2 else multistage_data['bracket'][multistage_data['current_match']][1]
        
        # Add winner to next round
        if 'next_round' not in multistage_data:
            multistage_data['next_round'] = []
        multistage_data['next_round'].append(winner)
        
        multistage_data['current_match'] += 1
        
        # Check if round is complete
        if multistage_data['current_match'] >= len(multistage_data['bracket']):
            if len(multistage_data['next_round']) == 1:
                # Tournament complete
                multistage_data['winner'] = multistage_data['next_round'][0]
            else:
                # Start next round
                multistage_data['bracket'] = []
                next_teams = multistage_data['next_round']
                for i in range(0, len(next_teams), 2):
                    if i + 1 < len(next_teams):
                        multistage_data['bracket'].append([next_teams[i], next_teams[i+1]])
                multistage_data['current_match'] = 0
                multistage_data['next_round'] = []
                multistage_data['round_name'] = get_round_name(len(next_teams))
        
        save_multistage(multistage_data)
        return redirect('multistage_match')
    
    # Get current match
    current_match = None
    if 'current_match' in multistage_data and multistage_data['current_match'] < len(multistage_data.get('bracket', [])):
        current_match = multistage_data['bracket'][multistage_data['current_match']]
    
    return render(request, 'multistage.html', {
        'multistage_data': multistage_data,
        'current_match': current_match,
        'stage': 'knockout'
    })

def get_round_name(teams_count):
    if teams_count == 2:
        return "Final"
    elif teams_count == 4:
        return "Semi-Final"
    elif teams_count == 8:
        return "Quarter-Final"
    else:
        return f"Round of {teams_count}"

def multistage_groups(request):
    multistage_data = load_multistage()
    if not multistage_data or 'groups' not in multistage_data:
        return redirect('home')
    
    return render(request, 'multistage_groups.html', {
        'multistage_data': multistage_data,
        'sorted_groups': get_sorted_groups(multistage_data)
    })