import os

SUPPLIER_SERVICE_URL = os.getenv("SUPPLIER_SERVICE_URL", "http://localhost:8084")
LOCATION_SERVICE_URL = os.getenv("LOCATION_SERVICE_URL", "http://localhost:8082")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8083")
STAFF_SERVICE_URL = os.getenv("STAFF_SERVICE_URL", "http://localhost:8085")
EQUIPMENT_SERVICE_URL = os.getenv("EQUIPMENT_SERVICE_URL", "http://localhost:8086")
HEAVY_CARGO_THRESHOLD_KG = float(os.getenv("HEAVY_CARGO_THRESHOLD_KG", "1000"))

