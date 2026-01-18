# Football Tournament Manager

A Django-based web application for managing football tournaments with multiple formats.

## Features

- **League Tournament**: Round-robin format where every team plays every other team
- **Knockout Tournament**: Single elimination bracket (requires power of 2 teams)
- **Multi-Stage Tournament**: Group stage followed by knockout playoffs

## Setup & Installation

1. Install Python from: https://www.python.org/downloads/
   (Make sure to check "Add Python to PATH" during installation)

2. Open Command Prompt and navigate to the project folder:
   ```
   cd "path\to\Fixture generator"
   ```

3. Install Django:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python main.py runserver
   ```

5. Open your web browser and go to: http://127.0.0.1:8000/

## How to Use

### Adding Teams
1. On the home page, enter team names in the input field
2. Click "Add Team" to add each team
3. You can remove individual teams or clear all teams

### Starting Tournaments

#### League Tournament
- Requires at least 2 teams
- Choose number of rounds (1-10)
- Every team plays every other team
- Points: Win = 3, Draw = 1, Loss = 0

#### Knockout Tournament
- Requires power of 2 teams (2, 4, 8, 16, etc.)
- Single elimination format
- Penalty shootout for tied matches

#### Multi-Stage Tournament
- Requires at least 4 teams
- Group stage followed by knockout playoffs
- Group winners advance to knockout rounds

## File Structure

- `main.py` - Django management script
- `settings.py` - Django configuration
- `urls.py` - URL routing
- `league.py` - League tournament logic
- `knockout.py` - Knockout tournament logic
- `multistage.py` - Multi-stage tournament logic
- `templates/` - HTML templates
- `teams.json` - Team data storage
- `tournament.db` - SQLite database

## Troubleshooting

If you get an import error, make sure Django is installed:
```
pip install django
```

If the server won't start, try a different port:
```
python main.py runserver 8080
```