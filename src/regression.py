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

startdate="'2018/5/1'"
enddate="'2019/4/30'"

corequery = 'project=LSF and issueType=Bug and createdDate >= %s and createdDate < %s '

querystring = corequery % (startdate,enddate)
issues = authed_jira.search_issues(querystring,maxResults=1000)

count=1
for issue in issues:
    #print("Checking %s of %s" % (count, len(issues)))    
    if len(issue.fields.issuelinks) > 0:
        for link in issue.fields.issuelinks:
            if link.type.id == "10060":
                if hasattr(link, 'outwardIssue') and link.outwardIssue.fields.issuetype.name != "Task":
                    linkdata = authed_jira.issue(link.outwardIssue.key)
                    print("%s,%s,%s" % (linkdata.key,linkdata.fields.assignee.displayName,linkdata.fields.summary))
    count+=1
                