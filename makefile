# Makefile
# Place this in the root of your FYP_BACKEND project.

.PHONY: run-whatsapp run-crud run-media-gen run-instagram run-scheduler run-all

run-whatsapp:
	@echo "Running whatsapp/app.py..."
	python whatsapp/app.py

run-crud:
	@echo "Running crud/app.py..."
	python crud/app.py

run-media-gen:
	@echo "Running media_gen/app.py..."
	python media_gen/app.py

run-instagram:
	@echo "Running instagram/app.py..."
	python instagram/app.py

run-scheduler:
	@echo "Running scheduler/app.py..."
	python scheduler/app.py

# This target will run all your services in parallel (background),
# then 'wait' will keep the terminal open until you stop them.
run-all:
	@echo "Running all Python services..."
	python whatsapp/app.py &
	python crud/app.py &
	python media_gen/app.py &
	python instagram/app.py &
	python scheduler/app.py &
	wait
