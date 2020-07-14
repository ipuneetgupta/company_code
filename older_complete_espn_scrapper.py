from match.models import Match,Match_Detail,MatchPlayer
from scorecard.models import ScoreCard,FallOfWicket
from match_inning.models import MatchBatsmanInning,MatchBowlersInning
from team.models import Team
import requests
from player.models import Player
from league.models import League,Series
from espn.models import ESPNMatch,ESPNMatchFail
from umpire.models import Umpire
import os
from win11.global_variable import BASE_LOG
from commentary.models import MatchCommentary
import random
from venue.models import Venue
from django.core.exceptions import ObjectDoesNotExist
from win11.settings import BASE_DIR
from countries.models import Countries
from continent.models import Continent
from helper.logs import save_success_log,save_error_log
import json
import time

def team_save(data):
    try:
        if data.get('team_id',None) != None:
            if len(Team.objects.filter(team_id=data['team_id'])) == 1 and data['team_id'] != None:
                return Team.objects.get(team_id=data['team_id'])
        return Team.objects.get(name=data['name'])
    except ObjectDoesNotExist:
        t = Team(**data)
        t.save()
        return t

def player_save(data):
    try:
        if data.get('espn_object_id',None) != None:
            if len(Player.objects.filter(espn_object_id=data['espn_object_id'])) == 1 and data['espn_object_id'] != None:
                return Player.objects.get(espn_object_id=data['espn_object_id'])
        return Player.objects.get(name=data['name'])
    except ObjectDoesNotExist:
        t = Player(**data)
        t.save()
        return t

def league_save(data):
    try:
        return League.objects.get(name=data['name'])
    except ObjectDoesNotExist:
        l = League(**data)
        l.save()
        return l

def series_save(data):
    try:
        return Series.objects.get(name=data['name'])
    except ObjectDoesNotExist:
        s = Series(**data)
        s.save()
        return s

def venue_save(data):
    try:
        return Venue.objects.get(name=data['name'])
    except ObjectDoesNotExist:
        v = Venue(**data)
        v.save()
        return v

def country_save(data):
    try:
        return Countries.objects.get(name=data['name'])
    except ObjectDoesNotExist:
        c = Countries(**data)
        c.save()
        return c

def continent_save(data):
    try:
        return Continent.objects.get(name=data['name'])
    except ObjectDoesNotExist:
        c = Continent(**data)
        c.save()
        return c

def match_save(data):
    # try:
    #     return Match.objects.get(description=data['description'])
    # except ObjectDoesNotExist:
    m = Match(**data)
    m.save()
    return m

def umpire_save(data):
    try:
        return Umpire.objects.get(name=data['name'])
    except ObjectDoesNotExist:
        u = Umpire(**data)
        u.save()
        return u

def match_player_save(data):
    try:
        if data.get('team',None) != None and data.get('match',None) != None:
            return MatchPlayer.objects.get(team=data['team'],match=data['match'])
        else:
            m_p = MatchPlayer(**data)
            m_p.save()
            return m_p
    except ObjectDoesNotExist:
        m_p = MatchPlayer(**data)
        m_p.save()
        return m_p

def scorecard_match_save(scorecard,match):
    for x in scorecard:
        match.scorecard.add(x)
    return match

def player_scorecard(data):

    try:
        if data['espn_object_id'] != None:
            data['espn_object_id'] = int(data['espn_object_id'])
        else:
            pass
    except:
        data['espn_object_id'] = None

    if data['espn_object_id'] != None and len(Player.objects.filter(espn_object_id=data['espn_object_id'])) == 1:
        return Player.objects.get(espn_object_id=data['espn_object_id'])
    elif len(Player.objects.filter(fullname=data['name'])) == 1:
        return Player.objects.get(fullname=data['name'])
    elif len(Player.objects.filter(card_name=data['name'])) == 1:
        return Player.objects.get(card_name=data['name'])
    elif len(Player.objects.filter(nickname=data['name'])) == 1:
        return Player.objects.get(nickname=data['name'])
    elif len(Player.objects.filter(name=data['name'])) == 1:
        return Player.objects.get(name=data['name'])
    else:
        p = Player(**data)
        p.save()
        return p

