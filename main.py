import asyncio
from database import PostgresDB, MongoDB, ElasticsearchDB
from test_runner import AsyncTestRunner

async def main():
    print("Initializing Database Connections...")
    
    # Init PostgreSQL
    pg_db = PostgresDB()
    pg_db.connect()
    pg_db.init_tables()
    
    # Init MongoDB
    mongo_db = MongoDB()
    mongo_db.connect()
    
    # Init Elasticsearch (for full-text log search via Kibana)
    es_db = ElasticsearchDB()
    es_db.connect()
    
    print("All Databases Connected and Tables Initialized!")
    
    # 1. Create 10 fake devices & register in PostgreSQL as AVAILABLE
    devices = [f"device_iphone_{str(i).zfill(3)}" for i in range(1, 11)]
    for device in devices:
        pg_db.register_device(device, "AVAILABLE")
    print("✅ 10 devices registered natively in PostgreSQL")
    
    # 2. Creates 3 test types across all devices building combinations
    test_types = ["performance_test", "connectivity_test", "stability_test"]
    test_requests = []
    
    # Building a pairing of 10 devices * 3 tests = 30 total tests to run concurrently
    for test in test_types:
        for device in devices:
            test_requests.append((test, device))
            
    # 3. Run all tests concurrently using AsyncTestRunner with DB bindings attached
    runner = AsyncTestRunner(pg_db=pg_db, mongo_db=mongo_db, es_db=es_db)
    final_results = await runner.run_all(test_requests)
    
    # 4. Print final mathematical summary
    print("\n--- Final Test Results Summary ---")
    total = len(test_requests)
    passed = 0
    failed = 0
    total_duration = 0.0
    
    for res in final_results:
        # Check if Python threw a root level runtime exception inside gather
        if isinstance(res, Exception):
            print(f"CRITICAL ERROR AVERTED: {res}")
            failed += 1
            continue
            
        if res.get("status") == "PASS":
            passed += 1
        else:
            failed += 1
            
        total_duration += res.get("duration", 0)
        
    avg_duration = total_duration / total if total > 0 else 0
    
    print(f"Total Tests Run: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Average Duration: {avg_duration:.2f} seconds")
    print("----------------------------------\n")

    # Safe Cleanup
    pg_db.close()
    mongo_db.close()
    es_db.close()

if __name__ == "__main__":
    asyncio.run(main())
