from cds_match.models import Match,MatchPlayer
from cds_scorecard.models import ScoreCard
from cds_series.models import Series
from cds_match_inning.models import MatchBatsmanInning,MatchBowlersInning
from cds_playerstats.models import PlayerBattingStats,PlayerBowlingStats,SeriesPlayerBowlingStats,SeriesPlayerBattingStats
from cds_player.models import Player
from django.db.models import Q
from cds_league.models import League
from tqdm import tqdm

def num(d):
    try:
        return int(d)
    except:
        return 0

def float_num(d):
    try:
        return float(d)
    except:
        return 0

def match_batting_inning_save(data):
    p_b = PlayerBattingStats.objects.filter(player=data['player'],league=data['league'])
    if len(p_b) != 0:
        p_b = p_b[0]
        p_b.__dict__.update(**data)
        p_b.save()
    else:
       p_b = PlayerBattingStats(**data)
       p_b.save()
       return p_b

def match_bowling_inning_save(data):
    p_b = PlayerBowlingStats.objects.filter(player=data['player'],league=data['league'])
    if len(p_b) != 0:
        p_b = p_b[0]
        p_b.__dict__.update(**data)
        p_b.save()
    else:
       p_b = PlayerBowlingStats(**data)
       p_b.save()
       return p_b

def series_match_batting_inning_save(data):
    p_b = SeriesPlayerBattingStats.objects.filter(player=data['player'],series=data['series'])
    if len(p_b) != 0:
        p_b = p_b[0]
        p_b.__dict__.update(**data)
        p_b.save()
    else:
       p_b = SeriesPlayerBattingStats(**data)
       p_b.save()
       return p_b

def series_match_bowling_inning_save(data):
    p_b = SeriesPlayerBowlingStats.objects.filter(player=data['player'],series=data['series'])
    if len(p_b) != 0:
        p_b = p_b[0]
        p_b.__dict__.update(**data)
        p_b.save()
    else:
       p_b = SeriesPlayerBowlingStats(**data)
       p_b.save()
       return p_b


def update_batting_stats():
    all_player = Player.objects.all()
    for p in tqdm(all_player):
        for l in League.objects.filter(name__in=['ICC ODI',"ICC T20",'ICC Test']):
            total_matches = MatchPlayer.objects.filter(players=p,match__series__league=l)
            matches_batting_inning = MatchBatsmanInning.objects.filter(player=p,scorecard__match__series__league=l).order_by('id')
            not_out_matches = matches_batting_inning.filter(fall_of_wicket_over="",how_out="not out")
            zero_out_matches = matches_batting_inning.filter((~Q(fall_of_wicket_over="")&(~(Q(how_out='not_out')))),runs=0)
            total_run,highest_run,no_of_sixes,no_of_fours,centuries,fifties,ball_faced = 0,0,0,0,0,0,0
            all_matches = Match.objects.filter(scorecard__matchbatsmaninning__player=p,series__league=l).order_by('start_date')
            first_match , last_match = None , None
            if len(all_matches) != 0:
                first_match = all_matches[0]
                last_match = list(all_matches)[-1]
            for m in matches_batting_inning:
                runs = num(m.runs)
                if runs >= 50 and runs < 100:
                    fifties += 1
                if runs >= 100 and runs < 200:
                    centuries += 1
                no_of_fours += num(m.fours)
                no_of_sixes += num(m.sixes)
                total_run += runs
                highest_run = max(highest_run,runs)
                ball_faced += num(m.balls)

            player_bat_stats_detail = {
                'matches' : len(total_matches),
                'average':round(total_run/(len(matches_batting_inning)-len(not_out_matches)),2) if (len(matches_batting_inning)-len(not_out_matches)) != 0 else 0,
                'strike_rate':round((total_run/ball_faced)*100,2) if ball_faced !=0 else 0,
                'innings': len(matches_batting_inning),
                'not_out': len(not_out_matches),
                'runs': total_run,
                'span': str(first_match.start_date.year) + " - " + str(last_match.start_date.year) if last_match != None and first_match != None else None,
                'zero_outs':len(zero_out_matches),
                'highest_run':highest_run,
                'style':p.playing_role,
                'centuries':centuries,
                'half_centuries':fifties,
                'fours':no_of_fours,
                'sixes':no_of_sixes,
                'balls_faced':ball_faced,
                'league':l,
                'player':p,
            }
            match_batting_inning_save(player_bat_stats_detail)

def update_bowling_stats():
    all_player = Player.objects.all()
    for p in tqdm(all_player):
        for l in League.objects.filter(name__in=['ICC ODI', "ICC T20", 'ICC Test']):
            total_matches = MatchPlayer.objects.filter(players=p, match__series__league=l)
            matches_bowling_inning = MatchBowlersInning.objects.filter(player=p,scorecard__match__series__league=l).order_by('id')
            all_matches = Match.objects.filter(scorecard__matchbatsmaninning__player=p, series__league=l).order_by('start_date')
            first_match, last_match = None, None
            if len(all_matches) != 0:
                first_match = all_matches[0]
                last_match = list(all_matches)[-1]

            average, strike_rate, wicket_5, wicket_4, maidens , wickets, overs , economy, runs, balls = 0, 0, 0, 0, 0, 0, 0,0,0,0

            for m in matches_bowling_inning:
                overs += float_num(m.overs)
                runs += num(m.run_conceded)
                wicket = num(m.wickets)
                wickets += wicket
                if num(m.maidens) == 1: maidens += 1
                if wicket >= 4 and wicket < 5: wicket_4 += 1
                if wicket >= 5 and wicket < 10: wicket_5 += 1
                balls +=  num(m.overs)*6+(float_num(m.overs)-num(m.overs))*10

            player_bowl_stats_detail = {
                'matches':len(total_matches),
                'innings':len(matches_bowling_inning),
                'span': str(first_match.start_date.year) + " - " + str(last_match.start_date.year) if last_match != None and first_match != None else None,
                'wicket_4':wicket_4,
                'wicket_5':wicket_5,
                'maidens':maidens,
                'overs':overs,
                'runs':runs,
                'wickets':wickets,
                'balls':num(balls),
                'average': round(runs/wickets,2) if wickets != 0 else 0,
                'economy':round(runs/overs,2) if overs != 0 else 0,
                'strike_rate':round(balls/wickets,2) if wickets != 0 else 0,
                'league': l,
                'player': p,
            }
            match_bowling_inning_save(player_bowl_stats_detail)