def fall_of_wicket_scorecard(data):
    if len(Player.objects.filter(fullname=data['name'])) == 1:
        return Player.objects.get(fullname=data['name'])
    elif len(Player.objects.filter(card_name=data['name'])) == 1:
        return Player.objects.get(card_name=data['name'])
    elif len(Player.objects.filter(nickname=data['name'])) == 1:
        return Player.objects.get(nickname=data['name'])
    elif len(Player.objects.filter(name=data['name'])) == 1:
        return Player.objects.get(name=data['name'])
    else:
        return None

def fall_wicket_del():
    f = FallOfWicket.objects.all()
    return f.delete()

def delete():
    l = [ Team.objects.all(),ScoreCard.objects.all(),MatchBowlersInning.objects.all(),
          MatchBatsmanInning.objects.all(),Match.objects.all(),Venue.objects.all(),Umpire.objects.all(),
          Match_Detail.objects.all(),League.objects.all(),Series.objects.all(),Player.objects.all(),Team.objects.all(),
          League.objects.all(),Series.objects.all()
          ]
    for x in l:
        x.delete()

def jsonscrapper():

    all_match = ESPNMatch.objects.filter(local_id=0)
    # print(len(all_match)-len(Match.objects.all()),"-->left match for scrap!!")

    for m in all_match:
        # start = time.time()
        #scorecard json file
        p = os.path.join(BASE_DIR,"media/"+str(m.scorecard_json))
        try:
            with open(p) as f:
                data = json.load(f)
        except:
            continue
        #end

        # json file
        json_data = {}
        try:
            url = "https://www.espncricinfo.com/matches/engine/match/{}.json".format(m.match_id)
            json_data = requests.get(url).json()
        except:
            pass
        # end
        # print("*"*100)

        m.local_id = random.randint(a=1,b=600000)

        header = data.get('header', {})
        content = data.get('content',{})
        about = content.get('about',{})
        team = header.get('matchEvent',{}).get('competitors',[])
        match_player1 = content.get('teams',[])
        innings_score = content.get('innings',[])
        series_json = json_data.get('series',[{}])[0]
        match_json = json_data.get('match',{})
        team_json = json_data.get('team',[])
        innings_json = json_data.get('innings',[])
        over_limit = None
        matchtype = None
        #continent
        contient_detail = {
            'name':match_json.get('continent_name',"")
        }
        con = continent_save(contient_detail)
        # print(contient_detail)
        #end

        #country
        country_detail = {
            'name':match_json.get('country_name',""),
            'continent':con
        }
        cou = country_save(country_detail)
        # print(country_detail)
        #end

        # league
        league_detail = {
            'name': m.league_name,
            'country':cou
        }
        l = league_save(league_detail)
        # print(league_detail)
        # end league

        #sereis
        series_detail = {
            'name' : about.get('series',{}).get('text',""),
            'description': json_data.get('description', ""),
            'start_date':series_json.get('start_date_raw',None),
            'end_date': series_json.get('end_date_raw',None),
            'status':series_json.get('series_status',None),
            'league': l
        }
        s = series_save(series_detail)
        # print(series_detail)
        #end series

        #venue
        venue_detail = {
            'name':about.get('venue',{}).get('text',"").split(',')[0],
            'espn_object_id' : about.get('venue', {}).get('href', '').split('/')[-1].split('.')[0]

        }
        v = venue_save(venue_detail)
        # print(venue_detail)
        # endVenue

        #umpire
        u_r , u_r_u , u_t , u_1 , u_2 = None,None,None,None,None
        umpire_ = about.get('umpire',[])
        refree_ = about.get('referee',[])
        reserve_umpire_ = about.get('reserver umpire',[])
        tv_umpire_ = about.get('tv umpire',[])

        for u in refree_:
            umpire_detail = {
                'name': u.get('text',''),
                'type': 'referee'
            }
            u_r = umpire_save(umpire_detail)
            l.umpires.add(u_r)

        for u in reserve_umpire_:
            umpire_detail = {
                'name': u.get('text',''),
                'type': 'reserve umpire'
            }
            u_r_u = umpire_save(umpire_detail)
            l.umpires.add(u_r_u)

        for u in tv_umpire_:
            umpire_detail = {
                'name': u.get('text',''),
                'type': 'tv umpire'
            }
            u_t = umpire_save(umpire_detail)
            l.umpires.add(u_t)

        temp_umpire_list = []
        for u in umpire_:
            umpire_detail = {
                'name': u.get('text',''),
                'type': 'umpire'
            }
            u_ = umpire_save(umpire_detail)
            l.umpires.add(u_)
            temp_umpire_list.append(u_)
        l.save()

        if len(temp_umpire_list)>=2:
            u_1 = temp_umpire_list[0]
            u_2 = temp_umpire_list[1]
        elif len(temp_umpire_list)==1:
            u_1 = temp_umpire_list[0]
            u_2 = None
        #endumpire

        # team and player
        for x in team_json:
            team_detail = {
                'team_id': x.get('team_id',None),
                'name': x.get('team_name',""),
                'abbrevation':x.get('team_abbreviation',""),
                'description':x.get('team_general_name',"") #doubt
            }
            t_json = team_save(team_detail)
            # print(team_detail)
            for y in x.get('player',[]):
                player_detail = {
                    'espn_object_id':y.get('object_id',None),
                    'name':y.get('alpha_name',''),
                    'fullname':y.get('known_as',''),
                    'nickname':y.get('popular_name',''),
                    'card_name':y.get('card_name',''),
                    'age':y.get('age_years',''),
                    'birth_place':None,#doubt
                    'playing_role':y.get('player_primary_role',''),
                    'status':'working',#doubt always working ??
                    'date_of_birth': y.get('dob','')
                }
                p_json = player_save(player_detail)
                t_json.players.add(p_json)
                t_json.save()
                # print(player_detail)
        # end

        # matchdetail
        winner_team = None
        for x in team :
            if x.get('isWinner',False) == True :
                winner_team_name = x.get('name',None)
                if len(Team.objects.filter(name=winner_team_name)) == 1:
                    winner_team = Team.objects.get(name=winner_team_name)
                break

        tossWin_team = None
        toss_win_team_name = str(about.get('toss','').split(',')[0]).strip()
        if len(Team.objects.filter(name=toss_win_team_name)) == 1:
            tossWin_team = Team.objects.get(name=toss_win_team_name)
        # end

        #scorecard
        scorecard_list = []
        for x,y in zip(innings_score,innings_json):

            scorecard_detail = {
            'title':x.get('title',None),
            'wickets':y.get('wickets',None),
            'no_ball':y.get('noballs',None),
            'wide':y.get('wides',None),
            'runs':y.get('runs',None),
            'required_run_rate':None, #doubt
            'run_rate':y.get('run_rate',None),
            'over':y.get('overs',None),
            'is_declared':x.get('isCurrent',False),
            'leg_bye':y.get('legbyes',None),
            'bye':y.get('byes',None),
            'extra':y.get('extras',None),
            }
            over_limit = y.get('over_limit', None)
            if over_limit:
                try:
                    over_limit = over_limit
                except:
                    over_limit = 0.0
                if over_limit == '20.0':
                    matchtype = 't20'
                elif over_limit == '50.0':
                    matchtype = 'odi'
                else:
                    matchtype = 'other'

            batting_team_id = y.get('batting_team_id',None)
            bowling_team_id = y.get('bowling_team_id', None)

            if len(Team.objects.filter(team_id=batting_team_id)) == 1:
                scorecard_detail['team1'] = Team.objects.get(team_id = batting_team_id)

            if len(Team.objects.filter(team_id=bowling_team_id)) == 1:
                scorecard_detail['team2'] = Team.objects.get(team_id = bowling_team_id)

            # print(scorecard_detail)
            scorecard = ScoreCard(**scorecard_detail)
            scorecard.save()

            f_o_w = x.get('fallOfWickets', [])
            for f_order,f_o in enumerate(f_o_w):
                fall_of_wicket_detail = {
                    'fall_of_wicket': f_o
                }
                scorecard.fall_of_wicket.create(**fall_of_wicket_detail)

            batsmen = x.get('batsmen',[])
            bowlers = x.get('bowlers',[])

            for i,b in enumerate(batsmen):
                batsmen_detail = {
                'player': player_scorecard({'espn_object_id':b.get('href','').split('/')[-1].split('.')[0],'name':b.get('name','')}),
                'order': i,
                'runs': b.get('runs',0),
                'balls':b.get('ballsFaced',0),
                'strike_rate':b.get('strikeRate',0),
                'fours':b.get('fours',0),
                'sixes':b.get('sixes',0),
                'how_out':b.get('shortText',0),
                'fall_of_wicket_over':b.get('runningOver',0),
                'fall_of_wicket':None #doubt
                }
                scorecard.match_batting_inning.create(**batsmen_detail)
                # print(batsmen_detail)
                # break

            for i, b in enumerate(bowlers):
                bowlers_detail = {
                'player': player_scorecard({'espn_object_id':b.get('href','').split('/')[-1].split('.')[0],'name':b.get('name','')}),
                'order':i,
                'run_conceded':b.get('conceded',0),
                'maidens':b.get('maidens',0),
                'wickets':b.get('wickets',0),
                'overs':b.get('overs',0),
                'economy':b.get('economyRate',0),
                'wides':b.get('wides',0),
                'no_balls':b.get('noballs',0),
                'zeros':None,#doubt
                'sixes':None,#doubt
                'fours':None,#doubt
                }
                scorecard.match_bowling_inning.create(**bowlers_detail)
                # print(bowlers_detail)
                # break
            # scorecard.save()
            scorecard_list.append(scorecard)
            # break
        #endscorcard

        match_detail_={
            'is_abandoned':None,#doubt
            'toss_decision':about.get('toss',''),
            'summary': header.get('matchEvent',{}).get('statusText',''),
            'winner' : winner_team,
            'toss_winner':tossWin_team
        }

        if match_detail_['summary'].strip() == "Match drawn":
            match_detail_['is_drawn'] = True
        else:
            match_detail_['is_drawn'] = False

        m_d = Match_Detail(**match_detail_)
        m_d.save()
        # print(match_detail_)
        #end

        #match
        match_detail = {
            'espn_id':m.match_id,
            'name':header.get('matchEvent',{}).get('name',''),
            'start_date':match_json.get('start_date_raw',None),
            'end_date':match_json.get('end_date_raw',None),
            'status': match_json.get('match_status',''),
            'description':header.get('matchEvent',{}).get('description',''),
            'over_limit':over_limit,
            'matchtype':matchtype,
            'refree':u_r,
            'umpire1':u_1,
            'umpire2': u_2,
            'tvumpire':u_t,
            'series':s,
            'team1': team_save({'name':match_json.get('team1_name')}),
            'team2': team_save({'name':match_json.get('team2_name')}),
            'match_detail':m_d,
            'venue':v
        }
        m_match = match_save(match_detail)
        # print(match_detail)
        scorecard_match_save(scorecard_list,m_match)

        #match_player
        for x in match_player1:
            match_player_detail = {}
            match_player_detail['match'] = m_match
            t_name = ''
            for z in x.get('title', '').split(" "):
                if z != 'Team':
                    t_name += z + ' '
            t_name = t_name.strip()
            if len(Team.objects.filter(name=t_name)) == 1:
                match_player_detail['team'] = Team.objects.get(name=t_name)
            # print(match_player_detail)
            m_p = match_player_save(match_player_detail)
            for y in x.get('players', []):
                player_detail = {
                    "espn_object_id" : y.get('href','').split('/')[-1].split('.')[0],
                    'name': y.get('name', ''),
                }
                if player_scorecard(player_detail) != None:
                    m_p.players.add(player_scorecard(player_detail))
            # print(m_p)
        #end
        m.save()
        save_success_log(
            BASE_LOG + 'json_data/scraper.txt',
            "Json Data from this Match_id  " + str(m.match_id) + " Saved in models"
        )
        # print(match_detail)

        # end = time.time()
        # print("Time Taken To Scrap this match --> ",end-start)
        # print("*"*100)
        #endmatch

        # break


