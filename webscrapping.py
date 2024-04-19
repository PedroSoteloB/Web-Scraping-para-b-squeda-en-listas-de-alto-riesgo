from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

app = Flask(__name__)

MAX_CALLS_PER_MINUTE = 20
calls_made = 0
last_call_time = 0

def search_entity_in_source(entity_name):
    global calls_made, last_call_time

    current_time = time.time()
    if current_time - last_call_time < 60:
        calls_made += 1
        if calls_made > MAX_CALLS_PER_MINUTE:
            return -1, [], "Se ha excedido el número máximo de llamadas por minuto."
    else:
        calls_made = 1
        last_call_time = current_time

    driver = webdriver.Chrome()

    driver.get("https://projects.worldbank.org/en/projects-operations/procurement/debarred-firms")

    time.sleep(5)

    table = driver.find_element(By.XPATH, '//*[@id="k-debarred-firms"]/div[3]/table')

    rows = table.find_elements(By.XPATH, "./tbody/tr")

    hits = 0
    results = []
    for row in rows:
        firm_name = row.find_element(By.XPATH, "./td[1]").text.strip()
        if entity_name.lower() in firm_name.lower():
            hits += 1
            entity_details = {
                "FIRM NAME": firm_name,
                "ADDRESS": row.find_element(By.XPATH, "./td[3]").text.strip(),
                "COUNTRY": row.find_element(By.XPATH, "./td[4]").text.strip(),
                "From DATE": row.find_element(By.XPATH, "./td[5]").text.strip(),
                "To DATE": row.find_element(By.XPATH, "./td[6]").text.strip(),
                "GROUNDS": row.find_element(By.XPATH, "./td[7]").text.strip()
            }
            results.append(entity_details)

    driver.quit()

    return hits, results, ""

@app.route('/search', methods=['GET'])
def search_entity():
    entity_name = request.args.get('entity_name')

    hits, results, error_message = search_entity_in_source(entity_name)

    if error_message:
        return jsonify({"error": error_message}), 429

    return jsonify({"hits": hits, "results": results})

if __name__ == '__main__':
    app.run(debug=True)
