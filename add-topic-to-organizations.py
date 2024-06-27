
#
# Add a given topic to every repo in one or more organizations
#
# A one-shot script that may be useful to me or others in the future, but not published with larger ambitions

import httpx
import json
import logging
import os
import re
import sys

def enable_logging():
  logging.basicConfig(
      format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
      datefmt="%Y-%m-%d %H:%M:%S",
      level=logging.DEBUG
  )  

def get_request_headers():
  token = os.environ['GITHUB_TOKEN']
  # fixme: exception if not set ^
  request_headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": "Bearer "+token,
    "X-GitHub-Api-Version": "2022-11-28"
  }
  return(request_headers)

def add_label(org,repo,label):

  resource = "https://api.github.com/repos/"+org+"/"+repo+"/topics"

  #*** Get current state of labels

  # leaving exception for the parent
  response_body = httpx.get(resource, headers=get_request_headers(),timeout=10.0)

  try:
    labels=response_body.json()
  except Exception:
    raise("FAIL: response for URL is not JSON\nURL: %s\nResponse body: \n%s" % (resource,response_body))
  tmp=labels["names"]

  if label in tmp:
    return

  #*** Save updated label set

  tmp.append(label)
  labels["names"] = tmp
  new_data = json.dumps(labels)
  r = httpx.put(resource, headers=get_request_headers(), data=new_data,timeout=10.0)


def list_repos(org):

  request_headers = get_request_headers()

  # does not work. fix later.
  # request_headers["per_page"] = "100"  
  #print(request_headers)

  repos = []
  page = 1

  page_link = "https://api.github.com/orgs/"+org+"/"+"repos?page="+str(page)+"&per_page=100"
  while True:
    print("Fetching "+page_link)

    response_body = httpx.get( page_link, headers=request_headers,timeout=10.0 )

    for repo in response_body.json():
      repos.append(repo['name'])

    if "link" in response_body.headers:
      link_header = response_body.headers['link']
      if not re.search(r'; rel="next"', link_header):
        return(repos)

      next_link = re.sub(r'.*<(.*)>; rel="next".*', r'\1', link_header)
      if( next_link == page_link ):
        return(repos)

      page_link = next_link
    else:
      return(repos)


def iterate_orgs(orgs,label):
  for org in orgs:
    print("Org: " +org)
    repos = list_repos(org)
    print("Repo count: %s" % str(len(repos)))

    for repo in repos:
      add_label(org,repo,label)

# *** MAIN

if( len(sys.argv) < 3 ):
  print("Usage: label org1 .. orgN")
  sys.exit(0)

enable_logging()
iterate_orgs(sys.argv[2:],sys.argv[1])
