import os
from flask import Flask
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from models import db, Usuario, Sistema, UsuarioSistema
from routes import auth_bp

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)

# Configurações do banco de dados usando variáveis de ambiente
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurações do JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'sua_chave_secreta_padrao')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))

# Inicializa extensões
db.init_app(app)
jwt = JWTManager(app)

# Registra os blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')


@app.route('/')
def index():
    return {'msg': 'API de Autenticação ', 'version': '1.0.0'}


@app.route('/health')
def health():
    return {'status': 'ok', 'database': 'connected' if db.engine else 'disconnected'}

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

# Contexto da aplicação para criar tabelas
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_ENV') == 'development', host='0.0.0.0', port=5001)