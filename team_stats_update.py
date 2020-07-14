from cds_match.models import Match
from cds_scorecard.models import ScoreCard
from cds_playerstats.models import PlayerBattingStats,PlayerBowlingStats
from cds_team.models import Team
from cds_teamstats.models import TeamStats,Series_TeamStats
from tqdm import tqdm
from cds_league.models import League
from cds_series.models import Series


def team_save(data):
    t = TeamStats.objects.filter(team=data['team'],league=data['league'])
    if len(t) != 0:
        t = t[0]
        t.__dict__.update(**data)
        t.save()
    else:
       t = TeamStats(**data)
       t.save()
       return t

def team_save_series(data):
    t = Series_TeamStats.objects.filter(team=data['team'], series=data['series'])
    if len(t) != 0:
        t = t[0]
        t.__dict__.update(**data)
        t.save()
    else:
        t = Series_TeamStats(**data)
        t.save()
        return t

def update():
    all_team = Team.objects.all()
    for a_t in tqdm(all_team):
        all_league = League.objects.filter(name__in=['ICC ODI',"ICC T20",'ICC Test'])
        for a_l in all_league:
            q1 = Match.objects.filter(team1=a_t,series__league=a_l)
            q2 = Match.objects.filter(team2=a_t,series__league=a_l)
            q = q1|q2
            all_match = q.distinct().order_by('start_date')
            if len(all_match) != 0:
                first_match = all_match[0]
                last_match = list(all_match)[-1]
                total_winner = all_match.filter(match_detail__winner=a_t)
                total_drawn = all_match.filter(match_detail__is_drawn=True)
                total_no_result = all_match.filter(match_detail__is_abandoned=True,match_detail__winner__isnull=True,match_detail__is_drawn=False)
                won_batting_first = total_winner.filter(scorecard__inning=1,scorecard__team1=a_t)
                won_fielding_first = total_winner.filter(scorecard__inning=1,scorecard__team2=a_t)
                total_lost = len(total_winner) - len(total_drawn) - len(total_no_result)
                scorecard = ScoreCard.objects.filter(match__series__league=a_l,team1=a_t)
                team_top_score = 0
                for s in scorecard:
                    team_top_score = max(team_top_score,s.runs)
                no_of_100 = 0
                for p in a_t.players.all():
                    p_s = PlayerBattingStats.objects.filter(player=p)
                    if len(p_s) == 1:
                        no_of_100 += p_s[0].centuries
                team_stats_detail = {
                    'total_matches':len(all_match),
                    'total_won':len(total_winner),
                    'total_lost':total_lost,
                    'tied':len(total_drawn),
                    'no_result':len(total_no_result),
                    'matches_won_batting_first':len(won_batting_first),
                    'matches_won_fielding_first':len(won_fielding_first),
                    'span': str(first_match.start_date.year) + " - " + str(last_match.start_date.year) if last_match != None and first_match != None else None,
                    'no_of_100':no_of_100,
                    'team_top_score':team_top_score,
                    'w_l_ratio':round(len(total_winner)/total_lost,2) if total_lost != 0 else 0,
                    'percentage_win': round((len(total_winner)/len(all_match)*100),2) if len(all_match) != 0 else 0 ,                   # 'percentage_lost': round(((len(total_lost)/len(all_match)*100),2) if len(all_match) != 0 else 0,
                    'percentage_lost': round((total_lost/len(all_match)*100),2) if len(all_match) != 0 else 0  ,                  # 'percentage_lost': round(((len(total_lost)/len(all_match)*100),2) if len(all_match) != 0 else 0,
                    'percentage_drawn': round((len(total_drawn)/len(all_match)*100),2) if len(all_match) != 0 else 0,
                    'league':a_l,
                    'team':a_t,
                }
                team_save(team_stats_detail)
