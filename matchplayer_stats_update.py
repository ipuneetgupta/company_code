from cds_match.models import Match,MatchPlayer
from cds_playerstats.models import PlayerBattingStats,PlayerBowlingStats
from cds_teamstats.models import TeamStats,Series_TeamStats,YearTeamStats
from tqdm import tqdm
from cds_player.models import Player

def update_match_players_stat():
    all_match = Match.objects.all()
    for m in tqdm(all_match):
        m_p = MatchPlayer.objects.filter(match=m)
        for x in m_p:
            if x.players != None:
                players_batting_stats = PlayerBattingStats.objects.filter(player__in=list(x.players.all()),league=m.series.league)
                players_bowling_stats = PlayerBowlingStats.objects.filter(player__in=list(x.players.all()),league=m.series.league)
                players_batting_stats = sorted(players_batting_stats,key=lambda x : x.average,reverse=True)
                players_batting_stats1 = sorted(players_batting_stats,key=lambda x : x.highest_run,reverse=True)
                players_bowling_stats = sorted(players_bowling_stats,key=lambda x : x.economy,reverse=True)
                x.individual_top_score = players_batting_stats1[0] if len(players_batting_stats1) !=0 else None
                x.best_bowling_economy = players_bowling_stats[0] if len(players_bowling_stats) !=0 else None
                x.best_batting_average = players_batting_stats[0] if len(players_batting_stats) !=0 else None
                for p in players_batting_stats: x.top_batsmen.add(p)
                for p in players_bowling_stats: x.top_bowler.add(p)
                x.save()