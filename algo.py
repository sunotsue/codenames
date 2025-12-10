from nltk.stem import PorterStemmer
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
import nltk
import gensim.downloader as api
import regex as re
import random

stemmer = PorterStemmer()
glove_wiki_model = api.load('glove-wiki-gigaword-100')
nltk.download('stopwords')

STOPWORDS = set(stopwords.words('english'))

def is_illegal_clue(clue, all_board_words):
    clue_lower = clue.lower()
    clue_stem = stemmer.stem(clue_lower)
    
    for word in all_board_words:
        word_lower = word.lower()
        word_stem = stemmer.stem(word_lower)
        
        # Check 1: Substring containment
        if clue_lower in word_lower or word_lower in clue_lower:
            return True
        
        # Check 2: Same stem (catches morphological variants)
        if clue_stem == word_stem:
            return True
    
    return False

def breakapart_compound_word(clue):
    # 1) Invalid format?
    has_bad_format = (
        '_' in clue
        or ' ' in clue
        or '-' in clue
    )
    
    if not has_bad_format:
        return [clue]
    
    parts = re.split(r'[_\-\s]+', clue)
    parts = [p for p in parts if p]
    return parts

def wordnet_similarity(clue, word):
    clue_synsets = wn.synsets(clue.lower())
    word_synsets = wn.synsets(word.lower())
    if not clue_synsets or not word_synsets:
        return 0.0
    return clue_synsets[0].wup_similarity(word_synsets[0]) or 0.0

def word2vec_similarity(clue, word, embedding_model):
    try:
        return embedding_model.similarity(clue.lower(), word.lower())
    except KeyError as e:
        # Word not in vocabulary
        return 0.0

def calc_similarity(clue, word, threshold):
    # score = wordnet_similarity(clue, word)
    # if score < threshold:
    #     return float(score)
    return float(word2vec_similarity(clue, word, glove_wiki_model))

def generate_clues_for_word(word, all_board_words):
    clues = set()
    synsets = wn.synsets(word.lower())
    
    if not synsets:
        return clues
    
    for synset in synsets: 
        for hyp in synset.hypernyms():
            for lemma in hyp.lemmas():
                clue = lemma.name()
                if is_illegal_clue(clue, all_board_words):  # Pass full list
                    continue
                for cleaned_clue in breakapart_compound_word(clue):
                    clues.add(cleaned_clue)
                    # Filter out stopwords
                    if cleaned_clue.lower() not in STOPWORDS:
                        clues.add(cleaned_clue)
    return clues

def generate_all_clues(target_words, all_board_words):
    all_clues = set()
    for target in target_words:
        word_clues = generate_clues_for_word(target, all_board_words)
        all_clues.update(word_clues)
    return all_clues
    

def score_clues(clues, target_words, avoid_words, assassin_words, risk_aversion):
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

def setup_game(num_words: int = 25):
    all_nouns = set()
    for synset in list(wn.all_synsets('n'))[:5000]:  # First 5000 noun synsets
        for lemma in synset.lemmas():
            word = lemma.name()
            # Only single words
            if word.isalpha() and '_' not in word:
                all_nouns.add(word.lower())
    
    # Sample random words
    board_words = random.sample(list(all_nouns), num_words)
    
    # Assign colors: 9 red, 8 blue, 7 neutral, 1 assassin
    colors = ['red'] * 9 + ['blue'] * 8 + ['neutral'] * 7 + ['assassin']
    random.shuffle(colors)
    
    return list(zip(board_words, colors)), random.choice(['red', 'blue'])

def make_guess(word, board, revealed):
    # Step 1: Check if word is on board
    for w, c in board:
        if w == word:
            color = c
            break
    else:
        return None, "Word not on board"

    # Step 2: Check if already revealed
    if word in revealed:
        return None, "Word already revealed"
    
    # Step 3: Mark as revealed
    revealed.add(word)
    return color, "Word revealed"

def operative_turn(clue, n, current_team, board, revealed):
    guesses_made = 0
    max_guesses = n 
    
    while guesses_made < max_guesses:
        # User input word
        guess = input(f"Clue: '{clue}' for {n}. Enter your guess: ").strip().lower()
        if guess == "pass":
            print("Operative chose to pass.")
            break
        
        # Call make_guess()
        color, message = make_guess(guess, board, revealed)
        if color is None:
            print("❌ Color not found:", message)
            continue

        if color == current_team:
            guesses_made += 1
            print(f"Correct guess! {guess} is {color}.")

        elif color == "neutral":
            print(f"{guess} is neutral. Turn ends.")
            break
        elif color == "assassin":
            print(f"{guess} is assassin! Game over.")
            return "assassin"
        else:
            print(f"Wrong guess! {guess} is {color}. Turn ends.")
            break
    return "continue"

def get_valid_integer(prompt, min_val=1, max_val=None, default=None):
    """Get validated integer input from user."""
    while True:
        user_input = input(prompt).strip()
        
        # Handle default
        if not user_input and default is not None:
            return default
        
        try:
            value = int(user_input)
            
            # Check bounds
            if value < min_val:
                print(f"❌ Must be at least {min_val}.")
                continue
            
            if max_val is not None and value > max_val:
                print(f"❌ Must be at most {max_val}.")
                continue
            
            return value
        
        except ValueError:
            print("❌ Please enter a valid number.")

def spymaster_turn(targets, avoids, assassins, revealed, board, risk_aversion):
    targets = [w for w in targets if w not in revealed]
    all_board_words = [w for w, c in board]
    clues = generate_all_clues(targets, all_board_words)
    clue_scores = score_clues(clues, targets, avoids, assassins, risk_aversion)
    clue_scores = sorted(clue_scores.items(), key=lambda x: x[1], reverse=True)
    
    print("Top clue suggestions:")
    print(clue_scores[:10])
    
    clue = input(f"Enter your clue: ").strip().lower()
    n = get_valid_integer(f"Enter n (1-{len(targets)}): ", min_val=1, max_val=len(targets))
    
    return clue, n
    

def play_game(board, starting_team):

    # Alternates between teams
    # Calls spymaster_turn() then operative_turn()
    # Checks win conditions
    # Ends when game is over
    current_team = starting_team
    game_over = False
    revealed = set()
    
    while not game_over:
        targets = [w for w, c in board if c == current_team and w not in revealed]
        avoids = [w for w, c in board if c != current_team and c != 'neutral' and c != 'assassin' and w not in revealed] 
        assassins = [w for w, c in board if c == 'assassin' and w not in revealed]
    
        print('targets:', targets)
        print('avoids:', avoids)
        print('assassins:', assassins)
        clue, n = spymaster_turn(targets, avoids, assassins, revealed, board, risk_aversion=2)
        turn_result = operative_turn(clue, int(n), current_team, board, revealed)
        if turn_result == "assassin":
            print(f"{current_team} team loses!")
            game_over = True
        elif all(t in revealed for t in targets):
            print(f"{current_team} team wins!")
            game_over = True
        else:
            current_team = 'blue' if current_team == 'red' else 'red'

if __name__ == "__main__":
    board, starting_team = setup_game()
    print('board')
    print(board)
    print('starting team:', starting_team)
    play_game(board, starting_team)