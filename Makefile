.PHONY: odoo-up dev-up dev-all odoo-down

odoo-up:
	./scripts/test_odoo_integration.sh

dev-up:
	./scripts/dev_up.sh

dev-all:
	RUN_BACKEND=1 RUN_BOT=1 ODOO_ENABLED=true ./scripts/dev_up.sh

odoo-down:
	docker compose down
