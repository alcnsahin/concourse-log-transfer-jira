#!/usr/bin/python

import os
import urllib
import urllib2
import cookielib
import json
import base64

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))


def get_cookie(cookie_name):
    cookie_value = None
    i = 0
    for c in cj:
        if cookie_name == c.name:
            if i == 0:
                print(c.name + " = " + c.value)
                cookie_value = c.value
                i += 1
            else:
                break
    return cookie_value


def dump_cookies():
    for c in cj:
        print(c.name + " = " + c.value)


def get_header(response, header_name):
    header_value = None
    for h in response.headers:
        if h.find(header_name) > -1:
            header_value = h
    return header_value


def dump_headers(response):
    for h in response.headers:
        print(h)


def base64encoder(text):
    return base64.b64encode(text)


# parameters
USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20'
PIPELINE_NAME = os.environ['PIPELINE_NAME']
JOB_NAME = os.environ['JOB_NAME']
CONCOURSE_ROOT_URL = os.environ['CONCOURSE_ROOT_PATH']
UAA_ROOT_URL = os.environ['UAA_ROOT_PATH']
UAA_USERNAME = os.environ['UAA_USERNAME']
UAA_PASSWORD = os.environ['UAA_PASSWORD']
CONSUL_ROOT_URL = os.environ['CONSUL_ROOT_PATH']
JIRA_ROOT_URL = os.environ['JIRA_ROOT_PATH']
JIRA_USERNAME = os.environ['JIRA_USERNAME']
JIRA_PASSWORD = os.environ['JIRA_PASSWORD']
JIRA_ENCRYPTED_PASS = "Basic" + base64encoder(JIRA_USERNAME+":"+JIRA_PASSWORD)

# get bearer token (step 1)
opener.addheaders.append(('Accept', 'application/json'))
opener.addheaders.append(('User-Agent', USER_AGENT))
resp = opener.open(CONCOURSE_ROOT_URL + "/auth/oauth?team_name=main")
concourse_state = get_cookie("_concourse_oauth_state").replace("_concourse_oauth_state = ", "")

# UAA LOGIN GET  (step 2)
uaa_resp = opener.open(UAA_ROOT_URL + "/login")
csrf_token = get_cookie("X-Uaa-Csrf").replace("X-Uaa-Csrf = ", "")

# UAA LOGIN.DO POST  (step 3)
login_data = urllib.urlencode({'username': UAA_USERNAME, 'password': UAA_PASSWORD, 'X-Uaa-Csrf': csrf_token})
uaa_resp = opener.open(UAA_ROOT_URL + "/login.do", data=login_data)
bearer_token = uaa_resp.read()
# print(bearer_token)

# GET Consul Result
consul = opener.open(CONSUL_ROOT_URL + "/" + PIPELINE_NAME + "/" + JOB_NAME)
consul_response = consul.read()
consul_json_array = json.loads(consul_response)
consul_value = base64.b64decode(consul_json_array[0]['Value'])  # decode consul value

jira_issue_id, build_id = consul_value.split("#")  # parse jira_id & build_id
print("issue_id: " + jira_issue_id)
print("build_id: " + build_id)

# get job status from concourse
opener.addheaders.append(('Authorization', bearer_token.rstrip()))
build_result = opener.open(CONCOURSE_ROOT_URL + "/api/v1/builds/" + build_id)
build_json_object = json.loads(build_result.read())
job_status = build_json_object["status"]
# print(job_status)

# jira comment
jbs = "JobStatus=" + job_status
comment = {'body': jbs}
print(comment)
jira_req = urllib2.Request(JIRA_ROOT_URL + "/rest/api/2/issue/" + jira_issue_id + "/comment")
jira_req.add_header('Content-Type', 'application/json')
jira_req.add_header('Authorization', JIRA_ENCRYPTED_PASS)
jira_response = urllib2.urlopen(jira_req, json.dumps(comment))
print(jira_response.getcode())
