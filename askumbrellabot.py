# Copyright (C) 2020  Alexandre Argeris and Valentim Muniz

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/


import requests
import json
import sys
import re
import time
import datetime
import configparser

# read variables from config
config = configparser.ConfigParser()
config.read('config')
org_id = config['Umbrella']['OrgID']
mgmt_api_key = config['Umbrella']['ManagementAPIKey']
mgmt_api_secret = config['Umbrella']['ManagementAPISecret']
UMB_Investigate_token = config['Umbrella']['InvestigateKey']
bearer = config['Bot']['AccessToken']
logs_roomId = config['Webex']['RoomID']
webex_domain = [config['Webex']['WebexDomain']]
webhook_port = config['WebHook']['Port']
admin_email = config['Script']['AdminEmail']
log_directory = config['Logs']['Directory']
log_prefix = config['Logs']['Prefix']

from json2html import *

try:
    from flask import Flask
    from flask import request
except ImportError as e:
    print(e)
    print("Looks like 'flask' library is missing.\n"
          "Type 'pip3 install flask' command to install the missing library.")
    sys.exit()

requests.packages.urllib3.disable_warnings()


#Headers for Investigate
headers = {"Accept": "application/json", "Content-Type": "application/json; charset=utf-8", "Authorization": "Bearer " + bearer}


#Headers for Management & Reporting
header_mgmt = {'content-type': 'application/json'}

# management api url, used to get access token for reporting api
mgmt_api_url = 'https://management.api.umbrella.com/auth/v2/oauth2/token'

# reporting api url
reporting_api_url = 'https://reports.api.umbrella.com/v2'


def get_reporting_request(access_token, endpoint):
    header_mgmt['Authorization'] = 'Bearer {}'.format(access_token)
    r = requests.get(reporting_api_url+endpoint, headers=header_mgmt)
    body = json.loads(r.content)
    return body

def get_access_token():
    global code_access_token
    r = requests.get(mgmt_api_url, headers=header_mgmt, auth=(mgmt_api_key, mgmt_api_secret))
    code_access_token = r.status_code
    if r.status_code == 401 or r.status_code == 403:
        return code_access_token

    body = json.loads(r.content)
    return body['access_token']


expected_messages = {"help me": "help",
                     "need help": "help",
                     "can you help me": "help",
                     "ajuda": "help",
                     "help": "help",
                     "greetings": "greetings",
                     "hello": "greetings",
                     "ola": "greetings",
                     "como esta": "greetings",
                     "hi": "greetings",
                     "how are you": "greetings",
                     "what's up": "greetings",
                     "what's up doc": "greetings"}

def send_spark_get(url, payload=None, js=True):
    if payload is None:
        request = requests.get(url, headers=headers)
    else:
        request = requests.get(url, headers=headers, params=payload)
    if js is True:
        request = request.json()
    return request

def send_spark_post(url, data):
    request = requests.post(url, json.dumps(data), headers=headers).json()
    return request

def help_me():
    return "Opaaa! Eu posso te ajudar. Abaixo tem uma lista com os comandos que eu entendo:<br/>" \
           "`ajuda` - Vou mostrar o que posso fazer.<br/>" \
           "`hello` - Vou exibir minha mensagem de saudação<br/>" \
           "`domain:` - Digite o dominio para consulta - Ex: 'domain: internetbadguys.com'<br/> ou domain internetbadguys.com <br>" \
           "`toplist XX` - Eu vou mostrar o top Umbrella Popularity Domain List - Global list - Ex: toplist 25'<br/>" \
           "`threats` - Eu vou mostrar o top de ameaças em um mês<br/>" \
           "`total` - Eu vou mostrar o total que de Requests em 1 mês<br/>" \
           "`summary or summ` - Eu vou mostrar o Sumário do Umbrella Reporting em um mês<br/>"

def greetings():
    return "Olá meu nome é {}.<br/>" \
           "Eu estou integrado com o Cisco Umbrella Threat Intelligence - Investigate & Reporting <br/>" \
           "Este Bot está sendo rodado por {} <br/>" \
           "Digite `Ajuda` para ver o que posso fazer.<br/>".format(bot_name,admin_email)

def totalrequests(totalreq):
    return "Cisco Umbrella Total Requests: <b>{}</b>".format(totalreq)

def summary(sum):
    return "Cisco Umbrella Summary: <br><b>{}</b>".format(sum)

def topthreats(topthreat):
    if topthreat == "":
        return "Nenhuma ameaça encontrada =D"
    else:
        return "Cisco Umbrella Top Threats: <br><b>{}</b>".format(topthreat)

