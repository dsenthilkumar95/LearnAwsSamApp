ENVIRONMENT ?= dev
RUN_ENV_VARS ?= run-env-vars.json

define ci_cts_steps_docker
    docker run --rm -it \
        -v "/var/run/docker.sock:/var/run/docker.sock" \
        -v "$(PWD):/root/app" \
        -v "$(HOME)/.aws:/root/.aws" \
        -v "$(HOME)/.ssh:/root/.ssh" \
        -e OWNER_USER=$(shell id -u) \
        -e OWNER_GROUP=$(shell id -g) $(3)\
        -p 3000:3000 \
        -w /root/app$(2) \
        ocs-lambdas-sam $(1)
endef

Init:
	python3 -m venv .venv
	. .venv/bin/activate
	docker build -t ocs-lambdas-sam .

Clean:
	docker system prune -f
	rm -rf 	lambda_layers/python/*
	rm -rf 	lambda_layers/*.zip
	rm -rf 	.venv .aws-sam

Build:
	$(call ci_cts_steps_docker, pip3 install  --upgrade -r requirements.txt -t .venv/lib/python3.7/site-packages \
	    --no-warn-conflicts )
	$(call ci_cts_steps_docker, pip3 install  --upgrade -r requirements-test.txt -t .venv/lib/python3.7/site-packages \
	    --no-warn-conflicts )
	$(call ci_cts_steps_docker, pip3 install  -r requirements.txt -t lambda_layers/python \
	    --no-warn-conflicts )
	$(call ci_cts_steps_docker, python3 templates/resolve_template.py)
	$(call ci_cts_steps_docker, sam build -m requirements.txt -t template.yml --profile saml --region eu-west-2)

Package:
	cd ./lambda_layers && zip -r lambdas-sam.zip python
	mkdir -p .aws-sam/lambda_layers && cp ./lambda_layers/lambdas-sam.zip .aws-sam/lambda_layers

Run:
	export SAM_CLI_TELEMETRY=0 && sam local invoke ${LAMBDA2RUN} -v .aws-sam/build --profile saml \
	    --region eu-west-2 --env-vars ${RUN_ENV_VARS} --debug --force-image-build \

Deploy:
	$(call ci_cts_steps_docker, sam validate  -t template.yml --profile saml --region eu-west-2 )
	$(call ci_cts_steps_docker, sam package --s3-bucket ocs-lambdas-sam --profile saml --region eu-west-2 \
		--template-file template.yml --output-template-file .aws-sam/package.yml.OUT )
	$(call ci_cts_steps_docker, sam deploy --profile saml --template-file .aws-sam/package.yml.OUT \
		--capabilities CAPABILITY_IAM \
		--stack-name ocs-lambdas-sam-${ENVIRONMENT} --region eu-west-2 \
		--parameter-overrides "Environment=${ENVIRONMENT}" "MPXPassword=${MPX_PASSWORD}" \
			$(shell jq -r '.Parameters[] | [.ParameterKey, .ParameterValue] | "\"\(.[0])=\\\"\(.[1])\\\"\""' conf/${ENVIRONMENT}.json) )

IntegrationTests:
	$(call ci_cts_steps_docker, coverage run -m unittest discover -v,/tests,\
		-e PYTHONPATH=/root/app/.venv/lib/python3.7/site-packages:/root/app/lambda_layers/custom:/root/app)
	$(call ci_cts_steps_docker, coverage html,/tests,\
    	-e PYTHONPATH=/root/app/.venv/lib/python3.7/site-packages:/root/app/lambda_layers/custom:/root/app)
	echo "==========================================================="
	echo "Execute 'open tests/htmlcov/index.html' to see the coverage"
