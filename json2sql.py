# coding: utf-8
# author: ai
# usage : convert opendoor json to postgreSQL

import psycopg2
import json
import yaml
from datetime import datetime
import requests

def json2sql(house):
  exist = sql_exist(house['id'])
  columnlist = [
    'source', 'source_id', 'latitude', 'longitude',
    'squarefeet', 'bathrooms', 'bedrooms', 'yearbuilt',
    'propertytype', 'lotsize', 'ispool', 'address1', 'zip',
    'city', 'county', 'cbsacode', 'state', 'listprice',
    'monthlyrent', 'yearlyinsurancecost', 'yearlypropertytaxes',
    'appreciation', 'neighborscore', 'status', 'updated_at', # 'created_at'
    'imgurl'
  ]
  value = {}
  value['source'] =     'opendoor'
  value['source_id'] =  house['id']             if 'id' in house else 'none'
  value['latitude'] =   house['lonlat'][1]      if 'lonlat' in house else 'none'
  value['longitude'] =  house['lonlat'][0]      if 'lonlat' in house else 'none'
  value['squarefeet'] = house['square_footage'] if 'square_footage' in house else 'none'
  value['bathrooms'] =  house['bathrooms']      if 'bathrooms' in house else 'none'
  value['bedrooms'] =   house['bedrooms']       if 'bedrooms' in house else 'none'
  value['yearbuilt'] =  house['year_built']     if 'year_built' in house else 'none'
  if 'address' in house:
    value['address1'] = house['address']['street1']     if 'street1' in house['address'] else 'none'
    value['zip'] =      house['address']['postal_code'] if 'postal_code' in house['address'] else 'none'
    value['city'] =     house['address']['city']        if 'city' in house['address'] else 'none'
    value['state'] =    house['address']['state']       if 'state' in house['address'] else 'none'
  value['listprice'] =  house['price_cents'] / 100.0    if 'price_cents' in house else 'none'
  value['status'] = house['display_state'] \            if 'display_state' in house and 'flip_state' in house else 'none'
  try:
    value['imgurl'] = house['listing_photos'][0]['thumbnail_urls'].values()[0]
  except:
    print 'Warning: id %s has no imgurl' % house['id']
    
  if not exist:
    columnlist.append('created_at')
    value['created_at'] = updated
  value['updated_at'] = updated
  # value[''] = house['']
  
  if exist:
    setstr = ''
    for key in value:
      i = value[key]
      if isinstance(i, str) or isinstance(i, unicode):
        i = "'%s'" % i
      setstr += '%s = %s, ' % (key, i)
    setstr = setstr[:-2]
    sql = "UPDATE %s SET %s WHERE source_id=%s;" % (table, setstr, house['id'])
    print 'update:', sql
  else:
    columns = ''.join([i + ', ' for i in columnlist])[:-2]
    # print columns
    valuelist = [value[k] if k in value else None for k in columnlist]
    valuestr = ''
    for i in valuelist:
      if i == None:
        i = 'null'
      elif isinstance(i, str) or isinstance(i, unicode):
        i = "'%s'" % i
      valuestr += str(i) + ', '
    valuestr = valuestr[:-2]
    # print [valuestr]
    # sql = "INSERT INTO %s (%s) VALUES (%s);" % (table, columns, valuestr)
  cursor.execute(sql)
  conn.commit()

def sql_exist(id):
  sql = "SELECT * FROM %s WHERE source_id=%s;" % (table, str(id))
  cursor.execute(sql)
  results = cursor.fetchall()
  if len(results) > 0:
    if len(results) > 1:
      print 'warning: multiple rows of source_id:%s' % str(id)
    return True
  else:
    return False

def slack(lenth):
  text = '```Opendoor to PSQL: %s UTC' % (updated[:10])
  summ = 0
  for c in lenth:
    if summ % 2 == 0:
      text += '\n'
    summ += 1
    text += '%9s %4d, ' % (c[:9], lenth[c])
  text += '```'
  print text
  slack_headers = {'Content-type': 'application/json'}
  slack_data = json.dumps({'text': text})
  if config['slack_toggle'] == False:
    return
  response = requests.post(url=config['slack_url'],
                           data=slack_data,
                           headers=slack_headers)
  print 'slack response', response.status_code


if __name__ == '__main__':
  config = yaml.load(open('config.yml'))
  conn = psycopg2.connect(database= config['postgre']['db'],
                          user=     config['postgre']['user'],
                          password= config['postgre']['password'],
                          host=     config['postgre']['host'],
                          port=     config['postgre']['port'])
  table = 'property'
  cursor = conn.cursor()
  
  today = str(datetime.today())
  # today = '2018-03-01'
  try:
    with open('%s.json' % today[:10], 'r') as f:
      all = f.read().strip()
  except IOError:
    print '404: %s.json not found!' % today[:10]
    exit()
  all = json.loads(all)
  updated = all['time']
  print [updated]
  
  lenth = {}
  for city in all:
    if city == 'time':
      continue
    print 'city', city
    houselist = all[city]
    lenth[city] = len(houselist)
    for h in houselist:
      json2sql(h)
      exit()
      
  slack(lenth)
  conn.close()