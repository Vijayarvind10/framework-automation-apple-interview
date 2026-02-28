import asyncio
import logging
import time
import datetime
import random
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class BaseTest(ABC):
    """Base abstract class that all tests will inherit from."""
    def __init__(self, device_id: str):
        self.device_id = device_id
        
    @abstractmethod
    async def run(self) -> dict:
        """The main test execution method to be overridden by subclasses."""
        pass

# -- Three Example Test Types for the Interview -- #
class PerformanceTest(BaseTest):
    async def run(self) -> dict:
        logging.info(f"[{self.device_id}] Starting PerformanceTest...")
        await asyncio.sleep(random.uniform(0.5, 1.0)) 
        if random.random() < 0.1: # 10% failure chance
            raise RuntimeError("Performance drop detected in memory profile")
        return {"status": "PASS", "device_id": self.device_id, "test_name": "PerformanceTest"}

class ConnectivityTest(BaseTest):
    async def run(self) -> dict:
        logging.info(f"[{self.device_id}] Starting ConnectivityTest...")
        await asyncio.sleep(random.uniform(0.5, 1.5)) 
        if random.random() < 0.1:
            raise ConnectionError("Wireless AP connection lost randomly")
        return {"status": "PASS", "device_id": self.device_id, "test_name": "ConnectivityTest"}

class StabilityTest(BaseTest):
    async def run(self) -> dict:
        logging.info(f"[{self.device_id}] Starting StabilityTest...")
        await asyncio.sleep(random.uniform(1.0, 2.0)) 
        if random.random() < 0.1:
            raise ValueError("Unexpected springboard crash on iOS device")
        return {"status": "PASS", "device_id": self.device_id, "test_name": "StabilityTest"}


class TestFactory:
    """Factory to create test instances based on the test name."""
    @staticmethod
    def create_test(test_name: str, device_id: str) -> BaseTest:
        tests_registry = {
            "performance_test": PerformanceTest,
            "connectivity_test": ConnectivityTest,
            "stability_test": StabilityTest,
        }
        
        test_class = tests_registry.get(test_name.lower())
        if not test_class:
            raise ValueError(f"Unknown test name requested: {test_name}")
            
        return test_class(device_id)


class AsyncTestRunner:
    """Runs wireless tests on multiple devices concurrently, logging results to PostgreSQL & MongoDB."""
    
    def __init__(self, pg_db=None, mongo_db=None):
        self.pg_db = pg_db
        self.mongo_db = mongo_db

    async def _execute_single_test(self, test_name: str, device_id: str) -> dict:
        """Wrapper to execute a single test, log database results, and handle exceptions safely."""
        start_time = time.time()
        status = "FAIL"
        error_msg = ""
        
        # 1. Update device status to RUNNING in PostgreSQL at the very beginning
        if self.pg_db:
            try:
                self.pg_db.update_device_status(device_id, "RUNNING")
            except Exception as e:
                logging.error(f"PG Update Error: {e}")

        try:
            # 2. Factory creates the correct test type based on the string name
            test_instance = TestFactory.create_test(test_name, device_id)
            
            # 3. Await the specific test's execution method
            result = await test_instance.run()
            status = "PASS"
            print(f"✅ [SUCCESS] Test '{test_name}' on device '{device_id}' completed.")
            
        except Exception as e:
            # 4. Handle exceptions gracefully without tearing down the entire runner loop
            error_msg = str(e)
            print(f"❌ [FAILED] Test '{test_name}' on device '{device_id}' failed: {type(e).__name__}({e})")
            result = {
                "status": "FAIL", 
                "device_id": device_id, 
                "test_name": test_name, 
                "error": error_msg
            }
            
        duration = time.time() - start_time
        result["duration"] = duration

        # 5. DB Cleanup: Write post-test results to PostgreSQL
        if self.pg_db:
            try:
                # Add to 'tests' & 'results' postgres table
                self.pg_db.log_result(test_name, device_id, status, duration, error_msg)
                # Ensure device status is released back to AVAILABLE since device is idle
                self.pg_db.update_device_status(device_id, "AVAILABLE")
            except Exception as e:
                logging.error(f"PostgreSQL logging error: {e}")

        # 6. DB Cleanup: Write raw document logs to MongoDB
        if self.mongo_db:
            try:
                timestamp = datetime.datetime.now()
                self.mongo_db.write_log(test_name, device_id, status, duration, error_msg, timestamp)
            except Exception as e:
                logging.error(f"MongoDB logging error: {e}")

        return result

    async def run_all(self, test_requests: list[tuple[str, str]]) -> list[dict]:
        """Runs all test/device combination tasks concurrently using asyncio.gather()."""
        print(f"🚀 Dispatching {len(test_requests)} tests to physical devices concurrently...")
        
        # Build the coroutine array
        tasks = [
            self._execute_single_test(test_name, device_id) 
            for test_name, device_id in test_requests
        ]
        
        # Gather will execute them independently in the event loop multiplexing IO operations
        results = await asyncio.gather(*tasks, return_exceptions=True)
        print(f"🏁 All {len(test_requests)} test executions have concluded.")
        return list(results)
