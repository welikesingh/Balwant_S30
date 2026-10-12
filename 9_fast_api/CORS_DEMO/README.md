
### CORS example
What is CORS?
CORS is a browser security mechanism that controls whether a web page from one origin can access resources from another origin.

## For example:
Component	HTML frontend	        FastAPI backend
URL	        http://localhost:5500	http://localhost:8000
Port	    5500	                8000
Origin	    Different	            Different



uvicorn cors_FastAPI:app --reload --port 8000


VS Code, install the Live Server extension, right-click index.html, and select Open with Live Server. The page will typically open at: http://127.0.0.1:5500/index.html



## altenatively: 
python -m http.server 5500

access  http://127.0.0.1:5500/index.html

Click “Call FastAPI”
Initially, the browser should block access to the API response because the backend has not allowed the frontend's origin. Check the browser's Developer Tools → Console for a CORS error.


## Fix the issue by enabling CORS
uvicorn cors_FastAPI_Fixed:app --reload --port 8000
python -m http.server 5500
access  http://127.0.0.1:5500/index.html   in browser



Without CORS configured: The API may receive and process the request, but the browser prevents JavaScript from reading the response.


With CORS configured: The backend sends the appropriate CORS response headers, allowing the browser to expose the response to your frontend JavaScript.
