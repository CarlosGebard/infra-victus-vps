.PHONY: bootstrap bootstrap-check bootstrap-debug bootstrap-from verify-bootstrap validate-bootstrap validate-runtime

bootstrap:
	python3 ./ops/scripts/bootstrap_via_infisical.py --verbosity=-vv

bootstrap-check:
	python3 ./ops/scripts/bootstrap_via_infisical.py --verbosity=-vv --check

bootstrap-debug:
	python3 ./ops/scripts/bootstrap_via_infisical.py --verbosity=-vvv

bootstrap-from:
	@if [ -z "$(TASK)" ]; then echo 'Usage: make bootstrap-from TASK="Task Name"'; exit 1; fi
	python3 ./ops/scripts/bootstrap_via_infisical.py --verbosity=-vvv --start-at-task "$(TASK)"

verify-bootstrap:
	python3 ./ops/scripts/verify_bootstrap_via_infisical.py --verbosity=-vv

validate-bootstrap:
	cd ansible && ANSIBLE_LOCAL_TEMP=/tmp/.ansible-local ansible-playbook -i inventories/production/syntax-check.yml bootstrap/playbooks/bootstrap.yml --syntax-check

validate-runtime:
	cd ansible && ANSIBLE_LOCAL_TEMP=/tmp/.ansible-local ansible-playbook -i inventories/production/syntax-check.yml runtime/playbooks/deploy-core.yml --syntax-check && ANSIBLE_LOCAL_TEMP=/tmp/.ansible-local ansible-playbook -i inventories/production/syntax-check.yml runtime/playbooks/validate-core-runtime.yml --syntax-check