def umbrella_get(varDOMAIN, roomType, room_title, today, timestamp, personEmail):
        today = datetime.datetime.today()
        timestamp = today.strftime('%Y-%m-%d %H:%M:%S')
        date = datetime.date.today()
        today = date.strftime('%Y-%m-%d')
        var_HEADERS = {
            'Authorization': "Bearer %s" % UMB_Investigate_token,
            }

        var_URL_CATEGORIES = "https://investigate.api.umbrella.com/domains/categorization/" + varDOMAIN
        var_LABELS = {"showLabels":""}
        var_RESPONSE_CATEGORIES = requests.request("GET", var_URL_CATEGORIES, headers=var_HEADERS, params=var_LABELS)
        if var_RESPONSE_CATEGORIES.status_code == 403 or var_RESPONSE_CATEGORIES.status_code == 500:
            return "Parece que o token do Investigate fornecido não está correto. Por favor, revise o arquivo de configuração!"
        var_OUTPUT0 = var_RESPONSE_CATEGORIES.text

        re1='.*?'       # Non-greedy match on filler
        re2='([-+]\\d+)'        # Integer Number 1
        rg = re.compile(re1+re2,re.IGNORECASE|re.DOTALL)
        m = rg.search(var_OUTPUT0)
        if m:
            sec_status = m.group(1)
        else:
            re1='.*?'   # Non-greedy match on filler
            re2='(\\d+)'        # Integer Number 1
            rg = re.compile(re1+re2,re.IGNORECASE|re.DOTALL)
            m = rg.search(var_OUTPUT0)
            sec_status = m.group(1)

        re1='.*?'       # Non-greedy match on filler
        re2='(\\[.*?\\])'       # Square Braces 1
        rg = re.compile(re1+re2,re.IGNORECASE|re.DOTALL)
        m = rg.search(var_OUTPUT0)
        sec_cat = m.group(1)

        re1='.*?'       # Non-greedy match on filler
        re2='\\[.*?\\]' # Uninteresting: sbraces
        re3='.*?'       # Non-greedy match on filler
        re4='(\\[.*?\\])'
        rg = re.compile(re1+re2+re3+re4,re.IGNORECASE|re.DOTALL)
        m = rg.search(var_OUTPUT0)
        web_cat=m.group(1)

        var_URL_RISK = "https://investigate.api.umbrella.com/domains/risk-score/" + varDOMAIN
        var_RESPONSE_RISK = requests.request("GET", var_URL_RISK , headers=var_HEADERS)
        var_OUTPUT1 = var_RESPONSE_RISK.text
        re1='.*?'
        re2='(\\d+)'
        rg = re.compile(re1+re2,re.IGNORECASE|re.DOTALL)
        m = rg.search(var_OUTPUT1)
        risk_level = m.group(1)

        f = open((log_directory+log_prefix+'-'+today+'.log'), "a")
        time.sleep(5)
        f.write(timestamp +", "+personEmail+", RoomType: " +roomType+", Room Name: "+room_title+", Answer: Security Status= " +sec_status+", Risk Level= "+risk_level+", Security_Cat= "+sec_cat+", Web_Cat= "+web_cat+'\n')


        msg = "Cisco Umbrella Investigate result for domain: <b>{}</b> >>><br/>" \
              "• Domain Security Status = <b>[ {} ]</b> (-1 = malicious, 1 = benign, 0 = not classified)<br/>" \
              "• Domain Risk Level = <b>[ {} ]</b> (0=no risk at all, 100 highest risk)<br/>" \
              "• Domain Security Categories : <b>{}</b> <br/>" \
              "• Domain Web Categories : <b>{}</b> <br/>".format(varDOMAIN, sec_status, risk_level, sec_cat, web_cat)
        return "{}".format(msg)


def umbrella_toplist(top, roomType, room_title, today, timestamp, personEmail):
        today = datetime.datetime.today()
        timestamp = today.strftime('%Y-%m-%d %H:%M:%S')
        date = datetime.date.today()
        today = date.strftime('%Y-%m-%d')
        top_int = int(top)
        if top_int > 101:
                  return "Cisco Umbrella Top domains - Global List<br/>" \
                         "Entre com um numero entre 0- 100 <br/>"
        elif top_int < 0:
                  return "Cisco Umbrella Top domains - Global List<br/>" \
                         "Entre com um numero entre 0- 100 <br/>"
        else:
            var_HEADERS = {
            'Authorization': "Bearer %s" % UMB_Investigate_token,
            }

            var_URL = "https://investigate.api.umbrella.com/topmillion?limit="+top
            get_toplist = requests.request("GET", var_URL, headers=var_HEADERS)
            if get_toplist.status_code == 403:
                return "Parece que o token do Investigate fornecido não está correto. Por favor, revise o arquivo de configuração!"
            toplist = get_toplist.text
            toplist_json = get_toplist.json()
            return "Cisco Umbrella Top {} domains - Global List<br/>" \
                   "{}<br/>".format(top, (json2html.convert(json = toplist_json)))


