"""
Cricket Commentary Generator
Generates realistic cricket commentary based on match events
"""

import random
from typing import Dict, List, Optional
from app.models.cricket import CricketBall


class CricketCommentaryGenerator:
    """Generate realistic cricket commentary for various match events"""

    def __init__(self):
        self.commentary_templates = {
            "four": [
                "FOUR! Beautifully timed through the covers!",
                "Boundary! What a shot! Races away to the fence!",
                "FOUR! Perfectly placed, the fielder had no chance!",
                "Glorious stroke! Four runs to the boundary!",
                "FOUR! Shot! That's bread and butter for any batsman!",
                "Exquisite timing! The ball finds the gap perfectly!",
            ],
            "six": [
                "SIX! What a massive hit! That's gone out of the stadium!",
                "Maximum! Absolutely smashed into the stands!",
                "SIX! Clean strike! The crowd is on its feet!",
                "Gone! Gone! GONE! That's a monster six!",
                "SIX! Pick that out of the stands! Incredible power!",
                "What a shot! That ball has been sent into orbit!",
            ],
            "wicket_bowled": [
                "BOWLED! What a peach of a delivery! Timber!",
                "BOWLED HIM! The stumps are shattered!",
                "Through the gate! That's a beautiful delivery!",
                "BOWLED! The batsman had no clue about that one!",
                "Cleaned up! What a ball to get the breakthrough!",
            ],
            "wicket_caught": [
                "CAUGHT! What a brilliant catch! Gone!",
                "TAKEN! Excellent work in the field!",
                "CAUGHT! The fielder makes no mistake!",
                "What a catch! Pouched safely!",
                "CAUGHT! Straight to the fielder! Well taken!",
            ],
            "wicket_lbw": [
                "LBW! That looked plumb! Up goes the finger!",
                "OUT! Hit in line, that's hitting the stumps!",
                "LBW! No doubt about that one! Dead in front!",
                "Trapped LBW! That was hitting middle stump!",
                "OUT! The umpire has no hesitation! LBW!",
            ],
            "wicket_run_out": [
                "RUN OUT! Direct hit! What brilliant fielding!",
                "OUT! Mix-up in the middle! Run out by yards!",
                "RUN OUT! The throw is spot on! Gone!",
                "Brilliant fielding! Direct hit and he's well short!",
                "RUN OUT! Communication breakdown costs a wicket!",
            ],
            "dot_ball": [
                "Dot ball. Good bowling, tight line and length.",
                "Well bowled! No runs off that delivery.",
                "Solid defense from the batsman.",
                "Good ball, well left by the batsman.",
                "Tidy bowling, no runs conceded.",
            ],
            "single": [
                "Quick single taken! Good running between the wickets!",
                "Just a single. Keeps the scoreboard ticking.",
                "One run. Smart cricket from the batsman.",
                "Single taken with ease. Good placement.",
                "Just the one. Nudged for a single.",
            ],
            "double": [
                "Two runs! Good running! They come back for the second!",
                "Couple of runs. Excellent running between the wickets!",
                "Two more added to the total. Good placement!",
                "They scamper back for two! Alert running!",
                "Two runs. The batsmen are quick between the wickets!",
            ],
            "wide": [
                "WIDE! That's down the leg side. Extra run!",
                "Wide called! Poor line from the bowler.",
                "That's a wide! Wayward delivery.",
                "Wide ball! The bowler loses his line.",
                "Called wide! That's outside the tramlines.",
            ],
            "no_ball": [
                "NO BALL! Free hit coming up!",
                "No ball called! The bowler has overstepped!",
                "That's a no ball! Front foot over the line!",
                "NO BALL! Free runs and a free hit to follow!",
                "No ball! The bowler needs to watch his front foot!",
            ],
        }

        self.milestone_templates = {
            "fifty": [
                "FIFTY! What a fantastic innings! The crowd is on its feet!",
                "Half-century! Brilliant batting display!",
                "FIFTY UP! Well deserved milestone!",
                "That's his fifty! Superb knock!",
                "Fifty runs! The batsman raises his bat!",
            ],
            "century": [
                "CENTURY! What an absolutely brilliant hundred!",
                "HUNDRED! The crowd erupts! What an innings!",
                "CENTURY! Masterful batting! Standing ovation!",
                "That's his hundred! Magnificent innings!",
                "CENTURY! Pure class from start to finish!",
            ],
        }

        self.pressure_comments = {
            "high_pressure": [
                "The pressure is mounting here!",
                "Tension in the air! Every run counts now!",
                "This is nail-biting stuff!",
                "The match is in the balance!",
                "Heart-stopping cricket!",
            ],
            "death_overs": [
                "We're into the death overs now!",
                "Crunch time! Every ball is crucial!",
                "The business end of the innings!",
                "This is where matches are won and lost!",
                "Pressure cooker situation!",
            ],
        }

    def generate_ball_commentary(
        self,
        ball: CricketBall,
        match_context: Dict,
        player_stats: Optional[Dict] = None,
    ) -> str:
        """Generate commentary for a specific ball"""

        runs = getattr(ball, "runs_scored", 0)
        extras = getattr(ball, "extras", 0)
        is_wicket = getattr(ball, "is_wicket", False)
        is_boundary = getattr(ball, "is_boundary", False)
        ball_type = getattr(ball, "ball_type", "legal")
        wicket_type = getattr(ball, "wicket_type", "")

        # Handle extras first
        if ball_type == "wide":
            return random.choice(self.commentary_templates["wide"])
        elif ball_type == "no_ball":
            return random.choice(self.commentary_templates["no_ball"])

        # Handle wickets
        if is_wicket:
            wicket_key = f"wicket_{wicket_type}" if wicket_type else "wicket_caught"
            if wicket_key in self.commentary_templates:
                base_comment = random.choice(self.commentary_templates[wicket_key])
                return self._add_context(base_comment, match_context)

        # Handle boundaries
        if is_boundary:
            if runs == 6:
                base_comment = random.choice(self.commentary_templates["six"])
            else:
                base_comment = random.choice(self.commentary_templates["four"])
            return self._add_context(base_comment, match_context)

        # Handle regular scoring
        if runs == 0:
            return random.choice(self.commentary_templates["dot_ball"])
        elif runs == 1:
            return random.choice(self.commentary_templates["single"])
        elif runs == 2:
            return random.choice(self.commentary_templates["double"])
        elif runs == 3:
            return "Three runs! Excellent placement and good running!"
        else:
            return f"{runs} runs! What a shot!"

    def generate_milestone_commentary(self, runs: int, milestone_type: str) -> str:
        """Generate commentary for batting milestones"""
        if milestone_type in self.milestone_templates:
            return random.choice(self.milestone_templates[milestone_type])
        return f"Milestone reached! {runs} runs!"

    def generate_match_situation_commentary(self, match_context: Dict) -> str:
        """Generate situational commentary based on match state"""
        required_rate = match_context.get("required_run_rate", 0)
        current_rate = match_context.get("current_run_rate", 0)
        overs_remaining = match_context.get("overs_remaining", 0)
        wickets_remaining = match_context.get("wickets_remaining", 10)

        if overs_remaining <= 3:
            return random.choice(self.pressure_comments["death_overs"])
        elif required_rate > current_rate + 2:
            return random.choice(self.pressure_comments["high_pressure"])
        elif wickets_remaining <= 3:
            return "Running out of wickets! The lower order needs to step up!"

        # Default situational comments
        comments = [
            f"Required rate: {required_rate:.1f}, Current rate: {current_rate:.1f}",
            f"{overs_remaining} overs remaining in the innings",
            f"{wickets_remaining} wickets in hand",
            "The game is nicely poised here!",
        ]
        return random.choice(comments)

    def _add_context(self, base_comment: str, match_context: Dict) -> str:
        """Add contextual information to commentary"""
        current_score = match_context.get("current_score", 0)
        current_wickets = match_context.get("current_wickets", 0)

        # Sometimes add score context
        if random.random() < 0.3:  # 30% chance to add context
            return f"{base_comment} Score: {current_score}/{current_wickets}"

        return base_comment

    def generate_over_summary(
        self, over_balls: List[CricketBall], over_runs: int
    ) -> str:
        """Generate end-of-over summary"""
        over_number = getattr(over_balls[0], "over_number", 1) if over_balls else 1

        wickets_in_over = sum(
            1 for ball in over_balls if getattr(ball, "is_wicket", False)
        )
        boundaries_in_over = sum(
            1 for ball in over_balls if getattr(ball, "is_boundary", False)
        )

        summary = f"End of over {over_number}: {over_runs} runs"

        if wickets_in_over > 0:
            summary += f", {wickets_in_over} wicket{'s' if wickets_in_over > 1 else ''}"

        if boundaries_in_over > 0:
            summary += f", {boundaries_in_over} boundar{'ies' if boundaries_in_over > 1 else 'y'}"

        if over_runs == 0:
            summary += " - A maiden over!"
        elif over_runs >= 15:
            summary += " - Expensive over for the bowler!"

        return summary


# Global commentary generator instance
commentary_generator = CricketCommentaryGenerator()
