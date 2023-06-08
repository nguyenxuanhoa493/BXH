import streamlit as st
import pandas as pd
import requests, urllib3
from streamlit_autorefresh import st_autorefresh

urllib3.disable_warnings()

st.set_page_config(page_title="Homepage",layout='wide')
HEADER = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
class Domain:
    def __init__(self, user):
        self.server = 'https://alpha-api.lotuslms.com'
        self.param = {'submit': '1', '_sand_ajax': '1', '_sand_platform': '3', '_sand_readmin': '1', '_sand_is_wan': 'false',
                      '_sand_ga_sessionToken': '', '_sand_ga_browserToken': '', '_sand_domain':'bvl', '_sand_masked': ''}
        self.user = self.login(user)
        

    def send(self,type, url, payload, files =[]):
        url = self.server + url
        payload.update(self.param)
        rq = requests.request(type, url=url, data=payload, headers=HEADER, files =files, verify=False)
        return rq.json()

    def login(self, user):
        payload = {'lname': user, 'pass': 'qwe123!@#QWE'}
        r = self.send('POST', '/user/login', payload)
        try:
            r = r['result']
            info = {'_sand_token': r['token'],'_sand_uiid': r['iid'], '_sand_uid': r['id']}
            self.param.update(info)
            print(f"Đã login bằng tài khoản: {user}")
            if user=='root':
                self.param.update({'_sand_domain':'system'})
            return r
        except:
            pass
    def rank(self,exam_round_iid):
        payload = {
            'criteria':'take_count',
            'exam_round_iid':exam_round_iid,
            'items_per_page':'1000000',
            'page':1,
        }
        r = self.send('POST', '/contest/score/rank', payload)
        if r['count']>0:
            return r['result']
        else:
             return False
            
            
        
def merge_rank(rank1, rank2):
    list_score = []
    rank = {}
    for user in rank1:
        rank.update({user['user_iid']:{
            'code':user['__expand']['user']['code'],
            'name':user['__expand']['user']['name'],
            'org':user['__expand']['orgs'][0]['short_name'],
            'score':user['score'],
            'spent_time':user['spent_time'],
            

        }})
    for user2 in rank2:
        iid = user2['user_iid']
        try:
            score =rank[iid]['score']
            spent_time =rank[iid]['spent_time'] 
            rank[iid].update({
                'score2':user2['score'],
                'spent_time2':user2['spent_time'],
                'total_score':user2['score']+score,
                'total_spent_time':user2['spent_time']+spent_time

            })
        except:
            rank.update({
                iid:{
                    'code':user2['__expand']['user']['code'],
                    'name':user2['__expand']['user']['name'],
                    'org':user2['__expand']['orgs'][0]['short_name'],
                    'score':0,
                    'spent_time':0,                  
                    'score2':user2['score'],
                    'spent_time2':user2['spent_time'],
                    'total_score':user2['score'],
                    'total_spent_time':user2['spent_time']
                }

            })
    for user in rank1:
        iid = user['user_iid']
        have_total_score = rank[iid].get('total_score',False)
        if not have_total_score:
            rank[iid].update({
                'total_score':rank[iid]['score'],
                'total_spent_time':rank[iid]['spent_time'],
                
                })
            
    rank = [i for i in rank.values()]
    rank = pd.DataFrame(rank)
    rank.sort_values(by=['total_score', 'total_spent_time'], inplace=True,ascending = [False, True])
    rank['spent_time'] = pd.to_datetime(rank["spent_time"], unit='s').dt.strftime("%H:%M:%S")
    rank['spent_time2'] = pd.to_datetime(rank["spent_time2"], unit='s').dt.strftime("%H:%M:%S")
    rank['total_spent_time'] = pd.to_datetime(rank["total_spent_time"], unit='s').dt.strftime("%H:%M:%S")

    rank = rank[['code', 'name', 'org', 'score', 'spent_time', 'score2', 'spent_time2', 'total_score','total_spent_time']]
    rank.rename(columns = {
        'code':'Mã thí sinh',
        'name':'Họ và tên',
        'org':'Đơn vị',
        'score':'Điểm vòng 1',
        'spent_time':'Thời gian làm vòng 1',
        'score2':'Điểm vòng 2',
        'spent_time2':'Thời gian làm vòng 2',
        'total_score':'Tổng điểm',
        'total_spent_time':'Tổng thời gian',
        }, inplace = True)
    # rank.columns = ['Mã thí sinh', 'Họ và tên', 'Đơn vị', 'Điểm vòng 1', 'Thời giang vòng 1', 'Điểm vòng 2', 'Thời giang vòng 2', 'Tổng điểm', 'Tổng thời gian']
    
    return rank

def one_rank(data):
    rank =[]
    for user in data:
        temp = {
            'code':user['__expand']['user']['code'],
            'name':user['__expand']['user']['name'],
            'org':user['__expand']['orgs'][0]['short_name'],
            'score':user['score'],
            'spent_time':user['spent_time']
        }
        rank.append(temp)
    rank = pd.DataFrame(rank)
    rank.sort_values(by=['score', 'spent_time'], inplace=True,ascending = [False, True])
    rank['spent_time'] = pd.to_datetime(rank["spent_time"], unit='s').dt.strftime("%H:%M:%S")
    rank.columns = ['Mã thí sinh', 'Họ và tên', 'Đơn vị','Tổng điểm', 'Tổng thời gian']
    return rank
bvl = Domain('bvl')
st.title(':blue[Bảng xếp hạng cuộc thi tranh tài BVLN tháng 6]')
data=st.experimental_get_query_params()
st_autorefresh(interval=10000, limit=1000, key="st_autorefresh")

round1=data.get('round1',9591642)
round2=data.get('round2',9591645)

rank1= bvl.rank(round1)
rank2= bvl.rank(round2)

if rank2 and not rank1:
    rank = one_rank(rank2)
    st.dataframe(rank,use_container_width=True, hide_index=True, height=1000)
elif rank1 and not rank2:
    rank = one_rank(rank1)
    st.dataframe(rank,use_container_width=True, hide_index=True, height=1000)

elif rank1 and rank2:
    rank = rank = merge_rank(rank1,rank2)
    st.dataframe(rank,use_container_width=True, hide_index=True, height=1000)
else:
    st.title('Chưa có kết quả')



# st.download_button(label='📥 Download Current Result', file_name= 'bxh.xlsx')

