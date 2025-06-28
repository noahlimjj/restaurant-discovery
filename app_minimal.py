from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World! App is working!'

@app.route('/test')
def test():
    return {'status': 'success', 'message': 'App is working!'}

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port) 