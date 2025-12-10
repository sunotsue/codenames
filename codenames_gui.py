import tkinter as tk
from tkinter import messagebox, scrolledtext
from codenames_game import (
    CodenamesGame, 
    generate_all_clues, 
    score_clues,
    is_illegal_clue
)

class CodenamesGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Codenames")
        self.root.geometry("1000x800")
        
        # Create game
        self.game = CodenamesGame()
        self.spymaster_mode = True  # Start in spymaster mode
        
        # Create UI
        self.create_widgets()
        self.update_display()
    
    def create_widgets(self):
        # Top control panel
        control_frame = tk.Frame(self.root, bg='lightgray', height=100)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Mode indicator
        self.mode_label = tk.Label(
            control_frame,
            text="MODE: SPYMASTER",
            font=('Arial', 14, 'bold'),
            bg='lightgray',
            fg='red'
        )
        self.mode_label.pack(side=tk.LEFT, padx=10)
        
        # Team indicator
        self.team_label = tk.Label(
            control_frame,
            text="",
            font=('Arial', 16, 'bold'),
            bg='lightgray'
        )
        self.team_label.pack(side=tk.LEFT, padx=20)
        
        # Score display
        self.score_label = tk.Label(
            control_frame,
            text="",
            font=('Arial', 12),
            bg='lightgray'
        )
        self.score_label.pack(side=tk.LEFT, padx=20)
        
        # Board frame (5x5 grid)
        board_frame = tk.Frame(self.root)
        board_frame.pack(pady=20)
        
        self.word_buttons = []
        for i in range(25):
            row = i // 5
            col = i % 5
            
            btn = tk.Button(
                board_frame,
                text="",
                width=15,
                height=3,
                font=('Arial', 12, 'bold'),
                command=lambda idx=i: self.on_word_click(idx)
            )
            btn.grid(row=row, column=col, padx=5, pady=5)
            self.word_buttons.append(btn)
        
        # Clue area - better contrast
        clue_frame = tk.Frame(self.root, bg='#2C3E50', height=150)  # Dark blue-gray
        clue_frame.pack(fill=tk.X, padx=10, pady=10)

        self.clue_label = tk.Label(
            clue_frame,
            text="SPYMASTER: Give a clue to your team",
            font=('Arial', 18, 'bold'),
            bg='#2C3E50',
            fg='white'  # White text on dark background
        )
        self.clue_label.pack(pady=10)
        
        # Spymaster input area
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10)
        
        self.suggest_btn = tk.Button(
            input_frame,
            text="🤖 Get AI Suggestions",
            command=self.show_suggestions,
            font=('Arial', 12),
            bg='lightblue'
        )
        self.suggest_btn.pack(side=tk.LEFT, padx=5)
        
        self.input_label1 = tk.Label(input_frame, text="Clue:", font=('Arial', 12))
        self.input_label1.pack(side=tk.LEFT, padx=5)
        
        self.clue_entry = tk.Entry(input_frame, width=20, font=('Arial', 12))
        self.clue_entry.pack(side=tk.LEFT, padx=5)
        
        self.input_label2 = tk.Label(input_frame, text="Number:", font=('Arial', 12))
        self.input_label2.pack(side=tk.LEFT, padx=5)
        
        self.n_entry = tk.Entry(input_frame, width=5, font=('Arial', 12))
        self.n_entry.pack(side=tk.LEFT, padx=5)
        
        self.submit_btn = tk.Button(
            input_frame,
            text="✅ Submit Clue",
            command=self.submit_clue,
            font=('Arial', 12),
            bg='lightgreen'
        )
        self.submit_btn.pack(side=tk.LEFT, padx=5)
        
        self.pass_btn = tk.Button(
            input_frame,
            text="⏭️ Pass Turn",
            command=self.pass_turn,
            font=('Arial', 12),
            bg='orange'
        )
        self.pass_btn.pack(side=tk.LEFT, padx=5)
        self.pass_btn.config(state=tk.DISABLED)
        
        # Log area
        log_frame = tk.Frame(self.root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(log_frame, text="Game Log:", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=('Arial', 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def switch_to_spymaster_mode(self):
        """Switch to spymaster mode - giving clues"""
        self.spymaster_mode = True
        self.mode_label.config(text="MODE: SPYMASTER", fg='red')
        
        # Enable spymaster controls
        self.suggest_btn.config(state=tk.NORMAL)
        self.input_label1.config(text="Clue:")
        self.clue_entry.config(state=tk.NORMAL)
        self.input_label2.config(text="Number:")
        self.n_entry.config(state=tk.NORMAL)
        self.submit_btn.config(state=tk.NORMAL, text="✅ Submit Clue")
        self.pass_btn.config(state=tk.DISABLED)
        
        self.clue_label.config(text="SPYMASTER: Give a clue to your team")
        
        self.update_display()
        self.log(f"🎯 {self.game.current_team.upper()} SPYMASTER's turn")
    
    def switch_to_operative_mode(self):
        """Switch to operative mode - guessing words"""
        self.spymaster_mode = False
        self.mode_label.config(text="MODE: OPERATIVE", fg='blue')
        
        # Disable spymaster controls
        self.suggest_btn.config(state=tk.DISABLED)
        self.clue_entry.config(state=tk.DISABLED)
        self.n_entry.config(state=tk.DISABLED)
        self.submit_btn.config(state=tk.DISABLED)
        self.pass_btn.config(state=tk.NORMAL)
        
        self.update_display()
        self.log(f"👥 {self.game.current_team.upper()} OPERATIVES' turn - Click words to guess")
    
    def update_display(self):
        """Update board colors and game state display"""
        # Update board buttons
        for i, (word, color) in enumerate(self.game.board):
            btn = self.word_buttons[i]
            btn.config(text=word.upper())
            
            if word in self.game.revealed:
                # Word has been revealed - show actual color (BRIGHT)
                color_map = {
                    'red': '#FF0000',
                    'blue': '#0000FF',
                    'neutral': '#FFFF00',
                    'assassin': '#000000'
                }
                text_color = 'white' if color in ['red', 'blue', 'assassin'] else 'black'
                btn.config(
                    bg=color_map[color],
                    fg=text_color,
                    activebackground=color_map[color],  # Mac fix
                    highlightbackground=color_map[color],  # Mac fix
                    state=tk.DISABLED,
                    relief=tk.SUNKEN
                )
            elif self.spymaster_mode:
                # Spymaster view - DARKER colors with Mac fixes
                color_map = {
                    'red': '#FF6B6B',
                    'blue': '#4ECDC4',
                    'neutral': '#F7DC6F',
                    'assassin': '#95A5A6'
                }
                btn.config(
                    bg=color_map[color],
                    fg='black',
                    activebackground=color_map[color],  # Mac fix
                    highlightbackground=color_map[color],  # Mac fix
                    highlightcolor=color_map[color],  # Mac fix
                    state=tk.NORMAL,
                    relief=tk.RAISED
                )
                print(f"Set {word} to {color} = {color_map[color]}")  # Debug
            else:
                # Operative view - all white
                btn.config(
                    bg='#FFFFFF',
                    fg='black',
                    activebackground='#FFFFFF',  # Mac fix
                    highlightbackground='#FFFFFF',  # Mac fix
                    state=tk.NORMAL,
                    relief=tk.RAISED
                )
        
        # Update score
        counts = self.game.get_counts()
        self.score_label.config(
            text=f"Red: {counts['red']} | Blue: {counts['blue']} | Neutral: {counts['neutral']}"
        )
        
        # Update team label
        color = 'red' if self.game.current_team == 'red' else 'blue'
        self.team_label.config(
            text=f"🎯 {self.game.current_team.upper()} TEAM",
            fg=color
        )
    
    def on_word_click(self, idx):
        """Handle clicking a word on the board"""
        if self.game.game_over:
            messagebox.showinfo("Game Over", "Game has ended!")
            return
        
        if self.spymaster_mode:
            messagebox.showwarning("Spymaster Mode", "Submit a clue first! Then operatives will guess.")
            return
        
        word, _ = self.game.board[idx]
        
        if word in self.game.revealed:
            self.log(f"⚠️ '{word}' already revealed!")
            return
        
        if not self.game.current_clue:
            messagebox.showwarning("No Clue", "Spymaster must give a clue first!")
            return
        
        # Make guess
        success, guessed_color, message = self.game.make_guess(word)
        
        if not success:
            self.log(f"❌ {message}")
            return
        
        # Log the guess
        emoji_map = {
            'red': '🔴',
            'blue': '🔵',
            'neutral': '⚪',
            'assassin': '💀'
        }
        emoji = emoji_map.get(guessed_color, '❓')
        self.log(f"{emoji} Guessed: '{word}' → {guessed_color.upper()} ({self.game.guesses_made}/{self.game.current_n})")
        
        self.update_display()
        
        # Check game over
        if self.game.game_over:
            winner_emoji = '🏆'
            self.log(f"{winner_emoji} GAME OVER: {self.game.winner.upper()} WINS!")
            messagebox.showinfo("Game Over", f"🏆 {self.game.winner.upper()} TEAM WINS! 🏆")
            self.disable_controls()
            return
        
        # Check if turn should end
        if self.game.should_end_turn(guessed_color):
            if guessed_color == self.game.current_team:
                # All guesses were correct!
                self.log(f"✅ All {self.game.current_n} guesses correct!")
                self.log(f"🎯 {self.game.current_team.upper()} team continues - Spymaster give new clue!")
                
                # Reset clue but keep same team
                self.game.current_clue = None
                self.game.current_n = 0
                self.game.guesses_made = 0
                self.switch_to_spymaster_mode()  # Stay with same team
            else:
                # Wrong color - switch teams
                self.log(f"❌ Wrong color - turn ends")
                self.game.end_turn()
                self.reset_for_new_turn()
                
    def submit_clue(self):
        """Spymaster submits a clue"""
        clue = self.clue_entry.get().strip().lower()
        n_str = self.n_entry.get().strip()
        
        if not clue:
            messagebox.showwarning("Invalid", "Enter a clue word!")
            return
        
        try:
            n = int(n_str)
            if n < 1:
                raise ValueError
        except:
            messagebox.showwarning("Invalid", "Enter a valid number >= 1!")
            return
        
        # Check max
        targets = self.game.get_unrevealed_by_color(self.game.current_team)
        if n > len(targets):
            messagebox.showwarning("Invalid", f"Only {len(targets)} words left!")
            return
        
        # ✅ NEW: Check if clue is illegal
        from codenames_game import is_illegal_clue
        all_board_words = self.game.get_all_words()
        
        if is_illegal_clue(clue, all_board_words):
            messagebox.showwarning(
                "Illegal Clue", 
                f"'{clue}' is illegal!\n\nIt contains or matches a word on the board.\nChoose a different clue."
            )
            return
        
        self.game.set_clue(clue, n)
        
        self.clue_label.config(text=f"📢 Clue: '{clue.upper()}' for {n} word(s)")
        self.log(f"📢 Spymaster gave clue: '{clue.upper()}' for {n}")
        
        self.clue_entry.delete(0, tk.END)
        self.n_entry.delete(0, tk.END)
        
        # Switch to operative mode
        self.switch_to_operative_mode()
    
    def pass_turn(self):
        """Pass turn without using all guesses"""
        self.log(f"⏭️ {self.game.current_team.upper()} team passed (used {self.game.guesses_made}/{self.game.current_n} guesses)")
        self.game.end_turn()
        self.reset_for_new_turn()
    
    def reset_for_new_turn(self):
        """Reset UI for new turn - switch back to spymaster mode"""
        self.clue_label.config(text="SPYMASTER: Give a clue to your team")
        self.clue_entry.delete(0, tk.END)
        self.n_entry.delete(0, tk.END)
        
        # Switch to spymaster mode for new turn
        self.switch_to_spymaster_mode()
    
    def disable_controls(self):
        """Disable all controls at game end"""
        self.submit_btn.config(state=tk.DISABLED)
        self.suggest_btn.config(state=tk.DISABLED)
        self.pass_btn.config(state=tk.DISABLED)
        self.clue_entry.config(state=tk.DISABLED)
        self.n_entry.config(state=tk.DISABLED)
        for btn in self.word_buttons:
            btn.config(state=tk.DISABLED)
    
    def show_suggestions(self):
        """Show AI-generated clue suggestions"""
        targets = self.game.get_unrevealed_by_color(self.game.current_team)
        opponent = 'blue' if self.game.current_team == 'red' else 'red'
        avoids = self.game.get_unrevealed_by_color(opponent)
        neutrals = self.game.get_unrevealed_by_color('neutral')
        assassins = self.game.get_unrevealed_by_color('assassin')
        all_board_words = self.game.get_all_words()
        
        if not targets:
            messagebox.showinfo("No Targets", "No more words to guess!")
            return
        
        # How many words to connect?
        num_targets = min(3, len(targets))  # Try to connect up to 3 words
        
        self.log(f"🤖 Generating AI suggestions for {num_targets} words...")
        clues = generate_all_clues(targets[:num_targets], all_board_words)
        
        if not clues:
            messagebox.showinfo("No Clues", "Couldn't generate valid clues!")
            return
        
        scored = score_clues(clues, targets[:num_targets], avoids + neutrals, assassins)
        top_clues = sorted(scored.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Show in popup window
        suggestions_window = tk.Toplevel(self.root)
        suggestions_window.title("AI Clue Suggestions")
        suggestions_window.geometry("500x400")
        
        tk.Label(
            suggestions_window,
            text=f"🤖 Top 5 AI Suggestions",
            font=('Arial', 16, 'bold')
        ).pack(pady=10)
        
        tk.Label(
            suggestions_window,
            text=f"(Trying to connect: {', '.join(targets[:num_targets])})",
            font=('Arial', 10, 'italic')
        ).pack(pady=5)
        
        for i, (clue, score) in enumerate(top_clues, 1):
            frame = tk.Frame(suggestions_window)
            frame.pack(fill=tk.X, padx=20, pady=5)
            
            tk.Label(
                frame,
                text=f"{i}. {clue.upper()}",
                font=('Arial', 14, 'bold'),
                width=15,
                anchor=tk.W
            ).pack(side=tk.LEFT)
            
            tk.Label(
                frame,
                text=f"(score: {score:.2f})",
                font=('Arial', 10),
                fg='gray'
            ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            suggestions_window,
            text="Close",
            command=suggestions_window.destroy,
            font=('Arial', 12)
        ).pack(pady=20)
    
    def log(self, message):
        """Add message to game log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = CodenamesGUI(root)
    root.mainloop()