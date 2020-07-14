from match.models import Match
import requests
from espn.models import ESPNMatch
import os
from player.models import Player
from win11.global_variable import BASE_LOG
from .models import MatchCommentary
from venue.models import Venue
from win11.settings import BASE_DIR
from helper.logs import save_success_log
import json

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

def switching_batsmen(per_bowl_data,batsmen,offstrike_batsmen):
    # handle offstrike and batsmen switching b/w over
    if (per_bowl_data['isWide'] == False and per_bowl_data['isNoball'] == False) \
            and (per_bowl_data['runs'] == 1 or per_bowl_data['runs'] == 3 or per_bowl_data['runs'] == 5):
        batsmen, offstrike_batsmen = offstrike_batsmen, batsmen
    elif per_bowl_data['isWide'] == True or per_bowl_data['isNoball'] == True:
        run_at_wasteBall = per_bowl_data['runs'] - 1
        if run_at_wasteBall == 1 or run_at_wasteBall == 3 or run_at_wasteBall == 5:
            batsmen, offstrike_batsmen = offstrike_batsmen, batsmen
    else:
        return None
    return batsmen,offstrike_batsmen
    # end


def get_batsmen_at_match_over(per_bowl_data):
    per_bowl_data_batsmen = per_bowl_data['matchOver'].get('batsmen', [])
    if len(per_bowl_data_batsmen) >= 2:
        batsmen_per_over = per_bowl_data_batsmen[0]
        offstrike_batsmen_per_over = per_bowl_data_batsmen[1]
        if batsmen_per_over:
            batsmen = player_scorecard({'espn_object_id': offstrike_batsmen_per_over.get('id', None),
                                        'name': offstrike_batsmen_per_over['name']})
        if offstrike_batsmen_per_over:
            offstrike_batsmen = player_scorecard(
                {'espn_object_id': batsmen_per_over.get('id', None), 'name': batsmen_per_over['name']})
        return batsmen , offstrike_batsmen
    return None , None


