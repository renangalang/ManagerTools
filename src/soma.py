from datetime import datetime, timezone
from dateutil import rrule
import os
import io
import csv
from jira import JIRA
import sys
import pprint
import smtplib
import pytz

JIRA_SITE='http://jira.lawson.com'

authed_jira = JIRA(JIRA_SITE, basic_auth=('testertim', 'Password1'))

lsfdevqa = "(eapostol,dennisc,vamercado, msantos, kmatel, asocias, ccatindig, vjramos, kadelcastillo, rperez2, amagno1, jrey1, pdtomias, lfiguerres, jmaglalang, nlorena, rgutierrez, rbunag, jverzosa, renang, armandoa, larinat, cmarcelo, mcyusing,gnavarro, ratienza)"
lsfdev = "(eapostol,dennisc,vamercado, msantos, kmatel, asocias, ccatindig, vjramos, kadelcastillo, rperez2, amagno1, jrey1, pdtomias, lfiguerres, jmaglalang, nlorena, rgutierrez, rbunag, jverzosa, rgalang)"

corequery = 'project=LSF and issuetype=Bug and "Reported By Customer"="false" and component != Security and resolutiondate >= startOfMonth("%s") and resolutiondate <= endOfMonth("%s")'
taskquery = 'project=LSF and issuetype=Task and (labels = Support_Triage or component = support_triage) and component != Security and resolutiondate >= startOfMonth("%s") and resolutiondate <= endOfMonth("%s")'

header=""
issuerow=""
taskrow=""
for i in range(-13, -1):

    querystring = corequery % (i,i)
    querystring = querystring + "and assignee in " + lsfdevqa 
    
    issues = authed_jira.search_issues(querystring)
    
    month=""
    if len(issues) > 0:                
        rdate = datetime.strptime(issues[0].fields.resolutiondate,"%Y-%m-%dT%H:%M:%S.%f%z")
        month = rdate.strftime("%B %Y")
            
    header+=month+","
    issuerow+=str(len(issues))+","    

    taskquerystring = taskquery % (i,i)
    taskquerystring = taskquerystring + "and assignee in " + lsfdevqa    
    tasks =  authed_jira.search_issues(taskquerystring)
    taskrow+=str(len(tasks))+","
    
    print(month+":"+str(len(issues))+","+str(len(tasks)))

print(header)
print(issuerow)
print(taskrow)