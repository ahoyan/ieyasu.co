#!/usr/bin/python3
# -*- config:utf-8 -*-

import bs4
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
        self.post = {}
        for tag in self.form.select('[name]'):
            if tag.has_attr('value'):
                self.post[tag['name']] = tag['value']
            else:
                self.post[tag['name']] = ''
        self.post['user[login_id]'] = self.user
        self.post['user[password]'] = self.password
        print(self.form['action'])

        self.login_url = self.relative_path_to_url(self.form['action'])
        return self.post

    def login(self):
        self.request = self.session.post(url=self.login_url, data=self.post)
        self.bs = bs4.BeautifulSoup(self.request.text, 'html5lib')
        print(self.bs.prettify())
        
    def dev(self):
        '''
        request format:
            [YYYY/MM/][D]D,[k|[int],[int][,int]][,][# comments]
        example(core time between 09:00 and 18:00):
            2021/04/01,,+30         # 09:00 <-> 18:30(+30min) 
            2021/04/02,-20,300,60   # 08:40(-20min) <-> 24:00(+300min) rest 2:00(+60min)
            2021/04/03,,            # do nothing
            4,                      # do nothing
            2021/04/05,k            # set rest day
        '''

        with open('sample') as fh:
            self.bs = bs4.BeautifulSoup(fh.read(), 'html5lib')
        print(self.bs.form)
        action_url = self.relative_path_to_url(self.bs.form['action'])
        # current YYYY
        yyyy = re.search('=([0-9]{4})-', action_url).group(1)
        # current MM
        mm = re.search('-([0-9]{2})$', action_url).group(1)

        print(action_url)
        #print(self.bs.form.select('table tr'))
        hoplist = {}
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




y = Yeyasu(
        url=c['url'],
        user=c['usr'],
        password=c['pas'])
'''
y.create_post_from_toppage()
print(y.site_root,y.post)
y.login()
'''
y.dev()
