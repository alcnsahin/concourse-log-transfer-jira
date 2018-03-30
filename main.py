#!/usr/bin/python

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
    return base64.b16encode(text)


# params
pipeline_name = "PIPELINE_NAME"
job_name = "JOB_NAME"
concourse_root_path = "CONCOURSE_ROOT_PATH"
uaa_root_path = "UAA_ROOT_PATH"
consul_root_path = "CONSUL_ROOT_PATH"
jira_root_path = "JIRA_ROOT_PATH"

# get bearer token
opener.addheaders.append(('Accept', 'application/json'))
opener.addheaders.append(('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20'))
resp = opener.open(concourse_root_path + "/auth/oauth?team_name=main")
concourse_state = get_cookie("_concourse_oauth_state").replace("_concourse_oauth_state = ", "")

print("#UAA LOGIN GET#")
uaa_resp = opener.open(uaa_root_path + "/login")
csrf_token = get_cookie("X-Uaa-Csrf").replace("X-Uaa-Csrf = ", "")

print("#UAA LOGIN.DO POST#")
login_data = urllib.urlencode({'username': 'UAA_USERNAME', 'password': 'UAA_PASSWORD', 'X-Uaa-Csrf': csrf_token})
uaa_resp = opener.open(uaa_root_path + "/login.do", data=login_data)
bearer_token = uaa_resp.read()
print(bearer_token)

print("#GET Consul Result#")
consul = opener.open(consul_root_path + "/" + pipeline_name + "/" + job_name)
consul_response = consul.read()
consul_json_array = json.loads(consul_response)
consul_value = base64.b64decode(consul_json_array[0]['Value'])  # decode consul value

jira_issue_id, build_id = consul_value.split("#")  # parse jira_id & build_id
print("issue_id: " + jira_issue_id)
print("build_id: " + build_id)

# get job status from concourse
opener.addheaders.append(('Authorization', bearer_token.rstrip()))
build_result = opener.open(concourse_root_path + "/api/v1/builds/" + build_id)
build_json_object = json.loads(build_result.read())
job_status = build_json_object["status"]
print(job_status)

# jira comment
comment = {"body":  "Status: " + job_status}
encrypted_pass = "Basic " + base64encoder("JIRA_USERNAME:JIRA_PASSWORD")
opener.addheaders.append(("Authorization", encrypted_pass))
jira = opener.open(jira_root_path + "/rest/api/2/issue/" + jira_issue_id + "/comment")
jira_result = jira.read()
print(jira_result)