app = Flask(__name__)

def CheckInt(txt):
    try:
        int(txt)
        return True
    except ValueError:
        return False

@app.route('/', methods=['GET', 'POST'])
def spark_webhook():

    if request.method == 'POST':
        webhook = request.get_json(silent=True)
        #print(json.dumps(webhook, indent=4))
        today = datetime.datetime.today()
        timestamp = today.strftime('%Y-%m-%d %H:%M:%S')
        date = datetime.date.today()
        today = date.strftime('%Y-%m-%d')
        if (webhook['resource'] == "memberships") and (webhook['event'] == "created") and (webhook['data']['personEmail'] == bot_email):
            msg = ""
            msg = greetings()
            send_spark_post("https://api.ciscospark.com/v1/messages", {"roomId": webhook['data']['roomId'], "markdown": msg})
            return 'ok'
        elif ("@webex.bot" not in webhook['data']['personEmail']) and (webhook['resource'] == "messages"):
            result = send_spark_get('https://api.ciscospark.com/v1/messages/{0}'.format(webhook['data']['id']))
            roomId_query = send_spark_get('https://api.ciscospark.com/v1/rooms/{0}'.format(webhook['data']['roomId']))
            in_message = result.get('text', '').lower()
            in_message = in_message.replace(bot_name.lower().split(' ', 1)[0], '')
            check_room_id = roomId_query.get('id', '').strip()
            if check_room_id == logs_roomId:
                mensagem = in_message.strip()
                #print(mensagem)
                personEmail =  result.get('personEmail', '')
                if not personEmail:
                    sys.exit()

                roomType = result.get('roomType', '')
                room_title = roomId_query.get('title', '')
                emaildomain = personEmail.split('@')[1]
                f = open((log_directory+log_prefix+'-'+today+'.log'), "a")
                #print ("print command to log")
                f.write(timestamp +", "+personEmail+", RoomType: " +roomType+", Room Name: "+room_title+", Command: " +mensagem + '\n')
                msg = ""
                for i in webex_domain:
                    webex_email_domain = i.split(',')

                if mensagem in expected_messages and expected_messages[mensagem] == "help":
                    msg = help_me()

                elif mensagem in expected_messages and expected_messages[mensagem] == "greetings":
                    msg = greetings()


                elif emaildomain not in webex_email_domain:
                    msg = 'Desculpe, mas você não tem permissão para usar este Bot, entre em contato com {} para mais informações'.format(admin_email)

                elif mensagem.startswith("domain:"):
                    if len(mensagem) > 7:
                        domain = mensagem.lower().replace('domain:', '').strip()
                        #print("dominio:", domain)
                        msg = umbrella_get(domain, roomType, room_title, today, timestamp, personEmail)
                    else:
                        msg = 'Parâmetros faltado! Use - domain: internetbadguys.com'

                elif mensagem.startswith("domain"):
                    if len(mensagem) > 6:
                        domain = mensagem.lower().replace('domain', '').strip()
                        #print("dominio", domain)
                        msg = umbrella_get(domain, roomType, room_title, today, timestamp, personEmail)
                    else:
                        msg = 'Parâmetros faltado! Use - domain internetbadguys.com'

                elif mensagem.startswith("toplist"):
                    if len(mensagem) > 7:
                        top = mensagem.split(' ')[1].lower()
                        if CheckInt(top) == True:
                            msg = umbrella_toplist(top, roomType, room_title, today, timestamp, personEmail)
                        else:
                            msg = 'Digite somente números como parâmetro para fazer essa requisição'
                    else:
                        msg = 'Parâmetros faltado! Use - toplist XX'

                elif mensagem.startswith("top"):
                    if len(mensagem) > 3:
                        top = mensagem.split(' ')[1].lower()
                        if CheckInt(top) == True:
                            msg = umbrella_toplist(top, roomType, room_title, today, timestamp, personEmail)
                        else:
                            msg = 'Digite somente números como parâmetro para fazer essa requisição'
                    else:
                        msg = 'Parâmetros faltado! Use - top XX'
                elif mensagem == "threats":
                    access_token = get_access_token()

                    if code_access_token == 403 or code_access_token == 401:
                        msg = "Parece que a Management Key ou Management Secret fornecido não está correto. Por favor, revise o arquivo de configuração!"
                    elif code_access_token == 200:
                        querystring = 'from=-30days&to=now&limit=100'
                        r = get_reporting_request(access_token, '/organizations/{}/top-threat-types?{}'.format(org_id, querystring ))
                        threats = []
                        result = ""
                        for i in r['data']:
                            threats.append("Threat Type: " + i['threattype'] + ", Count: " + str(i['threatscount']))
                        for res in threats:
                            result += res + '\n'
                        msg = topthreats(result)
                elif mensagem == "total":
                    access_token = get_access_token()

                    if code_access_token == 403 or code_access_token == 401:
                        msg = "Parece que a Management Key ou Management Secret fornecido não está correto. Por favor, revise o arquivo de configuração!"
                    elif code_access_token == 200:
                        querystring = 'from=-30days&to=now'
                        r = get_reporting_request(access_token, '/organizations/{}/total-requests?{}'.format(org_id, querystring ))

                        total = r['data']['count']
                        msg=totalrequests(total)
                elif mensagem == "summary" or mensagem == "summ":
                    access_token = get_access_token()

                    if code_access_token == 403 or code_access_token == 401:
                        msg = "Parece que a Management Key ou Management Secret fornecido não está correto. Por favor, revise o arquivo de configuração!"
                    elif code_access_token == 200:
                        querystring = 'from=-30days&to=now&limit=5000'
                        r = get_reporting_request(access_token, '/organizations/{}/summary?{}'.format(org_id, querystring ))
                        log_summary = ""
                        for key, value_subdic in r.items():
                            for data_subkey, value in value_subdic.items():
                                log_summary += data_subkey.capitalize() + ": " + str(value) + "\n"
                        msg=summary(log_summary)
                else:
                    msg = "Desculpe, mas não entendi sua solicitação. Digite `ajuda` para ver o que consigo fazer"

                if msg is not None:
                    send_spark_post("https://api.ciscospark.com/v1/messages", {"roomId": webhook['data']['roomId'], "markdown": msg})
                    """log = (timestamp+", "+personEmail+", RoomType: " +roomType+", Room Name: "+room_title+', Command: '+mensagem)
                    anwser = ("Anwser : <br/>" \
                  "{}".format(msg))"""
                    #send_spark_post("https://api.ciscospark.com/v1/messages", {"roomId": logs_roomId, "text": log})
                    #send_spark_post("https://api.ciscospark.com/v1/messages", {"roomId": logs_roomId, "markdown": anwser})

        return "true"
    elif request.method == 'GET':
        message = "<center><img src=\"https://cdn-images-1.medium.com/max/800/1*wrYQF1qZ3GePyrVn-Sp0UQ.png\" alt=\"Spark Bot\" style=\"width:256; height:256;\"</center>" \
                  "<center><h2><b>Congratulations! Your <i style=\"color:#ff8000;\">%s</i> bot is up and running.</b></h2></center>" \
                  "<center><b><i>Don't forget to create Webhooks to start receiving events from Cisco Spark!</i></b></center>" % bot_name
        return message