def commentary_model_update():

    all_match = ESPNMatch.objects.all()
    for m in all_match:
        # scorecard json file
        p = os.path.join(BASE_DIR, "media/" + str(m.commentary_json))
        try:
            with open(p) as f:
                commentary_data = json.load(f)
        except:
            continue
        # end
        if len(Match.objects.filter(espn_id=m.match_id)) == 1 and len(MatchCommentary.objects.filter(match__espn_id=m.match_id)) == 0:
            m_ = Match.objects.get(espn_id=m.match_id)

            #update overlimit or matchtype in match
            if len(m_.scorecard.all()) != 0:
                # json file
                json_data = {}
                try:
                    url = "https://www.espncricinfo.com/matches/engine/match/{}.json".format(m.match_id)
                    json_data = requests.get(url).json()
                except:
                    pass
                # end
                innings_json = json_data.get('innings', [])
                over_limit = None
                for inning in innings_json:
                    over_limit = inning.get('over_limit',None)
                if over_limit:
                    try:
                        m_.over_limit = over_limit
                    except:
                        m_.over_limit = 0.0

                    if over_limit == '20.0':
                        m_.matchtype = 't20'
                    elif over_limit == '50.0':
                        m_.matchtype = 'odi'
                    else:
                        m_.matchtype = 'other'
                m_.save()
                # print(m_.over_limit,m_.matchtype)
            #end

            #venue espn id update
            # scorecard json file
            p = os.path.join(BASE_DIR, "media/" + str(m.scorecard_json))
            try:
                with open(p) as f:
                    scorecard_data = json.load(f)
            except:
                pass
            # end
            content = scorecard_data.get('content', {})
            about = content.get('about', {})
            # venue_espn_object_id = about.get('venue',{}).get('href', '').split('/')[-1].split('.')[0]
            # if venue_espn_object_id != '':
            #     try:
            #         v_espn_object_id = int(venue_espn_object_id)
            #     except:
            #         v_espn_object_id = -1
            #
            #     venue_name = about.get('venue',{}).get('text',"").split(',')[0]
            #     venue = m_.venue
            #     if venue:
            #         venue.espn_object_id = v_espn_object_id
            #         venue.save()
            #     else:
            #         v_ = Venue()
            #         v_.name = venue_name
            #         v_.espn_object_id = v_espn_object_id
            #         venue.save()
            #         m_.venue = v_

            # print(m_.venue,m_.venue.espn_object_id)
            #end

            match_commentary = MatchCommentary()
            match_commentary.match = m_
            match_commentary.save()
            save_success_log(
                BASE_LOG + 'json_data/scraper.txt',
                "commentary Data from this Match_id  " + str(m.match_id) + " Saved in models"
            )
            for x in commentary_data.keys():
                inning_commentary = {}
                for y in commentary_data[x]:
                    comm_id = int(y.get('id',0))
                    inning_commentary[comm_id] = {
                        "ball" : y['ball'],
                        "over" : y['over'],
                        'runs' : y['runs'],
                        'isWide' : y['isWide'],
                        'isNoball' : y['isNoball'],
                        'isRetiredHurt' : y['isRetiredHurt'],
                        'description':y.get('shortText',''),
                        'text':y.get('text',''),
                        'matchOver':y.get('matchOver',None),
                        'matchWicket':y.get('matchWicket',None)
                    }
                ids = sorted(inning_commentary.keys())
                scorecard_id = int(x)-1
                current_batsmen_order = 2
                batsmen = None
                offstrike_batsmen = None
                bowler = None
                bowler1 = None
                team = None
                if  len(m_.scorecard.all()) >= scorecard_id+1:
                    if len(m_.scorecard.all()[scorecard_id].match_batting_inning.all()) >= 1:
                        batsmen = m_.scorecard.all()[scorecard_id].match_batting_inning.all()[0].player
                    if len(m_.scorecard.all()[scorecard_id].match_batting_inning.all()) >= 2:
                        offstrike_batsmen = m_.scorecard.all()[scorecard_id].match_batting_inning.all()[1].player
                    if len(m_.scorecard.all()[scorecard_id].match_bowling_inning.all()) >= 1:
                        bowler = m_.scorecard.all()[scorecard_id].match_bowling_inning.all()[0].player
                    if len(m_.scorecard.all()[scorecard_id].match_bowling_inning.all()) >= 2:
                        bowler1 = m_.scorecard.all()[scorecard_id].match_bowling_inning.all()[1].player
                    team = m_.scorecard.all()[scorecard_id].team1
                out_by_player = None
                total_wickets = 0
                total_runs = 0

                #ids need to sorted to extract bowler for current over
                cnt_to_ids = {}
                ids_to_cnt = {}
                sorted_cnt = 1
                for id in ids:
                    ids_to_cnt[id] = sorted_cnt
                    cnt_to_ids[sorted_cnt] = id
                    sorted_cnt+=1
                #end

                for id in ids:

                    per_bowl_data = inning_commentary[id]
                    per_bowl_data_future = inning_commentary.get(cnt_to_ids.get(ids_to_cnt[id]+6))

                    # update total run
                    total_runs += per_bowl_data.get('runs', 0)
                    # end

                    # if player out then need to update outbyplayer or change player
                    if per_bowl_data['matchWicket'] != None:
                        out_by_player = player_scorecard({'espn_object_id':
                                                              per_bowl_data['matchWicket'].get('id',None),
                                                          'name': per_bowl_data['matchWicket'].get('batsmenName','')})
                        temp = bowler
                        bowler = fall_of_wicket_scorecard({'name': per_bowl_data['matchWicket'].get('bowlerName','')})
                        if bowler is None:
                            bowler = temp
                        current_batsmen_order += 1
                        total_wickets += 1
                        if len(m_.scorecard.all()) >= scorecard_id + 1:
                            if total_wickets < 10 and len(m_.scorecard.all()[scorecard_id].match_batting_inning.all()) >= current_batsmen_order:
                                b_ = m_.scorecard.all()[scorecard_id].match_batting_inning.all()[
                                    current_batsmen_order - 1].player
                                if out_by_player == batsmen:
                                    batsmen = b_
                                elif out_by_player == offstrike_batsmen:
                                    offstrike_batsmen = b_
                    # end

                    # commentary detail
                    commentary_detail = {
                        'inning':scorecard_id+1,
                        'ball': per_bowl_data.get('ball', 0),
                        'over': per_bowl_data.get('over', 0),
                        'total_runs': total_runs,
                        'total_wickets': total_wickets,
                        'is_caugth': None,  # doubt
                        'ball_type': None,  # doubt
                        'runs': per_bowl_data.get('runs', 0),
                        'is_no_ball': per_bowl_data.get('isNoball', 0),
                        'is_wide': per_bowl_data.get('isWide', 0),
                        'description': per_bowl_data.get('description',''),
                        'text': per_bowl_data.get('text',''),
                        'batsmen': batsmen,
                        'offstrike_batsmen': offstrike_batsmen,
                        'bowler': bowler,
                        'player_out': out_by_player,
                        'team': team,
                    }
                    if out_by_player is not None:
                        commentary_detail['is_out'] = True
                        out_by_player = None
                    else:
                        commentary_detail['is_out'] = False
                    # print(commentary_detail)
                    match_commentary.commentary.create(**commentary_detail)
                    match_commentary.save()

                    # end

                    #switching of batsmen when 1 3 or 5 run batsmen take or if it is wide
                    # or no ball then also switching take place
                    order_of_batsmen = switching_batsmen(per_bowl_data,batsmen,offstrike_batsmen)
                    if order_of_batsmen != None:
                        batsmen , offstrike_batsmen = order_of_batsmen
                    #end

                    # match over batsmens and bowler switching
                    if per_bowl_data['matchOver'] != None:
                        # batsmen
                        if per_bowl_data['matchWicket'] == None:
                            a , b = get_batsmen_at_match_over(per_bowl_data)
                            if a: batsmen = a
                            if b: offstrike_batsmen = b

                        if order_of_batsmen != None:
                            batsmen , offstrike_batsmen = offstrike_batsmen , batsmen
                        elif order_of_batsmen == None and per_bowl_data['matchWicket'] != None:
                            a, b = get_batsmen_at_match_over(per_bowl_data)
                            if a: batsmen = a
                            if b: offstrike_batsmen = b
                        #end

                        # bowler
                        bowler_per_over = per_bowl_data['matchOver'].get('bowlers', [None, None])[1]
                        if bowler_per_over and bowler_per_over.get('id'):
                            bowler = player_scorecard(
                                {'espn_object_id': bowler_per_over['id'], 'name': bowler_per_over['name']})
                        else:
                            bowler = bowler1
                        bowler1 = None

                        if per_bowl_data_future and per_bowl_data_future['matchOver']:
                            bowler_per_over_future = per_bowl_data_future['matchOver'].get('bowlers', [None, None])[0]
                            if bowler_per_over_future and bowler_per_over_future.get('id'):
                                bowler = player_scorecard(
                                    {'espn_object_id': bowler_per_over_future['id'], 'name': bowler_per_over_future['name']})
                        #end
                    # end
                    # break
                # break
            # break
        # break