https://euron.one/code-agent


pip install euron-code
pip install -U euron-code
euron login

euron init

euron --dangerously-skip-permissions
-------------------------------------
uvicorn app.main:app --reload

 http://127.0.0.1:8000/docs 
------------------------------------

docker build -t calculator-api .

docker run -p 5000:8000 calculator-api
docker run --name calc-container -p 5000:8000 calculator-api
docker run -d --name calc-container -p 5000:8000 calculator-api

http://localhost:5000/docs

-------------------------------

Run the Streamlit calculator UI
pip install -r streamlit-app/requirements.txt
streamlit run streamlit-app/app.py --server.port 8501
 

Open your browser at http://127.0.0.1:8501 

----------------------------------

Execrcise prompt:




CALCULATOR API WITH FASTAPI
build a FastAPI app in app/main.py with

• GET /health
• POST /add, /subtract, /multiply, /divide and /power, each taking two numbers in a JSON body and returning the result
• POST /calculate that takes an expression string like "2 + 3 * 4" and returns the result (no eval; ask the agent for a safe parser)
• input validation with Pydantic (divide by zero returns 400 with a clear message, non-numbers are rejected)
• a GET /history endpoint that returns the last 20 calculations kept in memory
• tests with pytest for every endpoint, and requirements.txt
Run it with uvicorn app.main:app --reload, open /docs and call every endpoint. 
Run pytest and show all tests passing.




DOCKER IMAGE
write a Dockerfile (slim Python base image, non-root user, requirements installed before the code is copied so the layer caches) and a .dockerignore. 
Then:

docker build -t calculator-api .

docker run -p 5000:8000 calculator-api
docker run --name calc-container -p 5000:8000 calculator-api
docker run -d --name calc-container -p 5000:8000 calculator-api

http://localhost:5000/docs

 
• note the image size (docker images) and stop container and ask the agent to make it smaller if it is over 200 MB

observer newly created Dockerfile
Optional: a docker-compose.yml that starts the API, and push the image to Docker Hub.





CALCULATOR APP 

build a small calculator user interface that calls your API:http://localhost:5000/docs  a single HTML page with JavaScript served by FastAPI at GET /, or a Streamlit app, your choice. Buttons for digits and operators, a display, a history panel fed by /history, and friendly error messages when the API returns 400. Run it against the container :calc-container 

docker run -d --name calc-container -p 5000:8000 calculator-api

place frontend app code inside streamlit-app folder




