import requests
import datetime
import time
import json
import yaml

def getfromfile(c):
  with open('%s.json' % c, 'r') as r:
    text = r.read()
  return text


def slack(city_lenth):
  if config['slack_toggle']:
    text = '```*Opendoor*: %s UTC' % (today[:19])
    summ = 0
    for c in city_lenth:
      if summ % 2 == 0:
        text += '\n'
      summ += 1
      text += '%9s %4dk, ' % (c[:9], city_lenth[c])
    text += '```'
    print text
    slack_headers = {'Content-type': 'application/json'}
    slack_data = json.dumps({'text': text})
    response = requests.post(url=config['slack_url'],
                             data=slack_data,
                             headers=slack_headers)
    print 'slack response', response.status_code

if __name__ == '__main__':
  with open('config.yml', 'r') as f:
    config = yaml.load(f)
  # city = ['phoenix', 'dallas', 'las_vegas', 'atlanta', 'orlando', 'raleigh']
  city = config['city']
  url = config['opendoorurl']
  headers = config['headers']
  
  today = str(datetime.datetime.today())
  filename = today[:19].replace(':', '-') # 2018-03-02 17:53:54
  city_lenth = {}
  with open('history/%s.json' % filename, 'w') as f:
    f.write('{')
    for c in city:
      f.write('\n"%s":' % c)
      urlc = url + c
      page = requests.get(urlc, headers=headers)
      print c, page.status_code, len(page.text), page.text[:10]
      while len(page.text) > 0 and page.text[0] != '[':
        print 'error: no list returned! sleeping 3s...'
        time.sleep(3)
        page = requests.get(urlc, headers=headers)
        print c, page.status_code, len(page.text), page.text[:10]
      city_lenth[c] = len(page.text) / 1024
      text = page.text.encode('utf-8')
      f.write(text)
      f.write(', \n')
    f.write('\n"time": "%s"\n' % today)
    f.write('}\n')

  slack(city_lenth)
  
  config['filename'] = filename
  with open('config.yml', 'w') as f:
    yaml.dump(config, f)
  # print page.text
  