def main():
    global bot_email, bot_name
    if len(bearer) != 0:
        test_auth = send_spark_get("https://api.ciscospark.com/v1/people/me", js=False)
        if test_auth.status_code == 401:
            print("Parece que o token de acesso fornecido não está correto.\n"
                  "Revise o arquivo de configuração e certifique-se de que o bot pertence à sua conta.\n"
                  "Não se preocupe se você perdeu o token de acesso. "
                  "Você sempre pode ir à URL https://developer.ciscospark.com/apps.html "
                  "e gerar um token de acesso novo.")
            sys.exit()
        if test_auth.status_code == 200:
            test_auth = test_auth.json()
            bot_name = test_auth.get("displayName", "")
            bot_email = test_auth.get("emails", "")[0]
    else:
        print("'Access Token do Bot' no arquivo de configuração está vazio! \n"
              "Preencha-o com o token de acesso do bot e execute o script novamente.\n"
              "Não se preocupe se você perdeu o token de acesso. "
              "Você sempre pode ir à URL to https://developer.ciscospark.com/apps.html "
              "e gerar um token de acesso novo.")
        sys.exit()

    if "@webex.bot" not in bot_email:
        print("Você forneceu um token de acesso que não está relacionado a um bot.\n"
              "Por favor mude para um token de Bot válido e confirme se pertence à sua conta.\n"
              "Não se preocupe se você perdeu o token de acesso. "
              "Você sempre pode ir à URL https://developer.ciscospark.com/apps.html "
              "e gerar um token de acesso novo para seu Bot.")
        sys.exit()
    else:
        app.run(host='0.0.0.0', port= webhook_port)
    return "ok"

if __name__ == "__main__":
    main()
