from cds_match_inning.models import MatchBatsmanInning,MatchFieldingInning,MatchBowlersInning
from tqdm import tqdm
from django.db.models import Q

def update_fielding():

    for x in tqdm(MatchBatsmanInning.objects.all()):
        if len(MatchFieldingInning.objects.filter(scorecard=x.scorecard,player=x.player)) == 0:
            how_out = x.how_out.replace('&dagger;','')

            #extracting fielder and bowler from how out
            if how_out.find('not out') == -1:
                if how_out.find('run out') == -1: bowler = how_out[how_out.rfind('b')+2:]
                else: bowler = how_out[how_out.find('out (')+5:-1]
                if how_out.find('run out') == -1 and how_out.find('c ') !=- 1 : fielder = how_out[how_out.rfind('c ')+2:how_out.rfind(' b')]
                elif how_out.find('lbw') == -1: fielder = how_out[how_out.find('out (')+5:how_out.rfind('/')]
                else:fielder = None
            else:
                bowler = None
                fielder = None
            #END

            #finding player object
            bowler = MatchBowlersInning.objects.filter(scorecard=x.scorecard).filter(Q(player__name__contains=bowler) | Q(player__fullname__contains=bowler)) if bowler != None else []
            q1 = MatchBowlersInning.objects.filter(scorecard=x.scorecard).filter(Q(player__name__contains=fielder) | Q(player__fullname__contains=fielder)) if fielder != None else []
            q2 = MatchBatsmanInning.objects.filter(scorecard=x.scorecard).filter(Q(player__name__contains=fielder) | Q(player__fullname__contains=fielder)) if fielder != None else []
            players = []
            for m in q1: players.append(m.player)
            for m in q2: players.append(m.player)
            fielder = players
            #END

            isOut = False if how_out.find("not out") != -1 or how_out.find('absent hurt') != -1 or how_out.find('retired hurt') != -1 else True

            fielding_detail = {
                'isOut': isOut,
                'isRunOut':  True if how_out.find('run out') != -1 else False,
                'isLbw':  True if how_out.find('lbw') != -1 else False,
                'isCaught':True if how_out.find('c ') != -1 else False,
                'isBowled': True if how_out.find('c ') == -1 and how_out.find('lbw') == -1 and how_out.find('run out') == -1 and isOut else False ,
                'bowler': bowler[0].player if len(bowler) != 0 else None,
                'fielder': fielder[0] if len(fielder) != 0 else None,
                'scorecard': x.scorecard,
                'player': x.player,
            }
            MatchFieldingInning(**fielding_detail).save()