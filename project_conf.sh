# IMAGE VARIABLES
export ENV="prod"
export AWS_ACCOUNT_ID="046390580407"
export REGION="us-east-1"
export PROFILE="hyland_base_infra"
export INFRA_REPO_SLUG="${BITBUCKET_BRANCH}"
export INFRA_REPO_WORKSPACE="${BITBUCKET_WORKSPACE}"
export IMAGE_NAME="${ENV}-airflow-hyland-base-infra"
export AWS_BITBUCKET_PIPELINE_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/indiciumtech-hyland_base_infra"
