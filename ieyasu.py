#!/usr/bin/python3
# -*- config:utf-8 -*-

import bs4
import datetime
import requests
import re
import yaml


with open('config.yaml',) as fh:
    c = yaml.load(fh.read(), Loader=yaml.FullLoader)

s = requests.Session() 
r = s.get(url=c['url'])
b = bs4.BeautifulSoup(r.text, 'html5lib')
f = b.select_one('form#new_user')
class Yeyasu():
    def __init__(
            self,
            url='https:/',
            user='',
            password='',
            ):
        self.session=requests.Session()
        self.post = {}
        self.login_url = url
        self.user = user
        self.password = password
        self.site_root = self.relative_path_to_url('/', url)[:-1]
        self.standard_start_time = '09:00' if not 'sst' in c else c['sst']
        self.standard_end_time = '18:00' if not 'set' in c else c['set']
        self.standard_break_time = '1:00' if not 'sbt' in c else c['sbt']

    def relative_path_to_url(self, path='/', url=''):
        if not url:
            url = self.site_root
        _r = re.search('^(https?)://([^/]+)', url, flags=re.I)
        proto = _r.group(1)
        domain = _r.group(2)
        if re.search('^//', path):
            return proto + ':' + path
        elif re.search('^/', path):
            return proto + '://' + domain + path
        #else:
        return proto + '://' + domain + '/' + path

    def create_post_from_toppage(self):
        '''
        - create/reuse session.
        - download toppage.
        - generate post string from form, IDs
        - return [postdata, session]
        '''
        self.request = self.session.get(url=self.login_url)
        self.bs = bs4.BeautifulSoup(self.request.text, 'html5lib')
        self.form = self.bs.select_one('form#new_user')
        self.login_form = {}
        for tag in self.form.select('[name]'):
            if tag.has_attr('value'):
                self.login_form[tag['name']] = tag['value']
            else:
                self.login_form[tag['name']] = ''
        self.login_form['user[login_id]'] = self.user
        self.login_form['user[password]'] = self.password
        #print(self.form['action'], self.login_form)

        self.login_url = self.relative_path_to_url(self.form['action'])
        return self.login_form

    def login(self):
        self.create_post_from_toppage()
        return bs4.BeautifulSoup(
                self.session.post(url=self.login_url, data=self.login_form).text,
                'html5lib')

    def print_monthly_summary(self, date="2021/04"):
        """
        date format:
            yyyy.mm[.dd]
        """
        _r = re.search('^\s*([0-9]{4})[^0-9]([0-9]{2})', date)
        if not _r:
            return {}
        yyyy = _r.group(1)
        mm =_r.group(2)
        _l = {}
        _url = self.site_root + "/works/%s-%s" % (yyyy, mm)
        #print(_url, self.site_root + "/works/%s-%s" % (yyyy, mm))

        self.bs = bs4.BeautifulSoup(self.session.get(url=_url).text, 'html5lib')
        #print(self.bs.prettify())
        summary = {}
        for _i in self.bs.form.select('table tr'):
            # date
            _d = _i.select_one('td.cellDate span.date')
            # href
            _h = _i.select_one('td.cellDate div.view_work a[href]')
            if not _h:
                _h = "UnEditable or Accepted"
            else:
                #_h = self.site_root + "/" + _h['href'].strip()
                _h = self.relative_path_to_url(_h['href'].strip())
            # start
            _s = _i.select_one('td.cellTime.cellTime01.cellBreak.view_work div.item01 span')
            # end
            _e = _i.select_one('td.cellTime.cellTime02.view_work div.item01')
            # break time
            _b = _i.select_one('td.cellTime.cellTime07.cellBtime.view_work')
            # total time
            _t = _i.select_one('td.cellTime.cellTime08.view_work')
            if not (_d and _s and _e and _b and _t):
                # lack date or href or ....
                continue
            _d = _d.text.strip()
            _s = _s.text.strip()
            _e = _e.text.strip()
            _b = _b.text.strip()
            _t = _t.text.strip()
            summary[_d] = {'link': _h, 'start': _s, 'end': _e, 'break': _b, 'total': _t,}
        """
        print(summary)
        print('Year,%s,Month,%s,'  % (yyyy, mm))
        print('Date,Start,End,Breaks,Total,Link')
        for _i in sorted(summary.keys()):
            print('%s,%s,%s,%s,%s,%s' % (
                _i,
                summary[_i]['start'],
                summary[_i]['end'],
                summary[_i]['break'],
                summary[_i]['total'],
                summary[_i]['link']))
        """
        return summary

    def str_hhmm_2_int_sssss(self, _t='2:34') -> int:
        _r = re.search(r'^([0-9]{1,}):([0-9]{1,}$)', _t)
        if _r:
            _h, _m = [int(x) for x in _r.groups()]
            return int(60*_m + 60**2*_h)
        else:
            return _t

    def int_sssss_2_str_hhmm(self, _t='12345') -> str:
        if _t == None:
            return _t
        _m = int(int(_t) / 60)
        _h = int(_m / 60)
        _m = int(_m % 60)
        return "%02d:%02d" % (_h, _m)

    def update_attendance(self, command=''):
        '''
        command format:
            [YYYY/MM/][D]D,[k|[int],[int][,int]][,][# comments]

        example(core time between 09:00 and 18:00):
            2021/04/01,,+30         # 09:00 <-> 18:30(+30min) 
            2021/04/02,-20,300,60   # 08:40(-20min) <-> 24:00(+300min) break 2:00(+60min)
            2021/04/03,,            # do nothing
            4,                      # do nothing 
            2021/04/06,08:40,24:00, # 08:40(-20min) <-> 24:00(+300min)

            2021/04/05,k            # set rest day *** not implemented ***
        '''
        _r = re.search(
                r'^\s*((([0-9]{4})[^0-9])([0-9]{1,2})[^0-9])?([0-9]{1,2}),(([0-9]{1,2}:[0-9]{1,2})|([-+]?[0-9]+))?' \
                r'(,(([0-9]{1,2}:[0-9]{1,2})|([-+]?[0-9]+))?)?(,(([0-9]{1,2}:[0-9]{1,2})|([-+]?[0-9]+))?)?',
                command,
                flags=re.I,)
        '''
        1: ((([0-9]{4})[^0-9])([0-9]{1,2})[^0-9])?        # 2021/04/, 2020-12-
        2: (([0-9]{4})[^0-9])                             # 2021/, 2023-
        3: ([0-9]{4})                                     # [Year:Opt] 2004
        4: ([0-9]{1,2})                                   # [Month:Opt] 0, 12
        5: ([0-9]{1,2})                                   # [Date:Mand] 11, 3, 31
        6: (([-+]?[0-9]+)|([0-9]{1,2}:[0-9]{1,2}))?       # 20, -45, -300, +30, 9:15, 13:0
        7: ([0-9]{1,2}:[0-9]{1,2})                        # [AbsStartHour:Opt] 9:15, 13:0 , 08:00
        8: ([-+]?[0-9]+)                                  # [RelativeStartHour:Opt] 20, -45, -300, +30
        9: (,(([-+]?[0-9]+)|([0-9]{1,2}:[0-9]{1,2}))?)?   # ,20 ,-45 ,-300 ,+30 ,9:15 ,13:0 ,
        10: (([-+]?[0-9]+)|([0-9]{1,2}:[0-9]{1,2}))?      # 20, -45, -300, +30, 9:15, 13:0
        11: ([0-9]{1,2}:[0-9]{1,2})                       # [AbsEndHour:Opt] 18:15, 20:0 , 23:00
        12: ([-+]?[0-9]+)                                 # [RelativeEndHour:Opt] 20, -45, -300, +30
        13: (,(([-+]?[0-9]+)|([0-9]{1,2}:[0-9]{1,2}))?)?  # ,20 ,-45 ,-300 ,+30 ,9:15 ,13:0 ,
        14: (([-+]?[0-9]+)|([0-9]{1,2}:[0-9]{1,2}))?      # 20, -45, -300, +30, 9:15, 13:0
        15: ([0-9]{1,2}:[0-9]{1,2})                       # [AbsBreakTime:Opt] 0:30, 2:20
        16: ([-+]?[0-9]+)                                 # [RelativeBreakTime:Opt] 20, -45, -300, +30

        ## "2021/04/01,,+30" -> ['2021/04/', '2021/', '2021', '04', '01', None, None, None, ',+30', '+30', None, '+30', None, None, None, None]
        '''
        if not _r: 
            """Unrecognized command"""
            return None
        # now
        _now = datetime.datetime.now()
        # year
        if _r.group(3):
            _yyyy = int(_r.group(3))
        else:
            """ fill current year,if not specified. """
            _yyyy = _now.year
        # month
        if _r.group(4):
            _mm = int(_r.group(4))
        else:
            """ fill current month, if not specified. """
            _mm = _now.month
        # date (mandatory)
        _dd = int(_r.group(5))
        # start time
        if _r.group(7) != None:
            _st = self.str_hhmm_2_int_sssss(_r.group(7))
        elif _r.group(8) != None:
            _st = int(_r.group(8)) * 60 + self.str_hhmm_2_int_sssss(self.standard_start_time)
        else:
            """ Not specifiied, so do not modify start-time """
            _st = None
        # end time
        if _r.group(11) != None:
            _et = self.str_hhmm_2_int_sssss(_r.group(11))
        elif _r.group(12) != None:
            _et = int(_r.group(12)) * 60 + self.str_hhmm_2_int_sssss(self.standard_end_time)
        else:
            """ Not specifiied, so do not modify end-time """
            _et = None
        # break time
        if _r.group(15) != None:
            _bt = self.str_hhmm_2_int_sssss(_r.group(15))
        elif _r.group(16) != None:
            _bt = int(_r.group(16)) * 60 + self.str_hhmm_2_int_sssss(self.standard_break_time)
        else:
            """ Not specifiied, so do not modify break-time """
            _bt = None
        if _st == None and _et == None and _bt == None:
            """ command does nothing """
            return None

        _s = self.print_monthly_summary("%04d/%02d" % (_yyyy, _mm))
        _b = bs4.BeautifulSoup(
                self.session.get(
                    url=_s["%02d" % _dd]['link']).text,
                'html5lib')

        _f = _b.select_one('form[enctype="multipart/form-data"]')
        # action
        action = self.relative_path_to_url(_f["action"])
        # inputs
        _form = {}
        [ft.wrap(_b.new_tag('fake')) for ft in _f.select('[name]')]
        for tag in _f.select('fake'):
            '''
            inputs habitts:
                valueless hidden -> set("") / except name=holiday
                unchecked checkbox -> no entry

            '''
            if tag.select_one('input[type=checkbox]'):
                # input[type=checkbox]
                continue
            elif tag.select_one('input[disabled=disabled]'):
                # input[type=*][disabled=disabled]
                continue
            elif tag.select_one('input[type=hidden][name][value]'):
                # input[hidden]
                _form[tag.select_one('input[type=hidden][name][value]')['name']] = (None, tag.select_one(
                        'input[type=hidden][name][value]')['value'])
            elif tag.select_one('select[name] option[selected=selected][value]'):
                # select option[selected]
                _form[tag.select_one('select[name]')['name']] = (None, tag.select_one(
                        'select option[selected=selected][value]')['value'])
            elif tag.select_one('input[type=text][value]'):
                # input[text]
                _form[tag.select_one('input[type=text][name][value]')['name']] = (None, tag.select_one(
                        'input[type=text][name][value]')['value'])
            else:
                #print("ERR", tag.prettify())
                _form[tag.select_one('[name]')['name']] = (None, '')
        overwriting_form = {
                "holiday": "false",
                "commit": "登録する",
                "work[next_day_start]": "",
                "work[next_day_end]": "",
                "next_day_break_1_start]": "",
                "next_day_break_1_end": "",
                "next_day_break_2_start": "",
                "next_day_break_2_end": "",
                }
        for i in overwriting_form.keys():
            _form[i] = (None, overwriting_form[i])
        remove_keys = ["add_application"]
        for i in remove_keys:
            del _form[i]

        if _st != None:
            _form['work[start_at_str]'] = (None, self.int_sssss_2_str_hhmm(_st))
        if _et != None:
            _form['work[end_at_str]'] = (None, self.int_sssss_2_str_hhmm(_et))
        if _bt != None:
            _form['work[break_2_start_at_str]'] = (None, self.standard_end_time)
            _form['work[break_2_end_at_str]'] = (None, self.int_sssss_2_str_hhmm(
                self.str_hhmm_2_int_sssss(self.standard_end_time) 
                + _bt 
                - self.str_hhmm_2_int_sssss(self.standard_break_time)))
        ret = bs4.BeautifulSoup(
                self.session.post(url=action, data=_form).text,
                'html5lib')
        return ()


y = Yeyasu(url=c['url'], user=c['usr'], password=c['pas'])
y.login()
#y.update_attendance("2021/04/02,,300,60")
#y.update_attendance("2021/04/05,,30,")
#y.update_attendance("2021/04/06,-10,30,20")
data = '''2021/04/02,,300,60
2021/04/05,,30,
2021/04/06,-10,30,20
'''
for l in data.splitlines():
    y.update_attendance(l)

exit()
