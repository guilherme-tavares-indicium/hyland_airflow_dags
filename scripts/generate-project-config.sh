if [ -z "${BITBUCKET_REPO_SLUG}" ]; then
    echo "BITBUCKET_REPO_SLUG is not set. "
    BITBUCKET_REPO_SLUG=$(git config --get remote.origin.url | sed -E 's/.*\/(.*)\.git/\1/')
fi
if [ "${BITBUCKET_REPO_SLUG}" != "airflow-dags-base" ]; then
    echo "This script only runs from a branch in the airflow-dags-base repository."
    exit 0
fi
ENV="prod"
REGION="us-east-1"
AWS_ACCOUNT_ID="196029031078"
IMAGE_NAME="${ENV}-airflow-${PROFILE}"

# Generate the project_config.sh file in the $BITBUCKET_CLONE_DIR directory
cat << EOF > $BITBUCKET_CLONE_DIR/project_conf.sh
export ENV="${ENV}"
export REGION="${REGION}"
export PROFILE="${PROFILE}"
export IMAGE_NAME="${IMAGE_NAME}"
export AWS_BITBUCKET_PIPELINE_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/indiciumtech-aws_base_cloud_project"
EOF
