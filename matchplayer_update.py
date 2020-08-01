from cds_scorecard.models import ScoreCard,MatchPlayer
from team.models import ESPNTeam
from espn.models import ESPNTeamMatches
import requests
from cds_player.models import Player
from player.models import ESPNPlayer
from tqdm import tqdm
from cds_scorecard.models import MatchPlayerDetail
from cds_match.models import Match

def team_save(data):
    if data.get('espn_id',None) != None:
        t_espn = ESPNTeam.objects.filter(espn_id=data['espn_id'])
        if len(t_espn) == 1:
            return t_espn[0].team_id

def player_save(data):
    if data.get('espn_object_id',None) != None:
        p_espn = ESPNPlayer.objects.filter(espn_object_id=data['espn_object_id'])
        if len(p_espn) == 1:
            p = p_espn[0].player_id
            return p

def match_player_save(data):
    if data.get('team',None) != None and data.get('match',None) != None:
        if ScoreCard.objects.filter(team=data['team'],match=data['match']).count() != 0:
            m = ScoreCard.objects.filter(team=data['team'],match=data['match'])[0]
            m_p = MatchPlayer(scorecard=m)
            m_p.save()
            return m_p
        else: return None
    else: return None

def player_scorecard(data):

    try:
        if data['espn_object_id'] != None:
            data['espn_object_id'] = int(data['espn_object_id'])
        else:pass
    except:
        data['espn_object_id'] = None
    p_espn = ESPNPlayer.objects.filter(espn_object_id=data['espn_object_id'])
    if p_espn.count() == 1 and data['espn_object_id'] != None:
        return p_espn[0].player_id
    elif Player.objects.filter(fullname=data['name']).count() == 1:
        return Player.objects.get(fullname=data['name'])
    elif Player.objects.filter(name=data['name']).count() == 1:
        return Player.objects.get(name=data['name'])
    else: return None


def jsonscrapper():
    all_match = ESPNTeamMatches.objects.all()
    for a_m in tqdm(all_match):
        match_id = a_m.match_espn_object_id

        # json file
        json_data = {}
        try:
            url = "https://www.espncricinfo.com/matches/engine/match/{}.json".format(match_id)
            json_data = requests.get(url).json()
        except:  pass
        # end
        series_json = json_data.get('series', [{}])[0]
        series_id = series_json.get('object_id', None)
        #scorecard json file
        scorecard_json = {}
        try:
            url =  "https://hsapi.espncricinfo.com/v1/pages/match/scoreboard?lang=en&leagueId={}&eventId={}".format(series_id, match_id)
            scorecard_json = requests.get(url).json()
        except: pass
        data = scorecard_json
        #end

        team_json = json_data.get('team', [])
        innings_json = json_data.get('innings', [])
        content = data.get('content',{})
        innings_score = content.get('innings',[])

        # team and player
        q1 = {}
        for x in team_json:
            team_detail = {
                'name': x.get('team_name',""),
                'espn_id': x.get('team_id',None)
            }
            t_json = team_save(team_detail)
            scorecard = ScoreCard.objects.filter(team=t_json,match__id=a_m.local_id)
            match_player = MatchPlayer.objects.filter(scorecard= scorecard[0] if scorecard.count() != 0 else None)
            for y in x.get('player',[]):
                player_detail = {
                    'espn_object_id':y.get('object_id',None),
                    'name':y.get('alpha_name'),
                    'fullname':y.get('known_as'),
                }
                player = player_save(player_detail)
                role = y.get('player_primary_role') if y.get('player_primary_role') else ''
                s_p = y.get('bowling_pacespin') if y.get('bowling_pacespin') else ''
                q1.setdefault(player,{
                    'isWicketKeeper': True if y.get('keeper') == '1' else False,
                    'isCaptain': True if y.get('captain') == '1' else False,
                    'isViceCaptain': False,
                    'bowler': 'spin' if s_p.find('spin') != -1 else ('pace' if s_p.find('pace') != -1 else 'none'),
                    'matchplayer':match_player[0] if match_player.count() == 1 else None,
                    'player':player,
                    'team':t_json,
                    'match':Match.objects.get(id=a_m.local_id)
                })
                q2 = {}
                if role.find('allrounder') != -1:
                    q2 = {
                        'allrounder': 'batting' if role.find('batting') != -1 else('bowling' if role.find('bowling') != -1 else 'none'),
                        'isAllrounder':True,
                        'isBatsmen':True,
                        'isBowler':True,
                    }
                elif role.find('batsman') != -1 or role.find('wicketkeeper') != -1:
                    q2 = {
                        'batsmen':'opening' if role.find('opening') != -1 else ('top-order' if role.find('top-order') != -1 else ('middle-order'
                                            if role.find('middle-order') != -1 else ('wicketkeeper' if role.find('wicketkeeper') != -1 else 'none'))),
                        'isAllrounder': False,
                        'isBatsmen': True,
                        'isBowler': False,
                    }
                elif role.find('bowler') != -1:
                    q2 = {
                        'isAllrounder': False,
                        'isBowler': True,
                        'isBatsmen': False,
                    }
                q1[player].update(q2)

        for x,y in zip(innings_score,innings_json):
            for i,b in enumerate(x.get('batsmen',[])):
                player =  player_scorecard({'espn_object_id':b.get('href','').split('/')[-1].split('.')[0],'name':b.get('name','')}),
                role = b.get('role') if b.get('role') else ''
                player = player[0]
                if role.find('&dagger;') != -1 and role.find('(c)')==-1:
                    if player in q1.keys(): q1[player]['isViceCaptain'] = True
                if role.find('(c)') !=-1:
                    if player in q1.keys(): q1[player]['isCaptain'] = True
            for i, b in enumerate(x.get('bowlers',[])):
                role = b.get('role') if b.get('role') else ''
                player = player_scorecard({'espn_object_id': b.get('href', '').split('/')[-1].split('.')[0], 'name': b.get('name', '')}),
                if role.find('&dagger;') != -1 and role.find('(c)') == -1:
                    if player in q1.keys(): q1[player]['isViceCaptain'] = True
                if role.find('(c)') != -1:
                    if player in q1.keys(): q1[player]['isCaptain'] = True
        for q in q1:
            if MatchPlayerDetail.objects.filter(matchplayer__scorecard__match__id=a_m.local_id,player=q).count() == 0: MatchPlayerDetail(**q1[q]).save()
