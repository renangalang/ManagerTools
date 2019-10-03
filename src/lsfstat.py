from jira import JIRA,JIRAError
from string import Template
import datetime
from datetime import timedelta
import pprint
import smtplib
from urllib.parse import quote

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sender = "renan.galang@infor.com"

HTML_HEADER="""
<html>    
<head>
<style>
a {
    text-decoration:none;
}

body { 
    background: #fff; 
    font-family: Arial,sans-serif;
    color: #333;     
}

table {
    border-spacing: 0; 
    border-collapse: collapse; 
    box-sizing: border-box; 
}

p {
    line-height: 1em;
    font-size: 1.3em;    
    margin: 0;
    color: #59c7fb;
}

th, td { 
    font-size: .9em;
    line-height: 1.45; 
    color: #444; 
    vertical-align: middle; 
    padding: .75em; 
    text-align: center;
    border: 1px solid #ccc; 
    border-width: 1px;
}

th { 
    font-weight: 600; 
    text-align: right;
    border-width: 0;
}

tr:nth-child(even) { 
    background: #f5f5f5; 
}

li {
    font-size: .75em;     
}
</style>
</head>
<body>    
<p>Triage Tickets</p>
<table>
<tr><th></th><th>Backlog</th><th>Influx</th><th>Resolved</th></tr>
$task
</table>
<br>
<p>Bug Tickets (External)<p>
<table>
<tr><th></th><th>Backlog</th><th>Influx</th><th>Resolved</th></tr>
$bug
</table>
<ul>
<li>Week is from Monday to Sunday, inclusive</li>
<li>Some backlog variances due to ticket transfer between projects/teams</li>
<li>Backlog count is taken at the end of the week (Sunday)</li>
<li>Includes only Portal, Lawson S3 for Workspace, Design Studio, IOS, MOA, LID, Database and Environment</li> 
<li>Issue data is pulled using GMT+8 time zone</li>
</ul>
</body></html>"""   

class BIRRepo(object):
        
    def __init__(self):
        self.backlog=()     
        self.backlogurl=""
        self.influx=()
        self.influxurl=""
        self.resolved=() 
        self.resolvedurl="" 
    
    def setInflux(self, influx, url):
        self.influx = influx
        self.influxurl = url
        
    def setBacklog(self, backlog, url):
        self.backlog = backlog
        self.backlogurl = url
        
    def setResolved(self, resolved, url):
        self.resolved = resolved
        self.resolvedurl = url
        
    def getInflux(self):
        return self.influx
    
    def getBacklog(self):
        return self.backlog
    
    def getResolved(self):
        return self.resolved
    
    def getInfluxURL(self):
        return "http://jira.lawson.com/issues/?jql=%s" % quote(self.influxurl)
    
    def getBacklogURL(self):        
        return "http://jira.lawson.com/issues/?jql=%s" % quote(self.backlogurl)
    
    def getResolvedURL(self):        
        return "http://jira.lawson.com/issues/?jql=%s" % quote(self.resolvedurl)


login='testertim'
pword='Password1'
JIRASITE="http://jira.lawson.com"
AUTHED_JIRA = None
TASKFILTER= " AND (component=Support_Triage OR labels=Support_Triage) "
BUGFILTER = " AND 'Reported By Customer'='true'"
TASKISSUETYPE="Task"
BUGISSUETYPE="Bug"

BACKLOG_STRING = 'project=LSF and issuetype=%s and component in (IOS,Environment,LID,Database,MOA,Portal,"Lawson S3 for Workspace","Design Studio") and createdDate <= "%s" and (resolutionDate > %s OR resolution=Unresolved ) %s'
INFLUX_STRING = 'project=LSF and issuetype=%s and component in (IOS,Environment,LID,Database,MOA,Portal,"Lawson S3 for Workspace","Design Studio") and createdDate >= "%s" and createdDate <= "%s" %s'
RESOLVED_STRING = 'project=LSF and issuetype=%s and component in (IOS,Environment,LID,Database,MOA,Portal,"Lawson S3 for Workspace","Design Studio") and resolutionDate >= "%s" and resolutionDate <= "%s" %s'

