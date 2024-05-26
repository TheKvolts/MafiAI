class PredictorAI:
    def __init__(self, players, ids):

        # Players in the game. Dictionary object.
        self.players = players

        # Keep track of the current players in the game. List of player IDs.
        self.current = ids.copy()
        # Keep track of the deaths: List of tuples (Round, Player Object)
        self.deaths = []

        # Keep track of the world facts: Ex. (Round number, 'Kvolts has been killed')
        self.world_facts = []

        self.round_descriptions = []
        # 0: [[' hey what's  up hello'], [' hey what's  up hello'], [' hey what's  up hello']]

        self.predictions = []  # A list of predictions after each .round.


# Change this later.
