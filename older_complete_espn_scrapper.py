from cds_match.models import Match,Match_Detail,MatchPlayer
from cds_scorecard.models import ScoreCard
from cds_match_inning.models import MatchBatsmanInning,MatchBowlersInning
from cds_team.models import Team
from team.models import ESPNTeam
from espn.models import ESPNTeamMatches
import requests
from cds_player.models import Player
from player.models import ESPNPlayer
from series.models import ESPNSeries
from tqdm import tqdm
from cds_league.models import League
from cds_series.models import Series
from cds_umpire.models import Umpire
from cds_venue.models import Venue
from venue.models import ESPNVenue
from django.core.exceptions import ObjectDoesNotExist
from cds_countries.models import Countries
from cds_continent.models import Continent

def team_save(data):
    if data.get('espn_id',None) != None:
        t_espn = ESPNTeam.objects.filter(espn_id=data['espn_id'])
        if len(t_espn) == 1:
            return t_espn[0].team_id
        else:
            t_id = data.get('espn_id', None)
            if t_id != None or t_id != "":
                del data['espn_id']
                t = Team(**data)
                t.save()
                ESPNTeam(team_id=t, espn_id=t_id,active=False).save()
                return t


def player_save(data):
    if data.get('espn_object_id',None) != None:
        p_espn = ESPNPlayer.objects.filter(espn_object_id=data['espn_object_id'])
        if len(p_espn) == 1:
            return p_espn[0].player_id
        else:
            p_id = data.get('espn_object_id', None)
            if p_id != None or p_id != "":
                del data['espn_object_id']
                try:
                    p = Player(**data,active=False)
                    p.save()
                except:
                    del data['date_of_birth']
                    p = Player(**data, active=False)
                    p.save()
                ESPNPlayer(player_id=p, espn_object_id=p_id).save()
                return p


def series_save(data):
    if data.get('espn_object_id', None) != None:
        s_espn = ESPNSeries.objects.filter(espn_object_id=data['espn_object_id'])
        if len(s_espn) == 1:
            return s_espn[0].series_id
        else:
            s_id = data.get('espn_object_id', None)
            if s_id != None or s_id != "":
                del data['espn_object_id']
                s = Series(**data)
                s.save()
                ESPNSeries(series_id=s,espn_object_id=s_id).save()
                return s

def venue_save(data):
    if data.get('espn_object_id', None) != None:
        v_espn = ESPNVenue.objects.filter(espn_id=data['espn_object_id'])
        if len(v_espn) == 1 :
            return v_espn[0].venue_id

def country_save(data):
    try:
        return Countries.objects.get(name=data['name'])
    except ObjectDoesNotExist:
        return None

def continent_save(data):
    try:
        return Continent.objects.get(name=data['name'])
    except ObjectDoesNotExist:
       return None

def match_save(data):
    m = Match(**data)
    m.save()
    return m

def umpire_save(data):
    try:
        return Umpire.objects.get(name=data['name'])
    except ObjectDoesNotExist:
        u = Umpire(**data,active=False)
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

def player_scorecard(data):

    try:
        if data['espn_object_id'] != None:
            data['espn_object_id'] = int(data['espn_object_id'])
        else:
            pass
    except:
        data['espn_object_id'] = None

    p_espn = ESPNPlayer.objects.filter(espn_object_id=data['espn_object_id'])
    if len(p_espn) == 1 and data['espn_object_id'] != None:
        return p_espn[0].player_id
    elif len(Player.objects.filter(fullname=data['name'])) == 1:
        return Player.objects.get(fullname=data['name'])
    elif len(Player.objects.filter(card_name=data['name'])) == 1:
        return Player.objects.get(card_name=data['name'])
    elif len(Player.objects.filter(nickname=data['name'])) == 1:
        return Player.objects.get(nickname=data['name'])
    elif len(Player.objects.filter(name=data['name'])) == 1:
        return Player.objects.get(name=data['name'])
    else:
        return None

def delete():
    l = [ ScoreCard.objects.all(),MatchBowlersInning.objects.all(),
          MatchBatsmanInning.objects.all(),Match.objects.all(),
          Match_Detail.objects.all(),League.objects.all(),Series.objects.all()
          ]
    for x in l:
        x.delete()


