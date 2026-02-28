# Wireless Test Automation Framework

A Python-based asynchronous test automation framework mimicking an Apple Lab Execution Layer. 
This repository demonstrates executing tests concurrently on physical devices while maintaining a robust state through PostgreSQL and MongoDB natively.

## Project Structure
- `main.py`: Orchestrates the framework. Creates fictitious iPhone devices, pairs them with 3 concurrent test suites, and coordinates test runs.
- `test_runner.py`: Abstract Async Test Runner implementing Python's `asyncio.gather()` to launch 30 hardware-mocked tests simultaneously without GIL locking.
- `database.py`: Clean connection interfaces utilizing `psycopg2` for PostgreSQL schema management and `pymongo` for raw Document logging.
- `docker-compose.yml`: Spins up local PostgreSQL (`5432`) and MongoDB (`27017`) instances.
- `.github/workflows/ci.yml`: A CI/CD Action pipeline executing the entire end-to-end framework dynamically upon pull request or push.

## How to Run Locally

### 1. Start the Databases
In a new terminal, launch the required databases using Docker:
```bash
docker compose up -d
```
*Wait a few seconds for the databases to initialize.*

### 2. Setup your Python Environment
Because macOS natively restricts `pip install` modifications, it is safest to create a localized virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Framework
```bash
python main.py
```
You will see 30 tests concurrently dispatch, log to Postgres/Mongo, and complete!

### 4. Open the Data Visualization Dashboard
The framework includes a real-time data visualization dashboard explicitly designed for stakeholder communication (using Streamlit and Plotly). To view live tests:
```bash
source venv/bin/activate
streamlit run dashboard.py
```
This will open a browser window displaying test metrics, durations, and live pass/fail pie charts pulling straight from PostgreSQL!

## How the CI/CD Pipeline Works
This framework natively includes a GitHub Actions pipeline located in `.github/workflows/ci.yml`.
Whenever you push your code to the `main` branch, a fresh Ubuntu runner will:
1. Spin up ephemeral PostgreSQL and MongoDB containers purely for the duration of the pipeline loop.
2. Install Python 3.11 and the `requirements.txt`.
3. Run `flake8` to natively lint your code for syntax correctness.
4. Execute `python main.py`, capture the `stdout` terminal output logs into a file.
5. Parse the end-to-end simulation results and cleanly present the output right inside your GitHub pull request!