def update_batting_stats_series():
    all_player = Player.objects.all()
    for p in tqdm(all_player):
        for s in Series.objects.filter(match__scorecard__matchbatsmaninning__player=p):
            total_matches = MatchPlayer.objects.filter(players=p, match__series=s)
            if len(total_matches) != 0 and len(SeriesPlayerBattingStats.objects.filter(player=p,series=s)) == 0:
                matches_batting_inning = MatchBatsmanInning.objects.filter(player=p,scorecard__match__series=s).order_by('id')
                not_out_matches = matches_batting_inning.filter(fall_of_wicket_over="",how_out="not out")
                zero_out_matches = matches_batting_inning.filter((~Q(fall_of_wicket_over="")&(~(Q(how_out='not_out')))),runs=0)
                total_run,highest_run,no_of_sixes,no_of_fours,centuries,fifties,ball_faced = 0,0,0,0,0,0,0
                all_matches = Match.objects.filter(scorecard__matchbatsmaninning__player=p,series=s).order_by('start_date')
                first_match , last_match = None , None
                if len(all_matches) != 0:
                    first_match = all_matches[0]
                    last_match = list(all_matches)[-1]
                for m in matches_batting_inning:
                    runs = num(m.runs)
                    if runs >= 50 and runs < 100:
                        fifties += 1
                    if runs >= 100 and runs < 200:
                        centuries += 1
                    no_of_fours += num(m.fours)
                    no_of_sixes += num(m.sixes)
                    total_run += runs
                    highest_run = max(highest_run,runs)
                    ball_faced += num(m.balls)

                player_bat_stats_detail = {
                    'matches' : len(total_matches),
                    'average':round(total_run/(len(matches_batting_inning)-len(not_out_matches)),2) if (len(matches_batting_inning)-len(not_out_matches)) != 0 else 0,
                    'strike_rate':round((total_run/ball_faced)*100,2) if ball_faced !=0 else 0,
                    'innings': len(matches_batting_inning),
                    'not_out': len(not_out_matches),
                    'runs': total_run,
                    'span': str(first_match.start_date.year) + " - " + str(last_match.start_date.year) if last_match != None and first_match != None else None,
                    'zero_outs':len(zero_out_matches),
                    'highest_run':highest_run,
                    'style':p.playing_role,
                    'centuries':centuries,
                    'half_centuries':fifties,
                    'fours':no_of_fours,
                    'sixes':no_of_sixes,
                    'balls_faced':ball_faced,
                    'series':s,
                    'player':p,
                }
                series_match_batting_inning_save(player_bat_stats_detail)

def update_bowling_stats_series():
    all_player = Player.objects.all()
    for p in tqdm(all_player):
        for s in Series.objects.filter(match__scorecard__matchbowlersinning__player=p):
            total_matches = MatchPlayer.objects.filter(players=p, match__series=s)
            if len(total_matches) != 0 and len(SeriesPlayerBattingStats.objects.filter(player=p,series=s)) == 0:
                matches_bowling_inning = MatchBowlersInning.objects.filter(player=p,scorecard__match__series=s).order_by('id')
                all_matches = Match.objects.filter(scorecard__matchbatsmaninning__player=p, series=s).order_by('start_date')
                first_match, last_match = None, None
                if len(all_matches) != 0:
                    first_match = all_matches[0]
                    last_match = list(all_matches)[-1]

                average, strike_rate, wicket_5, wicket_4, maidens , wickets, overs , economy, runs, balls = 0, 0, 0, 0, 0, 0, 0,0,0,0

                for m in matches_bowling_inning:
                    overs += float_num(m.overs)
                    runs += num(m.run_conceded)
                    wicket = num(m.wickets)
                    wickets += wicket
                    if num(m.maidens) == 1: maidens += 1
                    if wicket >= 4 and wicket < 5: wicket_4 += 1
                    if wicket >= 5 and wicket < 10: wicket_5 += 1
                    balls +=  num(m.overs)*6+(float_num(m.overs)-num(m.overs))*10

                player_bowl_stats_detail = {
                    'matches':len(total_matches),
                    'innings':len(matches_bowling_inning),
                    'span': str(first_match.start_date.year) + " - " + str(last_match.start_date.year) if last_match != None and first_match != None else None,
                    'wicket_4':wicket_4,
                    'wicket_5':wicket_5,
                    'maidens':maidens,
                    'overs':overs,
                    'runs':runs,
                    'wickets':wickets,
                    'balls':num(balls),
                    'average': round(runs/wickets,2) if wickets != 0 else 0,
                    'economy':round(runs/overs,2) if overs != 0 else 0,
                    'strike_rate':round(balls/wickets,2) if wickets != 0 else 0,
                    'series': s,
                    'player': p,
                }
                series_match_bowling_inning_save(player_bowl_stats_detail)