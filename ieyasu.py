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
        url = self.site_root + "/works/%s-%s" % (yyyy, mm)
        #print(url, self.site_root + "/works/%s-%s" % (yyyy, mm))

        self.bs = bs4.BeautifulSoup(self.session.get(url=url).text, 'html5lib')
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
                _h = self.site_root + "/" + _h['href'].strip()
            # start
            _s = _i.select_one('td.cellTime.cellTime01.cellBreak.view_work div.item01 span')
            # end
            _e = _i.select_one('td.cellTime.cellTime02.view_work div.item01')
            # break time
            _b = _i.select_one('td.cellTime.cellTime07.cellBtime.view_work')
            # total time
            _t = _i.select_one('td.cellTime.cellTime08.view_work')
            #print(_s, _e, _b, _t)
            if not (_d and _s and _e and _b and _t):
                # lack date or href or ....
                continue
            _d = _d.text.strip()
            _s = _s.text.strip()
            _e = _e.text.strip()
            _b = _b.text.strip()
            _t = _t.text.strip()
            summary[_d] = {'link': _h, 'start': _s, 'end': _e, 'break': _b, 'total': _t,}
        #print(summary)
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
        return summary

    def str_hhmm_2_int_sssss(_t='2:34'):
        """_r = re.search(r'^[0-9]{1,}:[0-9]{1,}$', """

    def dev(self, command=''):
        '''
        request format:
            [YYYY/MM/][D]D,[k|[int],[int][,int]][,][# comments]
        example(core time between 09:00 and 18:00):
            2021/04/01,,+30         # 09:00 <-> 18:30(+30min) 
            2021/04/02,-20,300,60   # 08:40(-20min) <-> 24:00(+300min) break 2:00(+60min)
            2021/04/03,,            # do nothing
            4,                      # do nothing 
            2021/04/05,k            # set rest day
            2021/04/06,08:40,24:00, # 08:40(-20min) <-> 24:00(+300min)

        _u = "https://"
        _b = bs4.BeautifulSoup(self.session.get(url=_u).text, 'html5lib')
        print(_b.prettify())
        exit()
        '''
        _r = re.search(
                r'^\s*((([0-9]{4})[^0-9])([0-9]{1,2})[^0-9])?([0-9]{1,2}),(([0-9]{1,2}:[0-9]{1,2})|([-+]?[0-9]+))?(,(([0-9]{1,2}:[0-9]{1,2})|([-+]?[0-9]+))?)?(,(([0-9]{1,2}:[0-9]{1,2})|([-+]?[0-9]+))?)?',
                command,
                flags=re.I,
                )
        '''
        1: ((([0-9]{4})[^0-9])([0-9]{1,2})[^0-9])?        # 2021/04/, 2020-12-
        2: (([0-9]{4})[^0-9])                             # 2021/, 2023-
        3: ([0-9]{4})                                     # [Year:Opt] 2004
        4: ([0-9]{1,2})                                   # [Month:Opt] 0, 12
        5: ([0-9]{1,2})                                   # [Date:Mand] 11, 3, 31
        6: (([-+]?[0-9]+)|([0-9]{1,2}:[0-9]{1,2}))?       # 20, -45, -300, +30, 9:15, 13:0
        8: ([0-9]{1,2}:[0-9]{1,2})                        # [AbsStartHour:Opt] 9:15, 13:0 , 08:00
        7: ([-+]?[0-9]+)                                  # [RelativeStartHour:Opt] 20, -45, -300, +30
        9: (,(([-+]?[0-9]+)|([0-9]{1,2}:[0-9]{1,2}))?)?   # ,20 ,-45 ,-300 ,+30 ,9:15 ,13:0 ,
        10: (([-+]?[0-9]+)|([0-9]{1,2}:[0-9]{1,2}))?      # 20, -45, -300, +30, 9:15, 13:0
        11: ([0-9]{1,2}:[0-9]{1,2})                       # [AbsEndHour:Opt] 18:15, 20:0 , 23:00
        12: ([-+]?[0-9]+)                                 # [RelativeEndHour:Opt] 20, -45, -300, +30
        13: (,(([-+]?[0-9]+)|([0-9]{1,2}:[0-9]{1,2}))?)?  # ,20 ,-45 ,-300 ,+30 ,9:15 ,13:0 ,
        14: (([-+]?[0-9]+)|([0-9]{1,2}:[0-9]{1,2}))?      # 20, -45, -300, +30, 9:15, 13:0
        15: ([0-9]{1,2}:[0-9]{1,2})                       # [AbsBreakTime:Opt] 0:30, 2:20
        16: ([-+]?[0-9]+)                                 # [RelativeBreakTime:Opt] 20, -45, -300, +30
        '''
        if not _r: 
            """Unrecognized command"""
            return None
        # now
        now = datetime.datetime.now()
        # year
        if _r.group(3):
            yyyy = int(_r.group(3))
        else:
            yyyy = now.year
        # month
        if _r.group(4):
            mm = int(_r.group(4))
        else:
            mm = now.month
        # date
        dd = int(_r.group(5))









        with open('../sample') as fh:
            self.bs = bs4.BeautifulSoup(fh.read(), 'html5lib')
        _f = self.bs.select_one('form[enctype="multipart/form-data"]')
        print(_f.prettify())
        # action
        action = _f["action"]
        # inputs
        form = {}
        [ft.wrap(self.bs.new_tag('fake')) for ft in _f.select('[name]')]
        for tag in _f.select('fake'):
            '''
            inputs habitts:
                valueless hidden -> set("") / except name=holiday
                unchecked checkbox -> no entry

            '''
            #print(tag.prettify())
            if tag.select_one('input[type=checkbox]'):
                # input[type=checkbox]
                continue
            elif tag.select_one('input[disabled=disabled]'):
                # input[type=*][disabled=disabled]
                continue
            elif tag.select_one('input[type=hidden][name][value]'):
                # input[hidden]
                form[tag.select_one('input[type=hidden][name][value]')['name']] = (None, tag.select_one(
                        'input[type=hidden][name][value]')['value'])
            elif tag.select_one('select[name] option[selected=selected][value]'):
                # select option[selected]
                form[tag.select_one('select[name]')['name']] = (None, tag.select_one(
                        'select option[selected=selected][value]')['value'])
            elif tag.select_one('input[type=text][value]'):
                # input[text]
                form[tag.select_one('input[type=text][name][value]')['name']] = (None, tag.select_one(
                        'input[type=text][name][value]')['value'])
            else:
                print("ERR", tag.prettify())
                form[tag.select_one('[name]')['name']] = (None, '')
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
            form[i] = (None, overwriting_form[i])
        #form[''] = 
        [ print(i, form[i]) for i in form.keys()]

        exit()
        action_url = self.relative_path_to_url(self.bs.form['action'])
        # current YYYY
        yyyy = re.search('/([0-9]{4})-', action_url).group(1)
        # current MM
        mm = re.search('-([0-9]{2})$', action_url).group(1)
        print(self.bs.select_one('form').prettify())
        #print(self.bs.form.select('table tr'))
        hoplist = {}
        for i in self.bs.form.select('table tr'):
            # date
            _d = i.select_one('td.cellDate span.date')
            # href
            _h = i.select_one('td.cellDate div.view_work a[href]')
            # start
            _s = i.select_one('td.cellTime.cellTime01.cellBreak.view_work div.item01 span')
            # end
            _e = i.select_one('td.cellTime.cellTime02.view_work div.item01')
            # break time
            _b = i.select_one('td.cellTime.cellTime07.cellBtime.view_work')
            # total time
            _t = i.select_one('td.cellTime.cellTime08.view_work')
            #print(_s, _e, _b, _t)
            if not (_d and _h and _s and _e and _b and _t):
                # lack date or href or ....
                continue
            _d = _d.text.strip()
            _h = _h['href'].strip()
            _s = _s.text.strip()
            _e = _e.text.strip()
            _b = _b.text.strip()
            _t = _t.text.strip()
            print(_d, _s, _e, _b, _t, _h)
        """
        for i in self.bs.form.select('table tr'):
            # date
            _d = i.select_one('td.cellDate span.date')
            if not _d:
                continue
            # href
            _h = i.select_one('td.cellDate div.view_work a')
            if not _h:
                continue
            print(_d.text.strip(), _h['href'].strip())
        """




y = Yeyasu(
        url=c['url'],
        user=c['usr'],
        password=c['pas'])
"""
print(y.login())
y.print_monthly_summary("2021-04")
"""
y.dev("2021-04")
exit()

#y.dev()
