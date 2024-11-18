import requests
from concurrent.futures import ThreadPoolExecutor
import time

# URL del servidor Flask
URL = "http://127.0.0.1:5000/?filter=batman"

# Función para enviar una solicitud
def send_request():
    try:
        response = requests.get(URL)
        if response.status_code == 200:
            return response.elapsed.total_seconds()
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# Función principal para realizar la prueba de estrés
def stress_test(total_requests, concurrent_requests):
    with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        start_time = time.time()
        results = list(executor.map(lambda _: send_request(), range(total_requests)))
        end_time = time.time()

    successful_requests = [r for r in results if r is not None]

    print(f"Total solicitudes: {total_requests}")
    print(f"Solicitudes exitosas: {len(successful_requests)}")
    print(f"Tiempo promedio de respuesta: {sum(successful_requests) / len(successful_requests):.4f} s")
    print(f"Tiempo total: {end_time - start_time:.4f} s")

# Configura los parámetros de la prueba
TOTAL_REQUESTS = 1000  # Número total de solicitudes
CONCURRENT_REQUESTS = 10  # Número de solicitudes concurrentes

stress_test(TOTAL_REQUESTS, CONCURRENT_REQUESTS)
