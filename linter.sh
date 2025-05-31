#!/bin/bash
# curl (REST API)
# Assuming "anonymous read access" has been enabled on your Jenkins instance.

# Manfully run
# sh linter.sh path/to/Jenkinsfile
#
# Need input your Jenkins login username and token below.

# : "${JENKINS_USER:?Missing JENKINS_USER}"
# : "${JENKINS_TOKEN:?Missing JENKINS_TOKEN}"
# : "${JENKINS_URL:?Missing JENKINS_URL}"

if [ -z ${JENKINS_USER} ] || [ -z ${JENKINS_TOKEN} ] || [ -z ${JENKINS_URL} ]; then
    echo "Missing environment variables. Please set JENKINS_USER, JENKINS_TOKEN, and JENKINS_URL."
    exit 1
fi

PWD=`pwd`
JENKINS_FILE=$1

# JENKINS_CRUMB is needed if your Jenkins master has CRSF protection enabled as it should
# JENKINS_CRUMB=`curl "$JENKINS_URL/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,\":\",//crumb)"`
# curl -X POST -H $JENKINS_CRUMB -F "jenkinsfile=<Jenkinsfile" $JENKINS_URL/pipeline-model-converter/validate
result=$(curl --user $JENKINS_USER:$JENKINS_TOKEN -sX POST -F "jenkinsfile=<$PWD/$JENKINS_FILE" $JENKINS_URL/pipeline-model-converter/validate)

if [[ $result =~ Errors ]]; then
    echo "$result"
    exit 1
else
    echo "$result"
    exit 0
fi
