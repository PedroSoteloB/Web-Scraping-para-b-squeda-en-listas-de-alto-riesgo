from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

app = Flask(__name__)

# Control del número máximo de llamadas por minuto
MAX_CALLS_PER_MINUTE = 20
calls_made = 0
last_call_time = 0

# Función para buscar la entidad en la fuente específica mediante web scraping con Selenium
def search_entity_in_source(entity_name):
    global calls_made, last_call_time

    # Verificar el número máximo de llamadas por minuto
    current_time = time.time()
    if current_time - last_call_time < 60:
        calls_made += 1
        if calls_made > MAX_CALLS_PER_MINUTE:
            return -1, [], "Se ha excedido el número máximo de llamadas por minuto."
    else:
        calls_made = 1
        last_call_time = current_time

    # Inicializar el driver del navegador (en este caso, Chrome)
    driver = webdriver.Chrome()

    # Navegar a la página que quieres
    driver.get("https://projects.worldbank.org/en/projects-operations/procurement/debarred-firms")

    # Esperar un poco para asegurarnos de que la página se cargue completamente
    time.sleep(5)

    # Encontrar la tabla de resultados usando el XPath proporcionado
    table = driver.find_element(By.XPATH, '//*[@id="k-debarred-firms"]/div[3]/table')

    # Encontrar todas las filas de la tabla de resultados
    rows = table.find_elements(By.XPATH, "./tbody/tr")

    # Buscar la entidad en las filas de la tabla
    hits = 0
    results = []
    for row in rows:
        # Buscar el nombre de la entidad en la primera columna (FIRM NAME)
        firm_name = row.find_element(By.XPATH, "./td[1]").text.strip()
        if entity_name.lower() in firm_name.lower():
            hits += 1
            # Almacenar los detalles de la entidad
            entity_details = {
                "FIRM NAME": firm_name,
                "ADDRESS": row.find_element(By.XPATH, "./td[3]").text.strip(),
                "COUNTRY": row.find_element(By.XPATH, "./td[4]").text.strip(),
                "From DATE": row.find_element(By.XPATH, "./td[5]").text.strip(),
                "To DATE": row.find_element(By.XPATH, "./td[6]").text.strip(),
                "GROUNDS": row.find_element(By.XPATH, "./td[7]").text.strip()
            }
            results.append(entity_details)

    # Cerrar el driver
    driver.quit()

    return hits, results, ""

# Ruta para realizar la búsqueda de la entidad
@app.route('/search', methods=['GET'])
def search_entity():
    # Recibir el nombre de la entidad de los parámetros de la URL
    entity_name = request.args.get('entity_name')

    # Realizar la búsqueda en la fuente específica mediante web scraping con Selenium
    hits, results, error_message = search_entity_in_source(entity_name)

    if error_message:
        return jsonify({"error": error_message}), 429

    return jsonify({"hits": hits, "results": results})

if __name__ == '__main__':
    app.run(debug=True)