def jsonscrapper():
    all_match = ESPNTeamMatches.objects.filter(local_id=-1)
    for a_m in tqdm(all_match):
        match_id = a_m.match_espn_object_id

        # json file
        json_data = {}
        try:
            url = "https://www.espncricinfo.com/matches/engine/match/{}.json".format(match_id)
            json_data = requests.get(url).json()
        except:
            pass
        # end
        series_json = json_data.get('series', [{}])[0]
        match_json = json_data.get('match', {})
        team_json = json_data.get('team', [])
        innings_json = json_data.get('innings',[])

        series_id = series_json.get('object_id', None)

        #scorecard json file
        scorecard_json = {}
        try:
            url =  "https://hsapi.espncricinfo.com/v1/pages/match/scoreboard?lang=en&leagueId={}&eventId={}".format(series_id, match_id)
            scorecard_json = requests.get(url).json()
        except:
            pass
        data = scorecard_json
        #end

        header = data.get('header', {})
        content = data.get('content',{})
        about = content.get('about',{})
        match_player1 = content.get('teams',[])
        innings_score = content.get('innings',[])
        team = header.get('matchEvent',{}).get('competitors',[])
        over_limit = None
        matchtype = None

        #continent
        contient_detail = {
            'name':match_json.get('continent_name',"")
        }
        con = continent_save(contient_detail)
        #end

        #country
        country_detail = {
            'name':match_json.get('country_name',""),
            'continent':con
        }
        cou = country_save(country_detail)
        #end

        series_detail = {
            'espn_object_id':series_json.get('object_id', None),
            'name': series_json.get('series_name', ""),
            'description': json_data.get('description', ""),
            'start_date': series_json.get('start_date_raw', None),
            'end_date': series_json.get('end_date_raw', None),
            'status': series_json.get('series_status', None),
            'league':a_m.league,
        }
        s = series_save(series_detail)

        #venue
        v_detail = about.get('venue',{}).get('text',"").split(','),
        venue_detail = {}
        venue_detail['name'] =  v_detail[0][0]
        if len(v_detail[0]) == 2: venue_detail['location'] = v_detail[0][1]
        venue_detail['espn_object_id'] = match_json.get('ground_object_id', None)
        v = venue_save(venue_detail)
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
            if u_r: a_m.league.umpires.add(u_r)

        for u in reserve_umpire_:
            umpire_detail = {
                'name': u.get('text',''),
                'type': 'reserve cds_umpire'
            }
            u_r_u = umpire_save(umpire_detail)
            if u_r_u: a_m.league.umpires.add(u_r_u)

        for u in tv_umpire_:
            umpire_detail = {
                'name': u.get('text',''),
                'type': 'tv cds_umpire'
            }
            u_t = umpire_save(umpire_detail)
            if u_t: a_m.league.umpires.add(u_t)

        temp_umpire_list = []
        for u in umpire_:
            umpire_detail = {
                'name': u.get('text',''),
                'type': 'umpire'
            }
            u_ = umpire_save(umpire_detail)
            if u_: a_m.league.umpires.add(u_)
            temp_umpire_list.append(u_)

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
                'name': x.get('team_name',""),
                'abbrevation':x.get('team_abbreviation',""),
                'description':x.get('team_general_name',""), #doubt
                'espn_id': x.get('team_id',None)
            }
            t_json = team_save(team_detail)
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
                    'status':'working',
                    'date_of_birth': y.get('dob','')
                }
                p_json = player_save(player_detail)
                if p_json and t_json:
                    t_json.players.add(p_json)
                    t_json.save()
        # end

        # matchdetail
        winner_team = None
        for x in team:
            if x.get('isWinner', False) == True:
                winner_team_name = x.get('name', None)
                if len(Team.objects.filter(name=winner_team_name)) == 1:
                    winner_team = Team.objects.get(name=winner_team_name)
                break

        tossWin_team = None
        toss_win_team_name = str(about.get('toss', '').split(',')[0]).strip()
        if len(Team.objects.filter(name=toss_win_team_name)) == 1:
            tossWin_team = Team.objects.get(name=toss_win_team_name)
        # end

        #match
        for x,y in zip(innings_score,innings_json):
            over_limit = y.get('over_limit', None)
            if over_limit:
                try: over_limit = over_limit
                except: over_limit = 0.0
                if over_limit == '20.0': matchtype = 't20'
                elif over_limit == '50.0': matchtype = 'odi'
                else: matchtype = 'other'

            if over_limit != None or matchtype != None:
                break

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
        #end

        #match
        match_detail = {
            'match_number':series_json.get('match_number', None),
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
            'team1': team_save({'name':match_json.get('team1_name'),'espn_id':match_json.get('team1_id')}),
            'team2': team_save({'name':match_json.get('team2_name'),'espn_id':match_json.get('team2_id')}),
            'match_detail':m_d,
            'venue':v
        }
        m_match = match_save(match_detail)
        #end

        #scorecard
        cnt = 1
        for x,y in zip(innings_score,innings_json):

            scorecard_detail = {
            'inning':cnt,
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
            'match': m_match
            }

            cnt+=1

            batting_team_id = y.get('batting_team_id',None)
            bowling_team_id = y.get('bowling_team_id', None)

            if len(ESPNTeam.objects.filter(espn_id=batting_team_id)) == 1:
                scorecard_detail['team1'] = ESPNTeam.objects.get(espn_id=batting_team_id).team_id

            if len(ESPNTeam.objects.filter(espn_id=bowling_team_id)) == 1:
                scorecard_detail['team2'] = ESPNTeam.objects.get(espn_id=bowling_team_id).team_id

            # print(scorecard_detail)
            scorecard = ScoreCard(**scorecard_detail)
            scorecard.save()

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
                'fall_of_wicket':None,
                'scorecard':scorecard
                }
                match_bat_inning = MatchBatsmanInning(**batsmen_detail)
                match_bat_inning.save()


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
                'scorecard':scorecard
                }
                match_bow_inning = MatchBowlersInning(**bowlers_detail)
                match_bow_inning.save()
        #endscorcard


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
            m_p = match_player_save(match_player_detail)
            for y in x.get('players', []):
                player_detail = {
                    "espn_object_id" : y.get('href','').split('/')[-1].split('.')[0],
                    'name': y.get('name', ''),
                }
                if player_scorecard(player_detail) != None:
                    m_p.players.add(player_scorecard(player_detail))
        #end
        a_m.local_id = m_match.id
        a_m.save()
        # break
