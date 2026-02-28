from time import time
import datetime
from abc import ABC, abstractmethod

def retry(times=3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < times:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    print(f"Attempt {attempts} failed: {e}")
                    if attempts == times:
                        raise e
        return wrapper
    return decorator
    

def log_time(func):        
    def wrapper(*args, **kwargs):
        start = time()
        result = func(*args, **kwargs) 
        end = time()
        print(f"Ran for {end - start}")      
        return result     
    return wrapper

class BaseTest(ABC):
    def __init__(self, device):
        self.device = device
        self.status = "PENDING"   
        self.start_time = None  
        self.end_time = None  
        
    @retry(times = 3)
    @log_time
    def run(self):
        self.start()
        self.processing()
        return self.exit()
    
    
    def start(self):
        self.status = "STARTING"
        self.start_time = time() 
    
    @abstractmethod
    def processing(self):
         pass
    
    def exit(self):
        self.status = "DONE"
        self.end_time = time()
        return {
            "status": self.status,
            "device": self.device,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.end_time - self.start_time
        }
        


class WiFiSpeedTest(BaseTest):
    def processing(self):
        print(f"WiFi speed test running on {self.device}")

class WiFiLatencyTest(BaseTest):
    def processing(self):
        print(f"WiFi latency test running on {self.device}")

class BluetoothTest(BaseTest):
    def processing(self):
        print(f"Bluetooth test running on {self.device}")

class TestFactory:
    registry = {
        "wifi_speed": WiFiSpeedTest,
        "wifi_latency": WiFiLatencyTest,
        "bluetooth": BluetoothTest,
    }
    
    def __init__(self, test_name):
        self.test_name = test_name
    
    def process(self, device):
        if self.test_name not in self.registry:
            raise ValueError(f"Unknown test: {self.test_name}")
        return self.registry[self.test_name](device)
    

test = TestFactory("wifi_speed")
test = test.process("iPhone 11")
output = test.run()
print(output)