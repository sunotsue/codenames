from nltk.stem import PorterStemmer
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
import nltk
import gensim.downloader as api
import regex as re
import random

stemmer = PorterStemmer()
glove_wiki_model = api.load('glove-wiki-gigaword-100')

try:
    STOPWORDS = set(stopwords.words('english'))
except:
    nltk.download('stopwords')
    STOPWORDS = set(stopwords.words('english'))

# ============================================
# CORE GAME LOGIC (No input/output)
# ============================================

class CodenamesGame:
    """Pure game state and logic - no I/O"""
    
    def __init__(self, board=None, starting_team=None):
        if board is None:
            board, starting_team = setup_game()
        
        self.board = board  # List of (word, color) tuples
        self.current_team = starting_team
        self.revealed = set()
        self.game_over = False
        self.winner = None
        self.current_clue = None
        self.current_n = 0
        self.guesses_made = 0
    
    def get_unrevealed_by_color(self, color):
        """Get unrevealed words of a specific color"""
        return [w for w, c in self.board if c == color and w not in self.revealed]
    
    def get_all_words(self):
        """Get all board words"""
        return [w for w, c in self.board]
    
    def get_counts(self):
        """Count remaining words by color"""
        counts = {'red': 0, 'blue': 0, 'neutral': 0, 'assassin': 0}
        for word, color in self.board:
            if word not in self.revealed:
                counts[color] += 1
        return counts
    
    def make_guess(self, word):
        """
        Make a guess. Returns (success, color, message)
        
        success: True if guess was valid
        color: color of guessed word (or None)
        message: description of what happened
        """
        # Check if word on board
        word_color = None
        for w, c in self.board:
            if w.lower() == word.lower():
                word_color = c
                break
        
        if word_color is None:
            return False, None, "Word not on board"
        
        if word in self.revealed:
            return False, None, "Already revealed"
        
        # Reveal the word
        self.revealed.add(word)
        self.guesses_made += 1
        
        # Check results
        if word_color == 'assassin':
            opponent = 'blue' if self.current_team == 'red' else 'red'
            self.game_over = True
            self.winner = opponent
            return True, word_color, "Assassin hit! Game over."
        
        if word_color == self.current_team:
            # Check if team won
            if not self.get_unrevealed_by_color(self.current_team):
                self.game_over = True
                self.winner = self.current_team
                return True, word_color, "Correct! Team wins!"
            return True, word_color, "Correct!"
        
        # Wrong color - check if opponent won
        if word_color != 'neutral':
            opponent = 'blue' if self.current_team == 'red' else 'red'
            if not self.get_unrevealed_by_color(opponent):
                self.game_over = True
                self.winner = opponent
                return True, word_color, f"Wrong! {opponent} wins!"
        
        return True, word_color, f"Wrong! It's {word_color}."
    
    def set_clue(self, clue, n):
        """Spymaster sets clue"""
        self.current_clue = clue
        self.current_n = n
        self.guesses_made = 0
    
    def end_turn(self):
        """End current team's turn"""
        opponent = 'blue' if self.current_team == 'red' else 'red'
        self.current_team = opponent
        self.current_clue = None
        self.current_n = 0
        self.guesses_made = 0
    
    def should_end_turn(self, guessed_color):
        """Check if turn should end based on guess result"""
        if guessed_color == 'assassin':
            return True
        if guessed_color != self.current_team:
            return True
        if self.guesses_made >= self.current_n:
            return True
        return False


# ============================================
# HELPER FUNCTIONS (Pure functions - no state)
# ============================================

def is_illegal_clue(clue, all_board_words):
    clue_lower = clue.lower()
    clue_stem = stemmer.stem(clue_lower)
    
    for word in all_board_words:
        word_lower = word.lower()
        word_stem = stemmer.stem(word_lower)
        
        if clue_lower in word_lower or word_lower in clue_lower:
            return True
        if clue_stem == word_stem:
            return True
    
    return False

def breakapart_compound_word(clue):
    has_bad_format = ('_' in clue or ' ' in clue or '-' in clue)
    if not has_bad_format:
        return [clue]
    parts = re.split(r'[_\-\s]+', clue)
    return [p for p in parts if p]

def wordnet_similarity(clue, word):
    clue_synsets = wn.synsets(clue.lower())
    word_synsets = wn.synsets(word.lower())
    if not clue_synsets or not word_synsets:
        return 0.0
    return clue_synsets[0].wup_similarity(word_synsets[0]) or 0.0

def word2vec_similarity(clue, word):
    try:
        return glove_wiki_model.similarity(clue.lower(), word.lower())
    except KeyError:
        return 0.0

def calc_similarity(clue, word, threshold=0.3):
    return float(word2vec_similarity(clue, word))

def generate_clues_for_word(word, all_board_words):
    clues = set()
    synsets = wn.synsets(word.lower())
    
    if not synsets:
        return clues
    
    for synset in synsets: 
        for hyp in synset.hypernyms():
            for lemma in hyp.lemmas():
                clue = lemma.name()
                if is_illegal_clue(clue, all_board_words):
                    continue
                for cleaned_clue in breakapart_compound_word(clue):
                    if cleaned_clue.lower() not in STOPWORDS and len(cleaned_clue) >= 3:
                        clues.add(cleaned_clue)
    return clues

def generate_all_clues(target_words, all_board_words):
    all_clues = set()
    for target in target_words:
        word_clues = generate_clues_for_word(target, all_board_words)
        all_clues.update(word_clues)
    return all_clues

def score_clues(clues, target_words, avoid_words, assassin_words, risk_aversion=2.0):
    scored_clues = {}
    for clue in clues:
        total_score = 0.0
        for target in target_words:
            total_score += calc_similarity(clue, target, 0.3)
        for avoid in avoid_words:
            total_score -= calc_similarity(clue, avoid, 0.3)
        for assassin in assassin_words:
            total_score -= calc_similarity(clue, assassin, 0.3) * risk_aversion
        scored_clues[clue] = total_score
    return scored_clues

def setup_game(num_words=25):
    all_nouns = set()
    for synset in list(wn.all_synsets('n'))[:5000]:
        for lemma in synset.lemmas():
            word = lemma.name()
            if word.isalpha() and '_' not in word and len(word) > 3:
                all_nouns.add(word.lower())
    
    board_words = random.sample(list(all_nouns), num_words)
    colors = ['red'] * 9 + ['blue'] * 8 + ['neutral'] * 7 + ['assassin']
    random.shuffle(colors)
    
    return list(zip(board_words, colors)), random.choice(['red', 'blue'])