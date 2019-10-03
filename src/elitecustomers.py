import csv
from jira import JIRA
import sys
import pprint

JIRA_SITE='http://jira.lawson.com'            

def readURL(url):
    opener = urllib.request.FancyURLopener({})
    f = opener.open(url)
    output = f.read()
    f.close()
    return output

def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def hasUpgrading(labels):
    for label in labels:
        if label == "ELITECUSTOMER":
            return True
    return False

#MAIN METHOD============================================================
with open('eliteids.txt') as f:
    ids = f.read().splitlines()

authed_jira = JIRA(JIRA_SITE, basic_auth=('testertim', 'Password1'))
totalcount = 0;

for idset in list(chunks(ids, 25)):
    querystring = "project=LSF AND type=Bug AND 'Reported By Customer'='true' AND component in (Portal, 'Lawson S3 for Workspace', 'Design Studio', IOS, Environment, LID, MOA, Database) AND status in (Open, Accepted, 'Awaiting Reply') AND ("
    for id in idset:
        if id != "":
            customerquery = "(id in customerIssues(XC-%s)) OR " % id
            querystring += customerquery
            
    querystring = querystring[:len(querystring)-3] + ")"
    
    print(querystring)      

    issues = authed_jira.search_issues(querystring)
    totalcount += len(issues)

    for issue in issues:
        issuedata = authed_jira.issue(issue)
        if not hasUpgrading(issuedata.fields.labels):
            print("Adding elite label to %s" % issue)            
            labels = issuedata.fields.labels
            labels.append("ELITECUSTOMER")
            issue.update(fields={"labels": labels})            
        else:
            print("%s already has elite label" % issue)
                    
    #for issue in issues:
    #    print(issue)
print("Total elite count: %d" % totalcount)
sys.exit(0)