AUTHED_JIRA = JIRA(JIRASITE, basic_auth=(login,pword))
WEEK_COUNT=3

def hasComponent(components, cmps):
    for component in components:
        for cmp in cmps:
            if component.name == cmp:
                return True
    return False

def breakdownTotal(issues):
    
    envcount=0
    moacount=0
    portalcount=0
    for issue in issues:
        if hasComponent(issue.fields.components, ["Lawson S3 for Workspace", "Portal","IOS", "Design Studio"]):
            portalcount+=1
        elif hasComponent(issue.fields.components, ["Environment","Database", "LID"]):
            envcount+=1
        elif hasComponent(issue.fields.components, ["MOA"]):
            moacount+=1
    
    return (envcount,portalcount,moacount)

def getTotals(weekstart, weekend, issuetype, filter):    
    data = BIRRepo()
    
    #we use the end of the week as creation date as we want to capture all the tickets created during the week too
    qstring = BACKLOG_STRING % (issuetype, weekend, weekend, filter )
    print(qstring)
    issues = AUTHED_JIRA.search_issues(qstring)
    print(len(issues))    
    data.setBacklog(breakdownTotal(issues), qstring)
    
    qstring = INFLUX_STRING % (issuetype, weekstart, weekend, filter )
    print(qstring)
    issues = AUTHED_JIRA.search_issues(qstring)
    print(len(issues))
    data.setInflux(breakdownTotal(issues), qstring)

    qstring = RESOLVED_STRING % (issuetype, weekstart, weekend, filter )
    print(qstring)
    issues = AUTHED_JIRA.search_issues(qstring)
    print(len(issues))
    data.setResolved(breakdownTotal(issues), qstring)
    
    return data

def buildBreakdownString(envcount,portalcount,moacount):
    
    html = "%s (Env=%s, Web=%s, MOA=%s)" % (int(envcount+portalcount+moacount), int(envcount), int(portalcount), int (moacount))
    
    return html

def buildTable(issueType, filter):
    htmlstring = ""
    #triage
    for counter in range(0,WEEK_COUNT):
        dt = datetime.date.today()
        startofthisweek = dt - timedelta(days=dt.weekday())
        
        weekstart = startofthisweek - timedelta(days=7*(counter+1))
        weekend = startofthisweek - timedelta(days=(counter*7)+1)
            
        data = getTotals(weekstart, weekend, issueType,filter )
        
        label="Last Week"
        if counter > 0:
            label = "%s weeks ago" % str(counter+1)
        
        htmlstring = htmlstring + "<tr><th>%s</th><td><a href='%s'>%s</a></td><td><a href='%s'>%s</a></td><td><a href='%s'>%s</a></td>" % \
        ( label, 
          data.getBacklogURL(),
          buildBreakdownString(*data.getBacklog()),
          data.getInfluxURL(), 
          buildBreakdownString(*data.getInflux()),
          data.getResolvedURL(), 
          buildBreakdownString(*data.getResolved()))
    
    return htmlstring

taskhtml = buildTable(TASKISSUETYPE, TASKFILTER)
bughtml = buildTable(BUGISSUETYPE, BUGFILTER)

htmloutput = Template(HTML_HEADER).substitute(
    task = taskhtml,
    bug = bughtml)

cclist = "renan.galang@infor.com,gentley.escalante@infor.com"
#rcpts = "renan.galang@infor.com"
rcpts =  ["armando.aspiras@infor.com","krizelle.matel@infor.com","richard.perez@infor.com","rommel.gutierrez@infor.com","arianne.socias@infor.com","renan.galang@infor.com","gentley.escalante@infor.com"]

msg = MIMEMultipart('alternative')
msg['Subject'] = "LSF Tickets Weekly Summary for %s" % datetime.date.today().strftime("%Y-%m-%d")        
msg['To'] = ", ".join(rcpts)        
msg['Cc'] = cclist
  
htmlpart = MIMEText(htmloutput, 'html')
msg.attach(htmlpart)
  
s = smtplib.SMTP('smtp-relay.infor.com')
s.sendmail(sender, rcpts, msg.as_string())        
print("Email sent") 
   
try:
    text_file = open("output.html", "w")
    text_file.write(htmloutput)
finally:
    text_file.close()    
